#!/usr/bin/env python3
"""Check declared artifacts and ledger consistency, not scientific validity.

Schema v2 only. Old records require explicit review, never silent conversion.
Failed/blocked runs may pass structural checks without final success metrics.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

STATUSES = {"not_started", "in_progress", "completed", "failed", "blocked", "cancelled"}
TYPES = {"training", "evaluation", "diagnostic", "ablation", "analysis", "probe", "theory"}
VALIDITIES = {"unassessed", "valid", "limited", "invalid"}
INFERENCES = {"pending", "supported", "contradicted", "insufficient_evidence", "not_applicable"}

TRACKING_PATH = Path(__file__).resolve().parents[2] / "wandb/scripts/check_tracking.py"


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, status, message):
        self.rows.append((name, status, message))

    def load(self, path, name, object_required=True):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate key: {key}")
                result[key] = value
            return result
        try:
            result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            if object_required and not isinstance(result, dict):
                raise ValueError("expected object")
            return result
        except (OSError, ValueError, UnicodeError) as exc:
            self.add(name, "FAIL", f"{path}: {exc}")
            return None

    def file(self, directory, value, fmt, name, allow_pending=False, object_required=False):
        if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
            self.add(name, "FAIL", "需提供实验目录内相对文件路径")
            return
        try:
            path = (directory / value).resolve()
            if not path.is_relative_to(directory.resolve()):
                self.add(name, "FAIL", "文件不在实验目录内")
                return
            if allow_pending and not path.exists():
                return
            if not path.is_file() or path.stat().st_size == 0:
                self.add(name, "FAIL", f"文件缺失或为空：{value}")
                return
        except (OSError, RuntimeError, ValueError):
            self.add(name, "FAIL", f"无法访问文件：{value}")
            return
        if fmt == "json":
            before = len(self.rows)
            result = self.load(path, name, object_required=object_required)
            if len(self.rows) == before:
                self.add(name, "PASS", f"JSON可解析：{value}")
            return result
        elif isinstance(fmt, str) and fmt in {"text", "file"}:
            self.add(name, "PASS", f"文件存在且非空：{value}")
            return path
        else:
            self.add(name, "FAIL", f"未知format：{fmt}")

    def ledger(self, path):
        data = self.load(path, "台账")
        if data is None:
            return {}
        rows = data.get("experiments")
        if data.get("schema_version") != 2 or not isinstance(rows, list):
            self.add("台账", "FAIL", "需schema_version=2及experiments数组；旧记录须人工核对")
            return {}
        result = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("experiment_id"), str):
                self.add("台账", "FAIL", "实验行缺少字符串experiment_id")
                continue
            eid = row["experiment_id"]
            if not eid.startswith("exp-") or Path(eid).name != eid or "/" in eid or "\\" in eid:
                self.add("台账", "FAIL", f"非法实验ID：{eid}")
                continue
            if eid in result:
                self.add("台账", "FAIL", f"重复ID：{eid}")
            result[eid] = row
            for field, allowed in (("status", STATUSES), ("data_validity", VALIDITIES),
                                   ("inference_status", INFERENCES)):
                value = row.get(field)
                if not isinstance(value, str) or value not in allowed:
                    self.add(eid, "FAIL", f"台账{field}无效")
            if "meta_path" not in row or row["meta_path"] not in (None, f"{eid}/meta.json"):
                self.add(eid, "FAIL", "台账meta_path须指向对应目录的meta.json，或在未建记录时填null")
        return result

    def experiment(self, directory, row, check_artifacts=True, portable=False):
        eid = directory.name
        if not directory.resolve().is_relative_to(directory.parent.resolve()):
            self.add(eid, "FAIL", "实验目录越出台账目录")
            return
        data = self.file(directory, "meta.json", "json", eid + " meta", object_required=True)
        if data is None:
            return
        if data.get("schema_version") != 2:
            self.add(eid, "FAIL", "旧meta未核对，不自动转成新版预登记")
            return
        if data.get("tracking") is not None:
            if not TRACKING_PATH.is_file():
                self.add(eid + " W&B", "FAIL", "声明了tracking，但缺少相邻wandb/scripts/check_tracking.py；安装wandb配套skill后重查")
            else:
                spec = importlib.util.spec_from_file_location("dl_wandb_tracking", TRACKING_PATH)
                tracking = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tracking)
                unchecked = []
                for error in tracking.check(data, directory, portable=portable, unchecked=unchecked):
                    self.add(eid + " W&B", "FAIL", error)
                for limitation in unchecked:
                    self.add(eid + " W&B", "UNCHECKED", limitation)
        if data.get("experiment_id") != eid:
            self.add(eid, "FAIL", "目录名与meta experiment_id不一致")
        for field, allowed in (("type", TYPES), ("status", STATUSES),
                               ("design_mode", {"exploration", "confirmation"}),
                               ("data_validity", VALIDITIES), ("inference_status", INFERENCES)):
            if not isinstance(data.get(field), str) or data[field] not in allowed:
                self.add(eid, "FAIL", f"{field}缺失或不在枚举内")
        status = data.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            return
        for field in ("purpose",):
            if not isinstance(data.get(field), str) or not data[field].strip():
                self.add(eid, "FAIL", f"{field}需明确")
        if status in {"failed", "blocked", "cancelled"} and not data.get("status_reason"):
            self.add(eid, "FAIL", "失败/阻塞/取消需记录原因")
        if status != "completed":
            self.add(eid, "WARN", f"执行状态={status}，不表示完整实验成功")
        if data.get("data_validity") != "valid":
            self.add(eid, "WARN", f"data_validity={data.get('data_validity')}，需人工解释")
        if data.get("inference_status") in ("supported", "contradicted") and data.get("data_validity") not in ("valid", "limited"):
            self.add(eid, "FAIL", "未经有效性核查的数据不能填supported/contradicted")
        if row is None:
            self.add(eid, "FAIL", "台账缺少本实验")
        else:
            if row.get("meta_path") != f"{eid}/meta.json":
                self.add(eid, "FAIL", "台账有实验目录时须引用实际meta.json")
            for field in ("plan_task_id", "status", "data_validity", "inference_status"):
                if row.get(field) != data.get(field):
                    self.add(eid, "FAIL", f"台账与meta的{field}不一致")
        design = data.get("design_record")
        executed = status in {"in_progress", "completed", "failed"} or bool(data.get("attempts"))
        if design is not None or executed:
            if not isinstance(design, dict) or not design.get("path"):
                self.add(eid, "FAIL", "缺实际设计记录引用")
            else:
                record = self.file(directory, design["path"], "json", eid + " design", object_required=True)
                if record == {}:
                    self.add(eid, "FAIL", "设计记录须为非空JSON对象")
        if executed and not data.get("attempts"):
            self.add(eid, "FAIL", "已执行任务缺attempt记录")
        self.attempts(data, directory, eid, check_artifacts)
        artifacts = data.get("required_artifacts")
        if not isinstance(artifacts, list):
            self.add(eid, "FAIL", "required_artifacts必须是数组")
            return
        required = 0
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                self.add(eid, "FAIL", "产物声明需为对象")
                continue
            states = artifact.get("required_for")
            if not isinstance(states, list) or not states or any(not isinstance(s, str) or s not in STATUSES for s in states):
                self.add(eid, "FAIL", "产物required_for需非空有效状态数组")
                continue
            if status in states:
                required += 1
                if check_artifacts:
                    self.file(directory, artifact.get("path"), artifact.get("format"), eid + " artifact")
        if status == "completed" and required == 0:
            self.add(eid, "FAIL", "completed至少需声明一项实际产物")
        if check_artifacts and status in {"completed", "failed", "blocked", "cancelled"}:
            self.file(directory, "报告.md", "text", eid + " 报告")

    def attempts(self, data, directory, eid, check_artifacts):
        attempts = data.get("attempts")
        if not isinstance(attempts, list):
            self.add(eid, "FAIL", "attempts必须是数组")
            return
        seen = {}
        completed = False
        for attempt in attempts:
            if not isinstance(attempt, dict):
                self.add(eid, "FAIL", "attempt必须是对象")
                continue
            aid, rid = attempt.get("attempt_id"), attempt.get("replicate_id")
            if not isinstance(aid, str) or not aid.strip() or aid in seen:
                self.add(eid, "FAIL", "attempt_id缺失或重复")
                continue
            if not isinstance(rid, str) or not rid.strip():
                self.add(eid, "FAIL", "attempt缺replicate_id")
            state = attempt.get("status")
            if not isinstance(state, str) or state not in STATUSES:
                self.add(eid, "FAIL", "attempt status无效")
                state = None
            manual_ref = attempt.get("manual_record_ref")
            manual = data.get("execution_basis") == "manual" or manual_ref is not None
            command = attempt.get("command") or attempt.get("script")
            if not manual and (not isinstance(command, str) or not command.strip()):
                self.add(eid, "FAIL", "attempt缺实际命令或操作")
            if not manual and state in {"in_progress", "completed", "failed"}:
                commit = attempt.get("git_commit", data.get("git_commit"))
                dirty = attempt.get("code_dirty", data.get("code_dirty"))
                if not isinstance(commit, str) or not commit.strip():
                    self.add(eid, "FAIL", "已执行代码attempt缺代码commit")
                if type(dirty) is not bool:
                    self.add(eid, "FAIL", "已执行代码attempt需明确code_dirty")
                elif dirty:
                    self.file(directory, attempt.get("code_diff_path", data.get("code_diff_path")),
                              "text", f"{eid}/{aid} code diff")
            code = attempt.get("exit_code")
            if code is not None and type(code) is not int:
                self.add(eid, "FAIL", "attempt exit_code须为整数或null")
            if state in {"not_started", "in_progress"} and code is not None:
                self.add(eid, "FAIL", "未结束attempt不能填写终态退出码")
            if state == "completed":
                completed = True
                if manual:
                    if code is not None:
                        self.add(eid, "FAIL", "人工核查不能补造进程退出码")
                    if check_artifacts:
                        self.file(directory, manual_ref.get("path") if isinstance(manual_ref, dict) else manual_ref,
                                  "text", eid + " manual record")
                elif type(code) is not int or code != 0:
                    self.add(eid, "FAIL", "completed代码attempt须有实际退出码0")
            for field in ("retry_of", "resume_from"):
                source = attempt.get(field)
                if source is not None and (not isinstance(source, str) or source not in seen
                                           or seen[source] != rid):
                    self.add(eid, "FAIL", f"{field}须指同一重复的更早attempt")
            if check_artifacts:
                pending = state in {"not_started", "in_progress", "blocked", "cancelled"} and code is None
                config = attempt.get("configuration_ref", data.get("configuration_ref"))
                if config is not None:
                    self.file(directory, config.get("path") if isinstance(config, dict) else None,
                              "file", f"{eid}/{aid} config")
                for field, fmt in (("meta_path", "json"), ("log_path", "text"), ("exit_code_path", "text")):
                    if attempt.get(field) is not None:
                        name = f"{eid}/{aid} {field}"
                        result = self.file(directory, attempt[field], fmt, name,
                                           allow_pending=pending and field != "meta_path",
                                           object_required=field == "meta_path")
                        if field == "meta_path" and isinstance(result, dict):
                            if "attempt_id" in result and result["attempt_id"] != aid:
                                self.add(name, "FAIL", "运行记录的attempt_id不一致")
                        if field == "exit_code_path" and isinstance(result, Path):
                            try:
                                recorded = int(result.read_text(encoding="utf-8").strip())
                            except (OSError, ValueError):
                                self.add(name, "FAIL", "退出码文件无法读取为整数")
                            else:
                                if type(code) is not int or code != recorded:
                                    self.add(name, "FAIL", "退出码文件与attempt记录不一致")
                paths = attempt.get("result_paths", [])
                if not isinstance(paths, list):
                    self.add(eid, "FAIL", "attempt result_paths须为数组")
                else:
                    for path in paths:
                        fmt = "json" if isinstance(path, str) and path.lower().endswith(".json") else "file"
                        self.file(directory, path, fmt, f"{eid}/{aid} result")
            seen[aid] = rid
        if data.get("status") == "completed" and not completed:
            self.add(eid, "FAIL", "completed实验缺实际完成的attempt")

    def print_result(self):
        print("| 检查项 | 状态 | 说明 |\n|---|---|---|")
        for name, status, message in self.rows:
            clean = lambda value: str(value).replace("|", "／").replace("\n", " ")
            print(f"| {clean(name)} | {status} | {clean(message)} |")
        print("仅核查文件与记录，不证明预登记时间、数据有效或科学结论；WARN不等于实验完成。")
        return int(any(status == "FAIL" for _, status, _ in self.rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--expdir", type=Path)
    group.add_argument("--all", dest="all_dir", type=Path)
    args = parser.parse_args()
    target = args.expdir or args.all_dir
    if not target.is_dir():
        parser.error(f"目录不存在：{target}")
    checks = Checks()
    root = args.all_dir or args.expdir.parent
    ledger = checks.ledger(root / "index.json")
    if args.expdir:
        checks.experiment(args.expdir, ledger.get(args.expdir.name))
    else:
        directories = {p.name: p for p in root.glob("exp-*") if p.is_dir()}
        if not directories and not ledger:
            checks.add("实验集合", "FAIL", "没有实验记录，不能视为检查成功")
        for eid, directory in sorted(directories.items()):
            checks.experiment(directory, ledger.get(eid))
        for eid in ledger.keys() - directories.keys():
            row = ledger[eid]
            if row.get("status") == "not_started" and row.get("meta_path") is None and row.get("status_reason"):
                checks.add(eid, "WARN", "计划尚未建实验目录：" + str(row["status_reason"]))
            else:
                checks.add(eid, "FAIL", "台账存在但缺实验目录/未开始原因")
    return checks.print_result()


if __name__ == "__main__":
    sys.exit(main())
