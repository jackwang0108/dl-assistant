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
INFERENCES = {"pending", "supported", "contradicted", "insufficient_evidence",
              "not_identifiable", "invalid_data", "not_applicable"}

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

    def file(self, directory, value, fmt, name):
        if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
            self.add(name, "FAIL", "需提供实验目录内相对文件路径")
            return
        path = (directory / value).resolve()
        if not path.is_relative_to(directory.resolve()):
            self.add(name, "FAIL", "文件不在实验目录内")
        elif not path.is_file() or path.stat().st_size == 0:
            self.add(name, "FAIL", f"文件缺失或为空：{value}")
        elif fmt == "json":
            before = len(self.rows)
            self.load(path, name, object_required=False)
            if len(self.rows) == before:
                self.add(name, "PASS", f"JSON可解析：{value}")
        elif isinstance(fmt, str) and fmt in {"text", "file"}:
            self.add(name, "PASS", f"文件存在且非空：{value}")
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
            if not isinstance(row.get("status"), str) or row["status"] not in STATUSES:
                self.add(eid, "FAIL", "台账status无效")
        return result

    def experiment(self, directory, row, check_artifacts=True, portable=False):
        eid = directory.name
        data = self.load(directory / "meta.json", eid)
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
            for field in ("status", "data_validity", "inference_status"):
                if row.get(field) != data.get(field):
                    self.add(eid, "FAIL", f"台账与meta的{field}不一致")
        design = data.get("design_record")
        if not isinstance(design, dict) or not design.get("path"):
            self.add(eid, "FAIL", "缺设计副本引用，不能声称运行前登记")
        else:
            self.file(directory, design["path"], "json", eid + " design")
        mode_field = "interpretation_plan" if data.get("design_mode") == "confirmation" else "analysis_plan"
        if not data.get(mode_field):
            self.add(eid, "FAIL", f"需{mode_field}，探索无需keep判据")
        if status in {"in_progress", "completed", "failed"}:
            manual_theory = data.get("type") == "theory" and data.get("execution_basis") == "manual"
            if not manual_theory and not data.get("git_commit"):
                self.add(eid, "FAIL", "已执行代码任务缺代码commit；人工理论核查须明确execution_basis=manual")
            if not isinstance(data.get("attempts"), list) or not data["attempts"]:
                self.add(eid, "FAIL", "已执行任务缺attempt记录")
            if not isinstance(data.get("code_dirty"), bool):
                self.add(eid, "FAIL", "需明确code_dirty")
            elif data["code_dirty"]:
                self.file(directory, data.get("code_diff_path"), "text", eid + " code diff")
        self.attempts(data, directory, eid)
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
        self.file(directory, "报告.md", "text", eid + " 报告")

    def attempts(self, data, directory, eid):
        attempts = data.get("attempts")
        if not isinstance(attempts, list):
            self.add(eid, "FAIL", "attempts必须是数组")
            return
        seen = {}
        completed = False
        manual = data.get("type") == "theory" and data.get("execution_basis") == "manual"
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
            command = attempt.get("command") or attempt.get("script")
            if not isinstance(command, str) or not command.strip():
                self.add(eid, "FAIL", "attempt缺实际命令或操作")
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
                    ref = attempt.get("manual_record_ref")
                    self.file(directory, ref.get("path") if isinstance(ref, dict) else None,
                              "text", eid + " manual record")
                elif type(code) is not int or code != 0:
                    self.add(eid, "FAIL", "completed代码attempt须有实际退出码0")
            resume = attempt.get("resume_from")
            if resume is not None and (not isinstance(resume, str) or resume not in seen
                                       or seen[resume] != rid):
                self.add(eid, "FAIL", "resume_from须指同一重复的更早attempt")
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
            if row.get("status") == "not_started" and row.get("status_reason"):
                checks.add(eid, "WARN", "计划尚未建实验目录：" + str(row["status_reason"]))
            else:
                checks.add(eid, "FAIL", "台账存在但缺实验目录/未开始原因")
    return checks.print_result()


if __name__ == "__main__":
    sys.exit(main())
