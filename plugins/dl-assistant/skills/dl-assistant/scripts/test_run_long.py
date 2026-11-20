"""Launch regressions using an isolated tmux substitute, never user sessions."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('run-long.sh')


class LongRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="long run's ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        tmux = self.bin / 'tmux'
        tmux.write_text('#!/bin/bash\nif [ "$1" = has-session ]; then exit "${TEST_ACTIVE:-1}"; fi\nif [ "$1" = new-session ]; then\n [ "${TEST_LAUNCH_FAIL:-0}" = 1 ] && exit 1\n bash -c "${@: -1}"\nfi\n')
        tmux.chmod(0o700)
        self.logs = self.root / 'logs'
        self.logs.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + ':' + os.environ['PATH'])

    def run_task(self, name='attempt-1', command='printf first', expected=0):
        r = subprocess.run(['bash', str(SCRIPT.resolve()), name, str(self.logs), command],
                           env=self.env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode, expected, r.stdout + r.stderr)
        return r

    def test_success_and_failure_exit_codes(self):
        self.run_task()
        self.assertEqual((self.logs / 'attempt-1.log').read_text(), 'first')
        self.assertEqual((self.logs / 'attempt-1.EXIT_CODE').read_text().strip(), '0')
        self.run_task('attempt-2', 'printf failure; exit 7')
        self.assertEqual((self.logs / 'attempt-2.EXIT_CODE').read_text().strip(), '7')

    def test_existing_evidence_is_not_overwritten(self):
        for suffix in ('.log', '.EXIT_CODE'):
            p = self.logs / ('attempt-1' + suffix)
            p.write_text('old evidence')
            self.run_task(expected=1)
            self.assertEqual(p.read_text(), 'old evidence')
            p.unlink()

    def test_completed_name_cannot_be_reused(self):
        self.run_task()
        before = (self.logs / 'attempt-1.log').read_bytes()
        self.run_task(command='printf replacement', expected=1)
        self.assertEqual((self.logs / 'attempt-1.log').read_bytes(), before)

    def test_launch_failure_is_not_reported_as_started(self):
        self.env['TEST_LAUNCH_FAIL'] = '1'
        r = self.run_task(expected=1)
        self.assertNotIn('已 detach 启动', r.stdout)
        self.assertFalse((self.logs / 'attempt-1.EXIT_CODE').exists())

    def test_invalid_names_do_not_create_paths(self):
        for name in ('../escape', '-option', 'with space', 'x.y', 'x:y', ''):
            self.run_task(name=name, expected=2)
        self.assertEqual(list(self.logs.iterdir()), [])

    def test_existing_session_is_not_replaced(self):
        self.env['TEST_ACTIVE'] = '0'
        self.run_task(expected=1)
        self.assertEqual(list(self.logs.iterdir()), [])

    def test_launch_reservation_prevents_racing_writers(self):
        command = ['bash', str(SCRIPT.resolve()), 'race', str(self.logs), 'printf race']
        a = subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        b = subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        a.communicate(timeout=5)
        b.communicate(timeout=5)
        self.assertEqual(sorted([a.returncode, b.returncode]), [0, 1])
        self.assertEqual((self.logs / 'race.log').read_text(), 'race')


if __name__ == '__main__':
    unittest.main()
