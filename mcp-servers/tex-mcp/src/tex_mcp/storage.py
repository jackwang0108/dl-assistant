"""Immutable source snapshots and versioned parse payloads in a new database."""

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from .acquire import sha
from .models import TexError

PARSER_VERSION = "tex-v2.1"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class Storage:
    def __init__(self, directory=None):
        self.root = (
            Path(directory or os.getenv("TEX_MCP_CACHE_DIR", Path.home() / ".cache" / "tex-mcp"))
            .expanduser()
            .resolve()
        )
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "documents").mkdir(exist_ok=True)
        self.db_path = self.root / "documents-v2.sqlite3"
        self.parser_signature = digest(
            {
                "version": PARSER_VERSION,
                "code": {
                    name: sha(Path(__file__).parent / name)
                    for name in ("syntax.py", "document.py", "bibliography.py")
                },
                "libraries": {name: version(name) for name in ("pylatexenc", "pybtex")},
            }
        )
        with self.db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS source_index (arxiv_id TEXT, revision TEXT, main_tex TEXT, parser TEXT, document_id TEXT, PRIMARY KEY(arxiv_id,revision,main_tex,parser))"
            )

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.db_path, timeout=20)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, stage, metadata, parsed, manifest):
        identity = {
            "manifest": manifest,
            "main_tex": parsed["main_tex"],
            "actual_version": metadata.get("actual_version"),
            "parser": self.parser_signature,
        }
        document_id = digest(identity)
        dest = self.root / "documents" / document_id
        if not dest.exists():
            # Same-files concurrent imports are equivalent; rename installs complete snapshots only.
            try:
                stage.rename(dest)
            except OSError:
                if not dest.exists():
                    raise
        record = {
            **metadata,
            **parsed,
            "manifest": manifest,
            "document_id": document_id,
            "parser_version": PARSER_VERSION,
            "parser_signature": self.parser_signature,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.db() as db:
            db.execute(
                "INSERT OR IGNORE INTO documents VALUES(?,?)", (document_id, json.dumps(record))
            )
            if metadata.get("kind") == "arxiv":
                db.execute(
                    "INSERT OR REPLACE INTO source_index VALUES(?,?,?,?,?)",
                    (
                        metadata["arxiv_id"],
                        metadata["actual_version"],
                        parsed["main_tex"],
                        self.parser_signature,
                        document_id,
                    ),
                )
        return self.get(document_id)

    def find_arxiv(self, arxiv_id, revision, main_tex=None):
        with self.db() as db:
            rows = db.execute(
                "SELECT document_id FROM source_index WHERE arxiv_id=? AND revision=? AND parser=? AND (? IS NULL OR main_tex=?)",
                (arxiv_id, revision, self.parser_signature, main_tex, main_tex),
            ).fetchall()
        return self.get(rows[0][0]) if len(rows) == 1 else None

    def get(self, document_id):
        with self.db() as db:
            row = db.execute("SELECT payload FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise TexError("DOCUMENT_NOT_FOUND", "Unknown document_id; reopen source in this cache")
        return json.loads(row[0])

    def source_root(self, document_id):
        self.get(document_id)
        return self.root / "documents" / document_id

    def verify(self, document_id):
        doc = self.get(document_id)
        root = self.source_root(document_id)
        changed = []
        for entry in doc["manifest"]:
            path = root / entry["path"]
            if not path.is_file() or path.is_symlink() or sha(path) != entry["sha256"]:
                changed.append(entry["path"])
        return changed
