import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent_driver2 as driver
from task_ledger import TaskLedger


class LedgerTests(unittest.TestCase):
    def test_duplicate_retry_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = TaskLedger(os.path.join(tmp, 'ledger.sqlite3'))
            mail = {'id': 'm1', 'dedupe_key': 'job:1', 'done_when': 'output exists',
                    'evidence': ['output.txt'], 'budget': {'max_attempts': 2}}
            card = ledger.card('agent', mail)
            self.assertEqual(ledger.claim(card), 'claimed')
            self.assertEqual(ledger.claim(card), 'busy')
            self.assertFalse(ledger.finish(card, True, tmp)[0])
            self.assertEqual(ledger.claim(card), 'claimed')
            Path(tmp, 'output.txt').write_text('verified', encoding='utf-8')
            self.assertTrue(ledger.finish(card, True, tmp)[0])
            self.assertEqual(ledger.claim(ledger.card('agent', {**mail, 'id': 'm2'})), 'duplicate')
            self.assertEqual(ledger.claim(ledger.card('agent', {**mail, 'id': 'm3',
                                                               'done_when': 'changed acceptance'})),
                             'changed_require_new_key')
            self.assertEqual(ledger.get('job:1')[:2], ('done', 2))

    def test_failed_task_stops_at_attempt_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = TaskLedger(os.path.join(tmp, 'ledger.sqlite3'))
            card = ledger.card('agent', {'id': 'm1', 'budget': {'max_attempts': 1}})
            self.assertEqual(ledger.claim(card), 'claimed')
            self.assertFalse(ledger.finish(card, False, tmp, 'failed')[0])
            self.assertEqual(ledger.claim(card), 'exhausted')

    def test_mail_id_fallback_does_not_merge_followups(self):
        one = TaskLedger.card('agent', {'id': 'm1'})
        two = TaskLedger.card('agent', {'id': 'm2'})
        self.assertNotEqual(one['dedupe_key'], two['dedupe_key'])
        self.assertNotEqual(one['dedupe_key'], TaskLedger.card('other', {'id': 'm1'})['dedupe_key'])

    def test_dependency_blocks_review_until_execution_finishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = TaskLedger(os.path.join(tmp, 'ledger.sqlite3'))
            execution = ledger.card('doer', {'id': 'm1', 'dedupe_key': 'deliverable'})
            review = ledger.card('reviewer', {'id': 'm2', 'dedupe_key': 'review',
                                             'depends_on': ['deliverable']})
            self.assertEqual(ledger.claim(review), 'waiting_dependency')
            self.assertEqual(ledger.claim(execution), 'claimed')
            self.assertTrue(ledger.finish(execution, True, tmp)[0])
            self.assertEqual(ledger.claim(review), 'claimed')


class DriverTests(unittest.TestCase):
    def test_single_instance_lock(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(driver, 'LOCK', os.path.join(tmp, 'driver.lock')):
            with driver.single_instance() as first:
                with driver.single_instance() as second:
                    self.assertTrue(first)
                    self.assertFalse(second)
            with driver.single_instance() as next_run:
                self.assertTrue(next_run)

    def test_only_first_mail_is_passed_to_one_run_and_failure_is_not_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            hive = Path(tmp, 'hive')
            inbox = hive / 'agents' / 'agent' / 'inbox'
            inbox.mkdir(parents=True)
            for name in ('a.json', 'b.json'):
                (inbox / name).write_text(json.dumps({'id': name, 'subject': name}), encoding='utf-8')
            ledger = TaskLedger(os.path.join(tmp, 'ledger.sqlite3'))
            state = {}

            class FakeBridge:
                def __init__(self, *args): pass
                def start(self): pass
                def line(self, line): pass
                def finish(self, failed=False): pass

            class FakeProcess:
                returncode = 1
                stdout = ['failure\n']
                def poll(self): return self.returncode
                def wait(self): return self.returncode
                def kill(self): pass

            cfg = {'name': 'agent', 'out': 'agent', 'cmd': ['fake', '{prompt}'], 'timeout': 30}
            prompts = []
            def fake_popen(cmd, **kwargs):
                prompts.append(cmd[-1])
                return FakeProcess()
            with patch.object(driver, 'HIVE', str(hive)), patch.object(driver, 'HOME', tmp), \
                 patch.object(driver, 'PROJ', str(Path(tmp, 'project'))), \
                 patch.object(driver, 'STREAMS', str(Path(tmp, 'streams'))), \
                 patch.object(driver, 'resolve', lambda x: x), \
                 patch.object(driver.subprocess, 'Popen', side_effect=fake_popen), \
                 patch('native_hook_bridge.HookBridge', FakeBridge):
                result = driver.run_one('agent', cfg, state, ledger)
            self.assertTrue(result.startswith('failed:'))
            self.assertEqual(len(prompts), 1)
            self.assertIn('a.json', prompts[0])
            self.assertNotIn('b.json', prompts[0])
            self.assertNotIn('a.json', state['agent'].get('seen', []))
            self.assertTrue((inbox / 'a.json').exists())


if __name__ == '__main__':
    unittest.main()
