#!/usr/bin/env python3
"""Validate paper experiment identities, references and declared simple statistics."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import mean


STATUSES = {"not_started", "in_progress", "completed", "partial", "failed", "blocked", "cancelled"}
VALIDITIES = {"unassessed", "valid", "limited", "invalid"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path, versioned=True):
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    require(isinstance(data, dict), f"{path}: expected JSON object")
    if versioned:
        require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
                f"{path}: unsupported schema_version")
    return data


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)


def indexed(rows, key):
    require(isinstance(rows, list), f"{key}: expected a list")
    result = {}
    for row in rows:
        value = row[key]
        require(isinstance(value, str) and SLUG.fullmatch(value), f"{key}: invalid ID {value}")
        require(value not in result, f"{key}: duplicate ID {value}")
        result[value] = row
    return result


def positive(value):
    return type(value) is int and value > 0


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def local_file(root, path):
    relative = Path(path)
    require(not relative.is_absolute(), f"expected package-relative path: {path}")
    target = (root / relative).resolve()
    require(target.is_relative_to(root.resolve()) and target.is_file(), f"missing or outside package: {path}")
    return target


def snapshot(root, reference):
    target = local_file(root, reference["path"])
    require(digest(target) == reference["sha256"], f"snapshot digest mismatch: {target.name}")
    return target


def dependencies(rows, field):
    remaining = {}
    for eid, row in rows.items():
        items = row[field]
        require(isinstance(items, list) and len(set(items)) == len(items), f"{eid}: invalid {field}")
        require(set(items) <= rows.keys(), f"{eid}: unknown dependency")
        remaining[eid] = set(items)
    while remaining:
        ready = {eid for eid, items in remaining.items() if not items}
        require(ready, f"cyclic {field}")
        remaining = {eid: items - ready for eid, items in remaining.items() if eid not in ready}


def check_plan(plan):
    require(isinstance(plan["batch_id"], str) and SLUG.fullmatch(plan["batch_id"]), "invalid batch_id")
    require(positive(plan["plan_version"]), "invalid plan_version")
    rows = indexed(plan["experiments"], "exp_id")
    require(rows, "plan has no experiments")
    approval = plan["approval"]
    require(approval["ref"], "missing plan approval reference")
    approved = approval["experiment_ids"]
    require(isinstance(approved, list) and len(approved) == len(set(approved)), "invalid approved experiment IDs")
    require(set(approved) <= rows.keys(), "approval references unknown experiment")
    for eid, row in rows.items():
        for key in ("title", "operation", "purpose"):
            require(row[key], f"{eid}: {key} is empty")
        for key in ("comparison", "replicates", "interpretation", "resources"):
            require(isinstance(row[key], dict) and row[key], f"{eid}: missing {key}")
        require(row["priority"] in {"required", "optional"}, f"{eid}: invalid priority")
        require(isinstance(row["paper_locations"], list), f"{eid}: invalid paper_locations")
        indexed(row["measurements"], "id")
        replicates = row["replicates"]
        require(replicates["unit"], f"{eid}: missing replicate unit")
        for item in indexed(replicates["items"], "id").values():
            require(item["seed"] is None or type(item["seed"]) is int, f"{eid}: invalid seed")
    dependencies(rows, "depends_on")
    return rows, set(approved)


def check_spec(plan_path, plan, spec, rows, approved):
    require(spec["batch_id"] == plan["batch_id"], "plan and run-spec batch IDs differ")
    require(positive(spec["revision"]), "invalid run-spec revision")
    require(spec["plan"]["path"] == plan_path.name and spec["plan"]["sha256"] == digest(plan_path),
            "run-spec plan reference does not identify this approved plan")
    require(spec["approval_ref"], "missing actual execution authorization")
    bound = indexed(spec["experiments"], "exp_id")
    require(bound.keys() == approved and bound, "run-spec must bind exactly the approved experiments")
    for eid, row in bound.items():
        for key in ("working_directory", "git_commit", "command", "device", "config_ref", "resource_limit"):
            require(row[key], f"{eid}: run-spec missing {key}")
        require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", row["git_commit"]), f"{eid}: use full Git commit")
        for key in ("data_refs", "model_refs", "expected_artifacts"):
            require(isinstance(row[key], list), f"{eid}: run-spec {key} must be a list")
        require(set(rows[eid]["depends_on"]) <= set(row["schedule_after"]), f"{eid}: lost plan dependency")
    dependencies(bound, "schedule_after")


def check_artifact(root, artifact):
    require(isinstance(artifact, dict) and ("path" in artifact) != ("external" in artifact),
            "artifact needs either a local path or an external reference")
    if "path" in artifact:
        path = local_file(root, artifact["path"])
        if artifact.get("sha256") is not None:
            require(digest(path) == artifact["sha256"], f"artifact digest mismatch: {artifact['path']}")
    else:
        external = artifact["external"]
        require(all(external.get(key) for key in ("location", "version", "availability")),
                "external evidence needs location, version and availability")


def check_statistic(stat, attempts, root, measurements):
    name = stat["id"]
    metric = stat["measurement_id"]
    require(metric in measurements, f"{name}: unknown measurement")
    unit = stat["unit"]
    require(unit == measurements[metric]["unit"], f"{name}: unit differs from plan")
    require(finite(stat["value"]), f"{name}: invalid numeric value")
    selected = stat["attempt_ids"]
    require(isinstance(selected, list) and selected and len(set(selected)) == len(selected)
            and set(selected) <= attempts.keys(), f"{name}: invalid attempt references")
    chosen = [attempts[item] for item in selected]
    require(len({a["replicate_id"] for a in chosen}) == len(chosen), f"{name}: repeated independent replicate")
    require(all(a["status"] == "completed" and a["data_validity"] in {"valid", "limited"} for a in chosen),
            f"{name}: aggregates unavailable attempts")
    method = stat["method"]
    if method == "analysis":
        check_artifact(root, stat["analysis_ref"])
        return
    require(method in {"mean", "mean_paired_difference"}, f"{name}: unknown statistic method")
    values = []
    for attempt in chosen:
        data = load(local_file(root, attempt["metrics_ref"]), versioned=False)
        require(data["attempt_id"] == attempt["attempt_id"], f"{name}: metrics belongs to a different attempt")
        require(data["measurements"][metric]["unit"] == unit, f"{name}: wrong raw unit")
        raw = data["measurements"][metric]["values"]
        groups = [stat["group"]] if method == "mean" else [stat["minuend"], stat["subtrahend"]]
        require(len(set(groups)) == len(groups), f"{name}: invalid paired groups")
        operands = [raw[group] for group in groups]
        require(all(finite(value) for value in operands), f"{name}: invalid raw readout")
        values.append(operands[0] if len(operands) == 1 else operands[0] - operands[1])
    require(math.isclose(mean(values), stat["value"], abs_tol=1e-9, rel_tol=1e-9),
            f"{name}: value does not match declared raw readouts")


def check_results(root, result, plan, spec, plan_rows, approved):
    require(result["batch_id"] == plan["batch_id"], "results and plan batch IDs differ")
    require(positive(result["revision"]), "invalid result revision")
    previous = result["previous_sha256"]
    require((result["revision"] == 1 and previous is None)
            or (result["revision"] > 1 and sha256(previous)), "invalid previous result digest")
    require(isinstance(result["changes"], list), "changes must be a list")
    rows = indexed(result["experiments"], "exp_id")
    require(rows.keys() == plan_rows.keys(), "results must cover all plan experiments")
    for eid, row in rows.items():
        experiment = plan_rows[eid]
        execution = row["execution"]
        status = execution["status"]
        require(status in STATUSES, f"{eid}: invalid execution status")
        require(status == "completed" or execution["reason"], f"{eid}: missing status reason")
        attempts = indexed(execution["attempts"], "attempt_id")
        require(eid in approved or (status == "not_started" and not attempts), f"{eid}: unapproved execution")
        require(status != "not_started" or not attempts, f"{eid}: not_started with attempts")
        require(isinstance(execution["resource_usage"], list), f"{eid}: invalid resource_usage")
        require(status != "completed" or any(a["status"] == "completed" for a in attempts.values()),
                f"{eid}: completed without a completed attempt")
        measurement = row["measurement"]
        require(measurement["validity"] in VALIDITIES and isinstance(measurement["conditions"], list)
                and isinstance(measurement["limitations"], list), f"{eid}: invalid measurement record")
        require(row["evidence"]["summary"], f"{eid}: missing evidence judgment")
        require(isinstance(row["deviations"], list), f"{eid}: invalid deviations")
        replicates = indexed(experiment["replicates"]["items"], "id")
        measurements = indexed(experiment["measurements"], "id")
        parents = {}
        for aid, attempt in attempts.items():
            require(attempt["status"] in STATUSES and attempt["data_validity"] in VALIDITIES,
                    f"{eid}/{aid}: invalid attempt status or data validity")
            replicate = attempt["replicate_id"]
            require(replicate in replicates and attempt["seed"] == replicates[replicate]["seed"],
                    f"{eid}/{aid}: invalid replicate or seed")
            revision = attempt["run_spec_revision"]
            require(positive(revision) and revision <= spec["revision"], f"{eid}/{aid}: invalid run-spec revision")
            actual = load(local_file(root, attempt["meta_ref"]), versioned=False)
            for field in ("attempt_id", "replicate_id", "seed", "run_spec_revision", "status"):
                require(actual[field] == attempt[field], f"{eid}/{aid}: mismatched meta {field}")
            require(actual["exp_id"] == eid and actual["batch_id"] == result["batch_id"],
                    f"{eid}/{aid}: meta belongs to a different experiment")
            require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", actual["git_commit"]) and actual["command"],
                    f"{eid}/{aid}: missing actual execution identity")
            used_spec = load(snapshot(root, actual["run_spec_ref"]))
            require(used_spec["revision"] == revision and used_spec["batch_id"] == result["batch_id"]
                    and used_spec["plan"] == spec["plan"], f"{eid}/{aid}: incorrect actual run-spec")
            bound = indexed(used_spec["experiments"], "exp_id")
            require(eid in bound, f"{eid}/{aid}: actual run-spec lacks the experiment")
            if revision == spec["revision"]:
                require(actual["run_spec_ref"]["sha256"] == result["run_spec"]["sha256"],
                        f"{eid}/{aid}: same revision identifies different specs")
            if attempt.get("metrics_ref") is not None:
                local_file(root, attempt["metrics_ref"])
            refs = [attempt[key] for key in ("retry_of", "resume_from") if attempt.get(key)]
            require(len(refs) <= 1, f"{eid}/{aid}: choose retry or recovery")
            for prior in refs:
                require(prior in attempts and attempts[prior]["replicate_id"] == replicate,
                        f"{eid}/{aid}: retry or recovery must retain replicate")
            parents[aid] = {"previous": refs}
        dependencies(parents, "previous")
        for stat in indexed(row["statistics"], "id").values():
            require(row["measurement"]["validity"] in {"valid", "limited"}, f"{eid}: aggregate lacks valid measurements")
            check_statistic(stat, attempts, root, measurements)
        for artifact in row["artifacts"]:
            check_artifact(root, artifact)


def check_package(root):
    result_path = root / "paper-results.json"
    result = load(result_path)
    plan_path = snapshot(root, result["plan"])
    plan = load(plan_path)
    spec = load(snapshot(root, result["run_spec"]))
    rows, approved = check_plan(plan)
    check_spec(plan_path, plan, spec, rows, approved)
    check_results(root, result, plan, spec, rows, approved)
    return result_path, result, spec


def check_revision(current, previous):
    before_path, before, old_spec = check_package(previous)
    after_path, after, new_spec = current
    require(before["batch_id"] == after["batch_id"] and before["plan"]["sha256"] == after["plan"]["sha256"],
            "previous package belongs to a different approved batch")
    require(after["revision"] == before["revision"] + 1 and after["previous_sha256"] == digest(before_path),
            "result does not extend the supplied previous revision")
    require(new_spec["revision"] >= old_spec["revision"], "run-spec revision went backwards")
    if new_spec["revision"] == old_spec["revision"]:
        require(before["run_spec"]["sha256"] == after["run_spec"]["sha256"], "run-spec changed without a revision")
    new_rows = indexed(after["experiments"], "exp_id")
    for old_row in before["experiments"]:
        eid = old_row["exp_id"]
        new_row = new_rows[eid]
        attempts = indexed(new_row["execution"]["attempts"], "attempt_id")
        for old_attempt in old_row["execution"]["attempts"]:
            aid = old_attempt["attempt_id"]
            require(aid in attempts and all(attempts[aid][key] == old_attempt[key]
                       for key in ("replicate_id", "seed", "run_spec_revision")), f"{eid}/{aid}: lost attempt identity")
            old_meta = load(local_file(previous, old_attempt["meta_ref"]), versioned=False)
            new_meta = load(local_file(after_path.parent, attempts[aid]["meta_ref"]), versioned=False)
            for key in ("git_commit", "command"):
                require(old_meta[key] == new_meta[key], f"{eid}/{aid}: actual execution identity changed")
            require(old_meta["run_spec_ref"]["sha256"] == new_meta["run_spec_ref"]["sha256"],
                    f"{eid}/{aid}: actual run-spec changed")
        new_stats = indexed(new_row["statistics"], "id")
        for old_stat in old_row["statistics"]:
            sid = old_stat["id"]
            if new_stats.get(sid) != old_stat:
                require(any(change.get("exp_id") == eid and change.get("statistic_id") == sid
                            and change.get("previous_value") == old_stat["value"]
                            and change.get("reason") and change.get("impact") for change in after["changes"]),
                        f"{eid}/{sid}: changed or removed statistic lacks an explicit correction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", type=Path)
    mode.add_argument("--pkgdir", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    if args.plan and (not args.spec or args.previous) or args.pkgdir and args.spec:
        parser.error("use --plan with --spec, or --pkgdir with optional --previous")
    try:
        if args.plan:
            plan = load(args.plan)
            rows, approved = check_plan(plan)
            check_spec(args.plan, plan, load(args.spec), rows, approved)
        else:
            current = check_package(args.pkgdir)
            if args.previous:
                check_revision(current, args.previous)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(1, f"[FAIL] {exc}\n")
    print("[PASS] Declared records checked. Review scientific interpretation and external evidence separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
