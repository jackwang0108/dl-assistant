"""Instance-bound credentials, atomic replacement and private file permissions."""

import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .models import OverleafError


@dataclass(repr=False)
class Credential:
    cookie: str
    csrf_token: str
    origin: str


class CredentialStore:
    def __init__(self, path, expected_origin):
        self.path = Path(path)
        self.origin = expected_origin

    def read(self, path=None):
        path = Path(path or self.path)
        if not path.is_file():
            raise OverleafError(
                "AUTH_MISSING", "Configure a local session using python -m overleaf_mcp.auth_setup"
            )
        if path.is_symlink() or (os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077):
            raise OverleafError(
                "AUTH_FILE_PERMISSIONS", "Credential file must be a regular private file (0600)"
            )
        try:
            data = json.loads(path.read_text())
            if not isinstance(data, dict):
                raise ValueError()
            if data.get("origin") != self.origin:
                raise OverleafError(
                    "AUTH_INSTANCE_MISMATCH", "Credential file belongs to another Overleaf instance"
                )
            cookie, csrf = data["cookie"], data["csrf_token"]
            if (
                not all(
                    isinstance(v, str) and v.strip() and "\r" not in v and "\n" not in v
                    for v in (cookie, csrf)
                )
                or "<" in csrf
            ):
                raise ValueError()
            return Credential(cookie, csrf, self.origin)
        except (ValueError, KeyError, TypeError):
            raise OverleafError(
                "AUTH_FILE_INVALID", "Credential file is invalid; secret values are not returned"
            ) from None

    def save(self, cred):
        if cred.origin != self.origin:
            raise OverleafError(
                "AUTH_INSTANCE_MISMATCH", "Cannot store credentials for another instance"
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", dir=self.path.parent, delete=False) as stream:
            temp = Path(stream.name)
            os.chmod(temp, 0o600)
            json.dump(
                {"origin": cred.origin, "cookie": cred.cookie, "csrf_token": cred.csrf_token},
                stream,
            )
        os.replace(temp, self.path)
        os.chmod(self.path, 0o600)
