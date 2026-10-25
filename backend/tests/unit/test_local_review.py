"""Regressions for reviewed lifecycle, routing and private-link recovery paths."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.scripts import cli
from backend.src.local import lifecycle
from backend.src.local.config import ROOT
from backend.src.local.store import Store


class DispatchTests(unittest.TestCase):
    def dispatch(self, environment, persisted, argv=None):
        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(cli, "dotenv_values", return_value=persisted),
            patch.object(cli, "load_dotenv"),
            patch.object(cli.os, "chdir"),
            patch.object(cli, "service", return_value=11) as cloud,
            patch("backend.src.local.cli.main", return_value=22) as local,
        ):
            result = cli.main(argv or ["status"])
        return result, cloud.called, local.called

    def test_environment_only_cloud_install_keeps_legacy_dispatch(self):
        for variable in ("BASETEN_API_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
            with self.subTest(variable=variable):
                self.assertEqual(
                    self.dispatch({variable: "test-only"}, {}), (11, True, False)
                )

    def test_environment_selection_precedes_dotenv_and_explicit_local_wins(self):
        self.assertEqual(
            self.dispatch(
                {"STORAGE_PROVIDER": "local"}, {"BASETEN_API_KEY": "test-only"}
            ),
            (22, False, True),
        )
        self.assertEqual(
            self.dispatch(
                {"STORAGE_PROVIDER": "supabase"}, {"STORAGE_PROVIDER": "local"}
            ),
            (11, True, False),
        )
        self.assertEqual(
            self.dispatch({"BASETEN_API_KEY": "test-only"}, {}, ["local", "status"]),
            (22, False, True),
        )
        self.assertEqual(self.dispatch({}, {}), (22, False, True))


class StartupWatchdogTests(unittest.TestCase):
    def run_supervisor(self, replacement_ready):
        clock = [1000.0]
        steps = iter([1000, 1181, 1182, 1363, 1364, 1545, 1546])
        workers = []
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            store = Store(directory)
            real_snapshot = store.snapshot

            def snapshot():
                value = real_snapshot()
                value["health"]["capture"] = {"last_frame": clock[0]}
                return value

            def wait(_seconds):
                try:
                    clock[0] = next(steps)
                    return False
                except StopIteration:
                    return True

            def popen(argv, **_kwargs):
                child = Mock()
                child.poll.return_value = None
                child.kill.side_effect = lambda: setattr(child.poll, "return_value", -9)
                child.terminate.side_effect = lambda: setattr(
                    child.poll, "return_value", -15
                )
                if argv[-1] == "worker":
                    workers.append(child)
                    # Simulate persisted ready health from a prior process, even
                    # after the supervisor's starting publication. It must not
                    # disable the initialization deadline of a new child.
                    stamp = clock[0] if replacement_ready and len(workers) == 2 else 1
                    with store.db() as db:
                        db.execute(
                            "INSERT OR REPLACE INTO meta VALUES (?,?)",
                            (
                                "health.model",
                                json.dumps({"state": "ready", "updated": stamp}),
                            ),
                        )
                return child

            event = Mock()
            event.wait.side_effect = wait
            config = {
                "installation": "test",
                "retention_days": 7,
                "max_image_bytes": 1000000,
                "min_free_bytes": 0,
            }
            with (
                patch.object(lifecycle, "home", return_value=directory),
                patch.object(lifecycle, "load", return_value=config),
                patch.object(lifecycle, "Store", return_value=store),
                patch.object(lifecycle.threading, "Event", return_value=event),
                patch.object(lifecycle.threading, "Thread"),
                patch.object(lifecycle.signal, "signal"),
                patch.object(lifecycle.os, "umask"),
                patch.object(lifecycle.time, "time", side_effect=lambda: clock[0]),
                patch.object(lifecycle.time, "monotonic", side_effect=lambda: clock[0]),
                patch.object(lifecycle.subprocess, "Popen", side_effect=popen),
                patch("backend.src.local.server.make_server", return_value=Mock()),
                patch.object(store, "snapshot", side_effect=snapshot),
                patch.object(store, "retain"),
                patch.object(store, "health", wraps=store.health) as health,
            ):
                lifecycle.supervise()
            return workers, health.call_args_list

    def test_hung_initialization_retries_three_times_ignoring_stale_ready(self):
        workers, calls = self.run_supervisor(False)
        self.assertEqual(len(workers), 3)
        self.assertTrue(all(child.kill.call_count == 1 for child in workers))
        failures = [call for call in calls if call.args == ("model", "failed")]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].kwargs["reason"], "initialization_timeout")
        self.assertEqual(failures[0].kwargs["attempts"], 3)

    def test_replacement_current_ready_clears_startup_deadline(self):
        workers, calls = self.run_supervisor(True)
        self.assertEqual(len(workers), 2)
        self.assertEqual(workers[0].kill.call_count, 1)
        self.assertEqual(workers[1].kill.call_count, 0)
        self.assertFalse(any(call.args == ("model", "failed") for call in calls))


class GalleryRetryTests(unittest.TestCase):
    @unittest.skipUnless(
        shutil.which("node") and (ROOT / "frontend/node_modules/typescript").exists(),
        "requires npm ci; runs actual TSX in Node with mocked browser APIs",
    )
    def test_transient_session_failure_reuses_removed_fragment_token(self):
        # Execute the actual component/effect, not a copy of its retry algorithm.
        script = r"""
const fs = require("fs"), vm = require("vm"), assert = require("assert");
const ts = require("./frontend/node_modules/typescript");
const source = fs.readFileSync("frontend/components/local-gallery.tsx", "utf8");
const js = ts.transpileModule(source, {compilerOptions: {
  module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
}}).outputText;
let effect, retry, cleanup, sessions = 0, statuses = 0, closed = false;
const bodies = [], states = [];
const location = {hash: "#token=test-private-token", pathname: "/"};
const react = {
 useState: value => [value, value => states.push(value)],
 useRef: value => ({current:value}), useEffect: fn => {effect=fn},
};
const context = {exports: {}, URLSearchParams, Date, console,
 require: name => name === "react" ? react : name === "react/jsx-runtime"
   ? {jsx:()=>null, jsxs:()=>null} : {},
 location, history:{replaceState:()=>{location.hash=""}},
 setInterval:()=>1, clearInterval:()=>{},
 setTimeout:fn=>{retry=fn;return 1}, clearTimeout:()=>{},
 fetch: async (url, options) => {
   if(url==="/api/session") {
     bodies.push(JSON.parse(options.body));sessions++;
     return {ok:sessions>1, status:sessions>1 ? 200 : 503};
   }
   statuses++; return {ok:true, json:async()=>({detections:[],health:{}})};
 },
 EventSource:class {addEventListener(){ } close(){closed=true}},
};
vm.runInNewContext(js,context);
context.exports.LocalGallery(); cleanup=effect();
const settle = () => new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await settle();
 assert.strictEqual(location.hash, "");
 assert.strictEqual(sessions,1);assert.strictEqual(statuses,0);
 assert.ok(retry);retry();await settle();
 assert.strictEqual(sessions,2);assert.strictEqual(statuses,1);
 assert.deepStrictEqual(bodies,[{token:"test-private-token"},{token:"test-private-token"}]);
 cleanup();assert.ok(closed);
})().catch(error=>{console.error(error);process.exitCode=1});
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stderr)
