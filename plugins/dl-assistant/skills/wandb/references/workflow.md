# W&B 接入、运行和查回流程

本文件说明如何核实际实例和 logger，把每次尝试记录到 W&B，以及如何独立查回并保存需要的证据。

## 1. 首次接入并分开核三条路径

1. 从 setup 的 `tracking_ref` 或[部署说明](deployment.md)核目标实例、entity、project、SDK 与 MCP 的实际版本，以及允许写入的范围。先找项目现有的 logger、配置和环境。练习或接入测试使用独立测试项目。
2. 用项目已配置的实际解释器核 SDK。检查 `WANDB_BASE_URL` 非空且对应目标实例，API key 由私有配置提供。按实际环境核代理、容器内访问地址及已有设置。

```bash
wandb --version
test -n "${WANDB_BASE_URL:-}" && test -n "${WANDB_API_KEY:-}"
```

3. 在已确认可写的测试项目中，按[官方 SDK 用法](../upstream/wandb-primary/references/WANDB_SDK.md)记录已知配置、少量已知步数及适用时的小型测试产物。用实际 logger 运行。需要单独用 SDK 做最小探测时，在项目已核的实例环境和测试用身份下执行，例如：

```python
import os
import wandb

with wandb.init(
    entity=os.environ["WANDB_TEST_ENTITY"],
    project=os.environ["WANDB_TEST_PROJECT"],
    id=os.environ["WANDB_TEST_RUN_ID"],
    config={"probe": "sdk-write"},
) as run:
    for step, value in enumerate((1.0, 0.75, 0.5)):
        run.log({"probe/value": value}, step=step)
```

测试变量填已核的测试项目及唯一测试 run ID。实际接入若要验可追溯身份，在测试配置同步记录预登记的 `config.dl_assistant`。只跑本地或离线测试时，按实际范围记录。

4. **API 独立查回。** 在另一个已指向同实例的进程用 [官方 API](../upstream/wandb-primary/references/WANDB_SDK.md) 按完整路径查看。

```python
import os
import wandb

api = wandb.Api()
run = api.run(os.environ["WANDB_RUN_PATH"])  # entity/project/run_id
print(run.id, run.config.get("probe"), run.config.get("dl_assistant"))
print(list(run.scan_history(keys=["_step", "probe/value"], page_size=100)))
```

本例只针对测试指标。真实项目只读取需要核对的字段，将所需值和摘要保存在内部证据中。

5. **MCP 独立查回。** 在客户端发现实际已安装的 W&B 只读工具，按其参数先核同一个项目、run ID 和配置，再取所需指标历史。已有测试版本中可用项目查询及 `get_run_history_tool`，实际名称和参数从 discovery 读取。逐项对照已知步数、数值和需要核的产物，保存调用来源与结果。SDK 写入、API 查回和 MCP 查回分别记录，接入状态写入项目配置。

## 2. 记录、重试或恢复一次运行

按[实验记录](experiment-records.md)从批准设计登记重复、尝试与 run ID。运行前固定实际 Git 提交、配置、权重、数据和协议。在实际 logger 的 `config.dl_assistant` 记录同一本地身份，分布式任务按框架核主要记录进程。重试或 checkpoint 恢复用已登记的重复编号，保留原尝试及两次日志。

服务不可达时按已批准的策略处理。保留本地输出和待同步目录。补同步前从同一实例查项目和 run ID，确认实际接收状态及尚缺材料。确认待同步目录及目标后，按已安装 CLI 核用法并同步：

```bash
wandb sync --help
wandb sync "$offline_run_dir"
```

然后独立查回需要的配置、指标和产物，保存已查区间。记录实际失败或只取到部分结果的状态。科研记录分别写实际退出、测量及同步情况。

## 3. 从本地台账查回已有记录

1. 列出这次要查的实验及全部相关尝试，登记每个 run 的完整身份和应查指标、step、单位、配置、权重或产物。按实际比较口径说明纳入与排除。
2. 用 API 或 MCP 查询。各指标记录所用键、实际 step 范围、采样、分页和是否达到上限。不同步记录的指标按键分别查看；只有共同存在行的联合查询不能说明其他 step 无记录。查看产物时保留固定版本、digest 和当前可访问性。
3. 按[快照字段](experiment-records.md#3-独立查回已同步的范围)保存查询和覆盖。只查回摘要值时，将该字段登记为已核；后续需要完整曲线时另查所需 step。对失败、离线或未同步的尝试，保留本地版本和待补方式。

## 4. 核交接文件

```bash
python3 "$wandb_skill_dir/scripts/check_tracking.py" --meta "$experiment_meta"
bash "$cpe_skill_dir/scripts/check-run-artifacts.sh" --pkgdir "$handoff_dir"
```

第一条用于研究实验元记录。第二条用于论文回包，并核声明 W&B 的尝试。接收端缺离线恢复目录时，论文检查打印 `UNCHECKED` 并退出 3；身份矛盾、声明 `synced` 却缺应随包的查回快照等记录错误退出 1。两个检查器都读取已保存的本地证据。远端存续、证据有效性和结论仍按实际查询和原实验记录核实。
