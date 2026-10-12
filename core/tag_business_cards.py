"""Add explicit acceptance metadata to the two pending Lightcup inbox mails."""
import json
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIVE = Path(r'C:\Users\徐\yueqiaochangetheworld\hive')
BACKUP = HERE / 'backup-taskcards-20261012'
import os
BASE = os.environ.get('MD_PROJECT_DIR', 'projects/example-project/')  # 指向你的项目目录
EXEC = 'LIGHTCUP-closeout:execution:v1'
SPECS = {
    'tianshu-mv3d0002': {
        'dedupe_key': EXEC,
        'done_when': 'T1/T2 交付物齐全，README 两处写实测值或明确前置；报告含复跑命令和原始输出',
        'evidence': [
            {'path': BASE + '验收报告-性能实测.md', 'min_bytes': 300, 'contains': ['命令']},
            {'path': BASE + '06-代码改动/接入补丁.patch', 'min_bytes': 100},
            {'path': BASE + '接入说明-含前置依赖.md', 'min_bytes': 200},
            {'path': BASE + 'README.md', 'min_bytes': 300},
        ],
        'budget': {'max_attempts': 2, 'wall_seconds': 420, 'max_tokens': 60000},
    },
    'tianshu-approve-mv3e02': {
        'dedupe_key': 'LIGHTCUP-closeout:review:v1',
        'depends_on': [EXEC],
        'done_when': '独立复跑执行星域的命令、测试补丁及文档，并记录通过项与卡点',
        'evidence': [
            {'path': BASE + '验收报告-独立复核.md', 'min_bytes': 250, 'contains': ['命令']},
        ],
        'budget': {'max_attempts': 2, 'wall_seconds': 420, 'max_tokens': 60000},
    },
}


def main():
    files = {}
    for aid, task in SPECS.items():
        path = HIVE / 'agents' / aid / 'inbox' / '2026-10-11T15-52-59-000Z-lightcup-closeout.json'
        mail = json.loads(path.read_text(encoding='utf-8'))
        if mail.get('to') != aid or mail.get('conversation') != 'LIGHTCUP-closeout':
            raise RuntimeError('mail identity mismatch: ' + str(path))
        files[aid] = (path, mail, task)
    BACKUP.mkdir(exist_ok=True)
    for aid, (path, mail, task) in files.items():
        if mail.get('task') == task:
            continue
        backup = BACKUP / (aid + '.json')
        if not backup.exists():
            shutil.copy2(path, backup)
        mail['task'] = task
        tmp = path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(mail, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp, path)
        print(aid, task['dedupe_key'])


if __name__ == '__main__':
    main()
