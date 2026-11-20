"""Opt-in real SDK and MCP protocol tests; HTTP backend is a controlled fixture.

Run in an environment with the pinned official MCP package and SDK installed:
DL_ASSISTANT_TEST_WANDB_CLIENTS=1 python -m unittest discover -s <scripts> -p test_official_clients.py
These tests do not deploy W&B Server or validate its license, storage or APIs.
"""
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

HELPERS = Path(__file__).resolve().parents[1] / "upstream/wandb-primary/scripts"


def clean_env(root):
    env = {k: v for k, v in os.environ.items() if not (
        k.startswith(("WANDB", "WEAVE", "WF_", "MCP_"))
        or k.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"})}
    env.update(WANDB_CONFIG_DIR=str(root / "config"), NETRC=str(root / "no-netrc"),
               WANDB_ERROR_REPORTING="false", WEAVE_DISABLED="true", WANDB_SILENT="true")
    return env


@unittest.skipUnless(os.environ.get("DL_ASSISTANT_TEST_WANDB_CLIENTS") == "1", "optional client dependencies")
class OfficialClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wandb-client-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_real_sdk_preserves_offline_identity_metrics_and_artifact(self):
        env = clean_env(self.root)
        env.update(WANDB_BASE_URL="http://127.0.0.1:9", WANDB_MODE="offline", WANDB_DISABLE_CODE="true")
        code = '''
import json,pathlib,wandb
from wandb.sdk.internal.datastore import DataStore
from wandb.proto import wandb_internal_pb2 as pb
root=pathlib.Path.cwd();identity={"scope_id":"test","experiment_id":"exp-1","attempt_id":"a1"}
(root/"result.json").write_text('{"observed":true}')
with wandb.init(project="dl-assistant-test",entity="local-test",id="dlatest1",dir=str(root),config={"dl_assistant":identity},settings=wandb.Settings(disable_job_creation=True,_disable_stats=True)) as run:
 for step,value in enumerate([1,0.9,0.8]):run.log({"train/loss":value},step=step)
 art=wandb.Artifact("test-result",type="result");art.add_file(str(root/"result.json"));run.log_artifact(art)
 run_path=pathlib.Path(run.dir).parent
store=DataStore();store.open_for_scan(str(next(run_path.glob("*.wandb"))));values=[];configs=[];artifacts=0
while True:
 data=store.scan_data()
 if data is None:break
 record=pb.Record();record.ParseFromString(data)
 if record.HasField("history"):
  for item in record.history.item:
   if item.key=="train/loss" or list(item.nested_key)==["train/loss"]:values.append(json.loads(item.value_json))
 if record.HasField("config") or record.HasField("run"):
  for item in (record.config if record.HasField("config") else record.run.config).update:
   if item.key=="dl_assistant":configs.append(json.loads(item.value_json))
 if record.HasField("artifact"):artifacts+=1
store.close()
assert values==[1,0.9,0.8] and identity in configs and artifacts==1
'''
        result = subprocess.run([sys.executable, "-c", code], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_official_helper_and_stdio_mcp_use_controlled_local_backend(self):
        requests_seen = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                requests_seen.append(self.path)
                viewer = {"id": "VGVzdFZpZXdlcg==", "username": "local-test", "entity": "local-test",
                          "email": "test@example.invalid", "teams": {"edges": []}, "name": "Local Test",
                          "admin": False, "flags": "{}", "deletedAt": None, "apiKeys": {"edges": []}}
                body = json.dumps({"data": {"viewer": viewer, "serverInfo": {"cliVersionInfo": {
                    "min_cli_version": "0.0.1", "max_cli_version": "99.0.0", "latest_cli_version": "0.28.1"}}}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        env = clean_env(self.root)
        env.update(WANDB_BASE_URL=f"http://127.0.0.1:{server.server_port}", WANDB_API_KEY="0" * 40,
                   WANDB_MCP_TOOL_PROFILE="models-only", WANDB_MCP_ACCESS_MODE="read-only",
                   MCP_WORKLOAD_PROFILE="local", WANDB_MCP_PROXY_DOCS="false", MCP_ANALYTICS_DISABLED="true",
                   PYTHONPATH=str(self.root), TEST_NETWORK_LOG=str(self.root / "external-attempts.txt"))
        (self.root / "sitecustomize.py").write_text('''
import socket,os
old_connect=socket.socket.connect;old_addr=socket.getaddrinfo
def allow(host):return host in ("127.0.0.1","localhost","::1",None)
def deny(host):
 with open(os.environ["TEST_NETWORK_LOG"],"a") as f:f.write(str(host)+"\\n")
 raise OSError("external network disabled for test")
def connect(self,address):
 if self.family in (socket.AF_INET,socket.AF_INET6) and not allow(address[0]):deny(address[0])
 return old_connect(self,address)
def addr(host,*a,**kw):
 if not allow(host):deny(host)
 return old_addr(host,*a,**kw)
socket.socket.connect=connect;socket.getaddrinfo=addr
''')
        code = (f"import sys;sys.path.insert(0,{str(HELPERS)!r});"
                "from wandb_helpers import get_api;print(get_api(timeout=3).viewer.username)")
        result = subprocess.run([sys.executable, "-c", code], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("local-test", result.stdout)

        async def workflow():
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            params = StdioServerParameters(command=sys.executable, args=["-c",
                "from wandb_mcp_server.entrypoint import cli;cli()"], env=env, cwd=str(self.root))
            with (self.root / "mcp-stderr.log").open("w") as log:
                async with stdio_client(params, errlog=log) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        names = {t.name for t in (await session.list_tools()).tools}
                        self.assertIn("get_run_history_tool", names)
                        self.assertNotIn("create_wandb_report_tool", names)
                        self.assertFalse(any("weave" in n or "aria" in n for n in names))
                        result = await session.call_tool("query_wandb_tool", {
                            "query": "query { viewer { username } }"})
                        self.assertFalse(result.isError)
                        self.assertIn("local-test", str(result))
        asyncio.run(asyncio.wait_for(workflow(), timeout=40))
        self.assertTrue(requests_seen)
        log = self.root / "external-attempts.txt"
        self.assertFalse(log.exists() and log.read_text().strip())


if __name__ == "__main__":
    unittest.main()
