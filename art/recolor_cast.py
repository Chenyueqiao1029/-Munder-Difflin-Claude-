# -*- coding: utf-8 -*-
"""把像素美术层做成可复用的「美术 UI 层」：7 个基础角色 → 任意 N 个（默认 31）。

思路（不新增美术工作量）：
  · 取 7 个基础角色图（assets/chars/*.sheet.png / *.portrait.png）
  · 用「色相偏移 + 饱和度/明度微调」派生 N 个不重样的配色变体
  · 只改**有颜色**的像素（饱和度 > 阈值），保留黑白描边与阴影 → 不会变成一坨糊
  · 输出 contacts 预览图 + roster 清单（给上层框架当美术 UI 用）

产物：build/cast31/（图），build/roster31.json（清单），build/contact-sheet.png（预览）
"""
import io
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHARS = os.path.join(REPO, 'assets', 'chars')
OUT = os.path.join(REPO, 'build', 'cast31')
CONTACT = os.path.join(REPO, 'build', 'contact-sheet.png')
ROSTER = os.path.join(REPO, 'build', 'roster31.json')

# 31 个角色的"名字/角色"，取自 oh-my-coder 的 agent 命名风格（上层框架可换成任意清单）
SLOTS = [
    ('explore', '探索者', 'Explore'), ('analyst', '分析师', 'Analyst'),
    ('architect', '架构师', 'Architect'), ('executor', '执行者', 'Executor'),
    ('verifier', '验证者', 'Verifier'), ('reviewer', '代码评审', 'Code Reviewer'),
    ('cleaner', '清理工', 'Code Cleaner'), ('simplifier', '简化师', 'Code Simplifier'),
    ('research', '研究员', 'Code Research'), ('api', '接口工', 'API Agent'),
    ('auth', '权限官', 'Auth Agent'), ('db', '数据库官', 'DB Agent'),
    ('frontend', '前端工', 'Frontend Agent'), ('backend', '后端工', 'Backend Agent'),
    ('tester', '测试工', 'Test Agent'), ('docs', '文档官', 'Docs Agent'),
    ('refactor', '重构师', 'Refactor Agent'), ('perf', '性能官', 'Perf Agent'),
    ('security', '安全官', 'Security Agent'), ('debug', '排障师', 'Debug Agent'),
    ('devops', '运维官', 'DevOps Agent'), ('data', '数据官', 'Data Agent'),
    ('ui', '界面工', 'UI Agent'), ('i18n', '多语官', 'i18n Agent'),
    ('ci', '流水线官', 'CI Agent'), ('deps', '依赖官', 'Deps Agent'),
    ('migration', '迁移官', 'Migration Agent'), ('observability', '观测官', 'Observability Agent'),
    ('planner', '规划师', 'Planner'), ('coordinator', '协调员', 'Coordinator'),
    ('steward', '管家', 'Steward'),
]


def recolor(img, hue_shift, sat_mul=1.0, val_mul=1.0, sat_min=40):
    """只给"有颜色"的像素换色相；黑白描边/阴影保留。纯 PIL 通道运算，快到毫秒级。"""
    r, g, b, a = img.split()
    rgb = Image.merge('RGB', (r, g, b)).convert('HSV')
    H, S, V = rgb.split()
    shift = int(round(255 * hue_shift)) % 256
    H2 = H.point(lambda v: (v + shift) % 256)
    S2 = S.point(lambda v: min(255, int(v * sat_mul)))
    V2 = V.point(lambda v: min(255, int(v * val_mul)))
    # 掩码：饱和度高于阈值才换色
    mask = S.point(lambda v: 255 if v >= sat_min else 0)
    recolored = Image.merge('HSV', (H2, S2, V2)).convert('RGB')
    blended = Image.composite(recolored, Image.merge('RGB', (r, g, b)), mask)
    rr, gg, bb = blended.split()
    return Image.merge('RGBA', (rr, gg, bb, a))


def main():
    bases = sorted(f[:-10] for f in os.listdir(CHARS) if f.endswith('.sheet.png'))
    if not bases:
        print('  ✗ assets/chars 里没有 *.sheet.png')
        return 1
    print('  基础角色 %d 个: %s' % (len(bases), ', '.join(bases)))
    os.makedirs(OUT, exist_ok=True)

    roster = []
    thumbs = []
    for i, (key, cn, en) in enumerate(SLOTS):
        base = bases[i % len(bases)]
        # 每个角色一套独特的配色：色相分散 + 饱和度/明度轻微变化
        hue = (i * 0.61803398875) % 1.0          # 黄金角，保证相邻不撞色
        sat = 0.85 + (i % 5) * 0.06
        val = 0.94 + (i % 4) * 0.03
        sh = Image.open(os.path.join(CHARS, base + '.sheet.png')).convert('RGBA')
        po = Image.open(os.path.join(CHARS, base + '.portrait.png')).convert('RGBA')
        sh2 = recolor(sh, hue, sat, val)
        po2 = recolor(po, hue, sat, val)
        sh2.save(os.path.join(OUT, key + '.sheet.png'))
        po2.save(os.path.join(OUT, key + '.portrait.png'))
        thumbs.append((key, cn, po2))
        roster.append({
            'id': key, 'name': cn, 'nameEn': en, 'role': en,
            'base': base, 'hue': round(hue, 4), 'saturation': round(sat, 3), 'value': round(val, 3),
            'sheet': 'cast31/%s.sheet.png' % key, 'portrait': 'cast31/%s.portrait.png' % key,
            'seat': None,                      # 由上层按办公室布局分配（31 工位见 build/office31.json）
        })
    io.open(ROSTER, 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'count': len(roster), 'unit': [72, 108], 'rows': ['front', 'back', 'side'],
                    'columns': 7, 'agents': roster}, ensure_ascii=False, indent=2))
    print('  已生成 %d 个角色 → %s' % (len(roster), OUT))
    print('  清单 → %s' % ROSTER)

    # 预览接触表（8 列）
    cw, chh = 144, 216
    cols = 8
    rows = (len(thumbs) + cols - 1) // cols
    scale = 0.55
    tw, th = int(cw * scale), int(chh * scale)
    sheet = Image.new('RGBA', (cols * tw, rows * (th + 22)), (24, 24, 32, 255))
    for idx, (key, cn, im) in enumerate(thumbs):
        x = (idx % cols) * tw
        y = (idx // cols) * (th + 22)
        sheet.alpha_composite(im.resize((tw, th), Image.NEAREST), (x, y))
        try:
            from PIL import ImageDraw
            d = ImageDraw.Draw(sheet)
            d.text((x + 4, y + th + 4), '%s %s' % (key[:11], cn[:4]), fill=(230, 230, 240, 255))
        except Exception:
            pass
    sheet.save(CONTACT)
    print('  预览接触表 → %s' % CONTACT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
