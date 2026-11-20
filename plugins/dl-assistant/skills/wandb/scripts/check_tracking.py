#!/usr/bin/env python3
"""Read-only checks of declared W&B identity and saved evidence, never remote truth."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


class RecordError(ValueError):
    """Only fixed, non-sensitive diagnostic labels may be returned to callers."""


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")))


def origin(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("invalid instance origin")
    u = urlsplit(value)
    if (u.scheme not in {"http", "https"} or not u.hostname or u.username is not None
            or u.password is not None or u.path not in {"", "/"} or u.query or u.fragment):
        raise ValueError("instance must be an HTTP(S) origin without credentials")
    u.port  # Validate the port before any caller uses this address.
    if u.hostname.lower() in {"wandb.ai", "api.wandb.ai"}:
        raise ValueError("self-managed instance required; cloud fallback is not allowed")
    return value.rstrip("/")


def check(meta, root, portable=False, unchecked=None):
    """Return bounded error labels without printing config/credentials or changing files."""
    errors = []
    unchecked = unchecked if unchecked is not None else []

    def require(ok, label):
        if not ok:
            raise RecordError(label)

    def text(value, label):
        require(isinstance(value, str) and bool(value.strip()), label)

    def referenced_file(ref):
        require(isinstance(ref, dict), "file reference must be an object")
        path, digest = ref.get("path"), ref.get("sha256")
        text(path, "snapshot path missing")
        require(not Path(path).is_absolute(), "snapshot path must be relative")
        target = (root / path).resolve()
        require(target.is_relative_to(root.resolve()), "snapshot escapes experiment directory")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid snapshot hash")
        require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, "snapshot content changed")
        return target

    def hashed_file(ref):
        return load(referenced_file(ref))

    try:
        require(isinstance(meta, dict), "meta must be an object")
        if "tracking" not in meta or meta["tracking"] is None:
            return []  # Explicitly opt-in; do not rewrite historical records.
        t = meta["tracking"]
        require(isinstance(t, dict) and t.get("provider") == "wandb", "invalid tracking provider")
        base = origin(t.get("base_url"))
        for field in ("entity", "project", "scope_id"):
            text(t.get(field), "tracking identity missing: " + field)
        require(isinstance(t.get("hypothesis_ids"), list)
                and all(isinstance(x, str) and x.strip() for x in t["hypothesis_ids"]), "hypothesis_ids must be strings")
        require(t.get("research_round") is None or isinstance(t["research_round"], str), "invalid research_round")
        # Credentials have no legitimate role in these saved tracking/config objects.
        def private_keys(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    require(key.lower() not in {"api_key", "wandb_api_key", "password", "authorization", "token"},
                            "credential field in saved tracking record")
                    private_keys(item)
            elif isinstance(value, list):
                for item in value:
                    private_keys(item)
        private_keys(t)
        attempts = meta.get("attempts")
        require(isinstance(attempts, list), "attempts must be an array")
        seen_runs, seen_attempts = set(), set()
        prior_replicates = {}
        for number, a in enumerate(attempts, 1):
            try:
                require(isinstance(a, dict), "attempt must be an object")
                aid = a.get("attempt_id")
                text(aid, "attempt_id missing")
                require(aid not in seen_attempts, "duplicate attempt_id")
                previous = set(seen_attempts)
                seen_attempts.add(aid)
                resume = a.get("resume_from")
                require(resume is None or isinstance(resume, str) and resume in previous,
                        "resume_from must reference an earlier attempt")
                require(resume is None or prior_replicates.get(resume) == a.get("replicate_id"),
                        "resume source belongs to another replicate")
                prior_replicates[aid] = a.get("replicate_id")
                w = a.get("wandb")
                require(isinstance(w, dict), "attempt has no W&B record")
                private_keys(w)
                rid = w.get("run_id")
                require(isinstance(rid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", rid), "invalid run_id")
                require(rid not in seen_runs, "multiple attempts share one run_id")
                seen_runs.add(rid)
                identity = w.get("identity")
                require(isinstance(identity, dict), "run identity missing")
                for key, value in (("experiment_id", meta.get("experiment_id")), ("attempt_id", aid),
                                   ("replicate_id", a.get("replicate_id")), ("resume_from_attempt", resume)):
                    require(identity.get(key) == value, "local identity mismatch: " + key)
                text(identity.get("experiment_id"), "experiment_id missing")
                text(identity.get("replicate_id"), "replicate_id missing")
                text(identity.get("git_commit"), "actual git_commit missing")
                commit = a.get("git_commit", meta.get("git_commit"))
                text(commit, "local code commit missing")
                require(identity["git_commit"] == commit, "attempt code commit mismatch")
                source_changed = any(key in a and meta.get(key) is not None and a[key] != meta[key]
                                     for key in ("git_commit", "code_dirty", "code_diff_path", "configuration_ref"))
                if source_changed:
                    deviations = meta.get("deviations", [])
                    require(isinstance(deviations, list), "invalid deviations")
                    require(any(isinstance(d, dict) and d.get("id") == a.get("deviation_ref")
                                and isinstance(d.get("approval"), dict)
                                and d["approval"].get("status") == "approved"
                                and d["approval"].get("basis") for d in deviations),
                            "changed attempt code needs recorded approval")
                for key in ("design_sha256", "config_sha256"):
                    require(isinstance(identity.get(key), str) and re.fullmatch(r"[0-9a-f]{64}", identity[key]),
                            "invalid identity hash: " + key)
                diff = identity.get("code_diff_sha256")
                require(diff is None or isinstance(diff, str) and re.fullmatch(r"[0-9a-f]{64}", diff),
                        "invalid diff hash")
                dirty = a.get("code_dirty", meta.get("code_dirty"))
                require(type(dirty) is bool, "actual code_dirty missing")
                if dirty:
                    diff_path = a.get("code_diff_path", meta.get("code_diff_path"))
                    referenced_file({"path": diff_path, "sha256": diff})
                else:
                    require(diff is None, "clean code has a diff hash")
                config_ref = a.get("configuration_ref", meta.get("configuration_ref"))
                hashed_file(config_ref)
                require(config_ref["sha256"] == identity["config_sha256"], "actual config hash mismatch")
                for key in ("data_refs", "model_refs"):
                    require(isinstance(identity.get(key), list), key + " must be an array")
                text(identity.get("protocol_ref"), "protocol_ref missing")
                design = meta.get("design_record", {})
                require(isinstance(design, dict), "invalid design_record")
                design_path = design.get("path")
                text(design_path, "design path missing")
                target = (root / design_path).resolve()
                require(not Path(design_path).is_absolute() and target.is_relative_to(root.resolve()),
                        "design escapes experiment directory")
                require(hashlib.sha256(target.read_bytes()).hexdigest() == identity["design_sha256"],
                        "run design hash differs from saved design")
                state = w.get("sync_status")
                require(state in {"pending", "offline", "failed", "unknown", "not_created", "synced"},
                        "invalid sync_status")
                if state != "synced":
                    text(w.get("local_dir"), "unsynced attempt needs local_dir")
                    recovery_present = (root / w["local_dir"]).is_dir()
                    if portable and not recovery_present:
                        unchecked.append("未同步运行的恢复目录在接收端不可得；保留原local_dir/recovery_ref，不认证恢复或远端同步")
                    else:
                        require(recovery_present, "local recovery directory missing")
                    recovery = w.get("recovery_ref")
                    if recovery is not None:
                        require(isinstance(recovery, dict), "invalid recovery_ref")
                        text(recovery.get("path"), "original recovery path missing")
                        text(recovery.get("reason"), "recovery availability reason missing")
                        require(recovery.get("availability") in {"accessible", "unavailable", "not_checked"},
                                "invalid recovery availability")
                    if state != "pending":
                        text(w.get("reason"), "unsynced attempt needs reason")
                else:
                    snapshot = hashed_file(w.get("snapshot_ref"))
                    require(isinstance(snapshot, dict) and snapshot.get("schema_version") == 1,
                            "invalid readback snapshot")
                    require(origin(snapshot.get("base_url")) == base, "readback instance mismatch")
                    for key, value in (("entity", t["entity"]), ("project", t["project"]), ("run_id", rid)):
                        require(snapshot.get(key) == value, "readback identity mismatch: " + key)
                    text(snapshot.get("queried_at"), "readback query time missing")
                    require(isinstance(snapshot.get("query"), dict) and bool(snapshot["query"]), "query scope missing")
                    require(isinstance(snapshot.get("coverage"), dict) and bool(snapshot["coverage"]), "coverage missing")
                    config = snapshot.get("config")
                    require(isinstance(config, dict), "readback config missing")
                    expected = dict(identity, **{k: t.get(k) for k in ("scope_id", "research_round", "hypothesis_ids")})
                    require(config.get("dl_assistant") == expected, "readback config differs from local identity")
                    require(isinstance(snapshot.get("summary"), dict), "readback summary missing")
            except RecordError as exc:
                errors.append(f"W&B attempt[{number}]: {exc}")
            except (OSError, ValueError, TypeError):
                # Keep all attempts visible without exposing any potentially sensitive values.
                errors.append("W&B attempt identity/evidence check failed")
    except RecordError as exc:
        errors.append("W&B tracking: " + str(exc))
    except (OSError, ValueError, TypeError):
        errors.append("W&B tracking configuration check failed")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = load(args.meta)
        errors = check(data, args.meta.parent)
    except (OSError, ValueError, TypeError):
        errors = ["Unable to read tracking record"]
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        if not data.get("tracking"):
            print("SKIP: no W&B tracking declared; this does not verify W&B integration")
        else:
            print("PASS: local declarations checked; remote persistence and scientific validity unverified")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
