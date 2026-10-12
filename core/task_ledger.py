"""Small durable claim ledger for headless inbox delivery.

An explicit dedupe_key identifies the same deliverable across different mails.
Without one, the mail id is the key, so distinct follow-ups are never merged.
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager


SCHEMA = """CREATE TABLE IF NOT EXISTS tasks (
    dedupe_key TEXT PRIMARY KEY, owner TEXT NOT NULL, status TEXT NOT NULL,
    done_when TEXT NOT NULL, evidence TEXT NOT NULL, budget TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0, updated REAL NOT NULL,
    mail_id TEXT NOT NULL, last_error TEXT NOT NULL DEFAULT ''
)"""


class TaskLedger:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.execute(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute('PRAGMA busy_timeout=10000')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def card(aid, mail):
        spec = mail.get('task') if isinstance(mail.get('task'), dict) else mail
        key = spec.get('dedupe_key') or ('mail:' + aid + ':' + str(mail.get('id', '')))
        if key == 'mail:' + aid + ':':
            raise ValueError('mail id or dedupe_key required')
        evidence = spec.get('evidence', [])
        if not isinstance(evidence, list):
            raise ValueError('evidence must be a list')
        budget = spec.get('budget', {})
        if not isinstance(budget, dict):
            raise ValueError('budget must be an object')
        depends_on = spec.get('depends_on', [])
        if not isinstance(depends_on, list) or not all(isinstance(x, str) for x in depends_on):
            raise ValueError('depends_on must be a list of task keys')
        return {'dedupe_key': str(key), 'owner': aid,
                'done_when': str(spec.get('done_when') or 'CLI exits 0'),
                'evidence': evidence,
                'depends_on': depends_on,
                'budget': {'max_attempts': min(3, max(1, int(budget.get('max_attempts', 2)))),
                           'wall_seconds': min(600, max(30, int(budget.get('wall_seconds', 420)))),
                           'max_tokens': min(200000, max(10000, int(budget.get('max_tokens', 60000))))},
                'mail_id': str(mail.get('id', ''))}

    def claim(self, card):
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for dependency in card['depends_on']:
                dependency_row = db.execute('SELECT status FROM tasks WHERE dedupe_key=?',
                                            (dependency,)).fetchone()
                if dependency_row is None or dependency_row[0] != 'done':
                    return 'waiting_dependency'
            row = db.execute('SELECT owner,status,attempts,updated,budget,done_when,evidence FROM tasks WHERE dedupe_key=?',
                             (card['dedupe_key'],)).fetchone()
            if row:
                owner, status, attempts, updated, saved_budget, done_when, evidence = row
                if owner != card['owner']:
                    return 'other_owner'
                if done_when != card['done_when'] or json.loads(evidence) != card['evidence']:
                    return 'changed_require_new_key'
                if status == 'done':
                    return 'duplicate'
                limit = json.loads(saved_budget)['max_attempts']
                if attempts >= limit:
                    return 'exhausted'
                if status == 'running' and now - updated < json.loads(saved_budget)['wall_seconds'] + 60:
                    return 'busy'
                db.execute('UPDATE tasks SET status=?,attempts=attempts+1,updated=?,mail_id=? WHERE dedupe_key=?',
                           ('running', now, card['mail_id'], card['dedupe_key']))
            else:
                db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,1,?,? ,?)',
                           (card['dedupe_key'], card['owner'], 'running', card['done_when'],
                            json.dumps(card['evidence'], ensure_ascii=False),
                            json.dumps(card['budget']), now, card['mail_id'], ''))
        return 'claimed'

    def finish(self, card, cli_ok, root, error=''):
        missing = []
        for item in card['evidence']:
            path = item.get('path') if isinstance(item, dict) else item
            target = path if isinstance(path, str) and os.path.isabs(path) else os.path.join(root, str(path))
            if not isinstance(path, str) or not os.path.isfile(target):
                missing.append(str(path))
                continue
            if isinstance(item, dict):
                if os.path.getsize(target) < int(item.get('min_bytes', 0)):
                    missing.append(str(path) + ' too small')
                    continue
                required = item.get('contains', [])
                if required:
                    with open(target, encoding='utf-8', errors='replace') as fh:
                        content = fh.read()
                    if not all(text in content for text in required):
                        missing.append(str(path) + ' missing required text')
        done = bool(cli_ok and not missing)
        reason = error or ('missing evidence: ' + ', '.join(missing) if missing else '')
        with self.connect() as db:
            db.execute('UPDATE tasks SET status=?,updated=?,last_error=? WHERE dedupe_key=?',
                       ('done' if done else 'failed', time.time(), reason[:1000], card['dedupe_key']))
        return done, reason

    def get(self, key):
        with self.connect() as db:
            return db.execute('SELECT status,attempts,last_error FROM tasks WHERE dedupe_key=?', (key,)).fetchone()
