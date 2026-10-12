# -*- coding: utf-8 -*-
"""把「自定义像素角色包」打进官方 renderer（不动其他逻辑，保留 godCommand 等特性）。

补丁点（官方 bundle 里可读的原文）：
  A. 主 bundle 顶部注入 window.__MD_CAST = { 角色名: {sheet, portrait} }
  B. OfficeFloor chunk：getCastFrames 优先用自定义帧表（36×64 格）
  C. OfficeFloor chunk：新增 MD_ANIM_FRAMES（走 0-2 / 打字 3-4 / 阅读 5-6），按标记选择
  D. 主 bundle：卡片头像先画程序化、自定义图解码完再覆盖
"""
import argparse
import base64
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, 'tools')
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

CAST = ['stanley', 'dwight', 'angela', 'oscar', 'jim', 'kevin', 'michael']
CELL_W, CELL_H = 72, 108


def data_url(path):
    with open(path, 'rb') as fh:
        return 'data:image/png;base64,' + base64.b64encode(fh.read()).decode('ascii')


class InstallError(RuntimeError):
    pass


_ROLLBACK = None


def _load_config():
    try:
        from md_config import cfg, cfg_with_source
    except (ImportError, SyntaxError) as exc:
        raise InstallError(
            '无法加载 tools/md_config.py（%s）。请确认该文件存在且能通过 py_compile。' % exc
        )
    return cfg, cfg_with_source


def _require_app(app):
    out_dir = os.path.join(app, 'resources', 'app', 'out') if app else ''
    if not app or not os.path.isdir(out_dir):
        raise InstallError(
            '找不到 Munder Difflin 应用目录。请设置环境变量 MD_APP_DIR，'
            '或在仓库根 config.json 中填写 app_dir（应包含 resources\\app\\out）。'
        )
    return out_dir


def _require_esbuild(esbuild):
    if not esbuild or not os.path.isfile(esbuild):
        raise InstallError(
            '找不到 esbuild。请设置环境变量 MD_ESBUILD，'
            '或在仓库根 config.json 中填写 esbuild（指向 esbuild.exe）。'
        )


def _pick_stage(app, configured, source):
    if source in ('config.json', 'env:MD_STAGE_DIR'):
        return configured
    candidates = [configured, os.path.join(os.path.dirname(app), '_renderer-patched')]
    return next((p for p in candidates if p and os.path.isdir(p)), configured or candidates[-1])


def _pick_renderer(out_dir, configured, source):
    if source in ('config.json', 'env:MD_RENDERER_DIR'):
        candidates = [configured]
    else:
        official = sorted(
            (os.path.join(out_dir, name) for name in os.listdir(out_dir)
             if name.startswith('renderer.official-')),
            reverse=True,
        )
        candidates = official + [configured, os.path.join(out_dir, 'renderer')]
    renderer = next((p for p in candidates if p and os.path.isdir(p)), '')
    if not renderer:
        raise InstallError(
            '找不到 renderer 源目录。请设置 MD_RENDERER_DIR，或在 config.json 中填写 '
            'renderer_dir（目录内应有 index.html 和 assets）。'
        )
    return renderer


def _dry_run(paths, sources):
    print('干跑模式：路径校验通过，不会写入任何文件。')
    print('  app      : %s [%s]' % (paths['app'], sources['app']))
    print('  esbuild  : %s [%s]' % (paths['esbuild'], sources['esbuild']))
    print('  renderer : %s [%s]' % (paths['source'], sources['renderer']))
    print('  将重建   : %s' % paths['stage'])
    print('  将修改   : %s' % os.path.join(paths['stage'], 'index.html'))
    print('  将修改   : %s' % os.path.join(paths['stage'], 'assets', 'index-*.js'))
    print('  将修改   : %s' % os.path.join(paths['stage'], 'assets', 'OfficeFloor-*.js'))
    print('  可能修改 : %s' % os.path.join(paths['stage'], 'assets', 'global-*.js'))
    print('  将备份到 : %s' % paths['backup'])


def _backup_stage(stage, backup_root):
    if not os.path.isdir(stage):
        return None
    os.makedirs(backup_root, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    target = os.path.join(backup_root, 'renderer-' + stamp)
    shutil.copytree(stage, target)
    print('原补丁目录已备份:', target)
    return target


def _rollback_stage(stage, backup_path):
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    if backup_path:
        shutil.copytree(backup_path, stage)
        print('安装失败，已从备份回滚:', stage)
    else:
        print('安装失败，已移除未完成的补丁目录:', stage)


def _syntax_gate(esbuild, paths):
    with tempfile.TemporaryDirectory(prefix='starhive-esbuild-') as temp_dir:
        for index, path in enumerate(dict.fromkeys(paths)):
            if not path or not os.path.isfile(path):
                continue
            out = os.path.join(temp_dir, 'gate-%d.js' % index)
            result = subprocess.run(
                [esbuild, '--log-level=error', '--outfile=' + out,
                 '--allow-overwrite', path],
                capture_output=True, text=True, encoding='utf-8', errors='replace',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
            if result.returncode:
                detail = (result.stderr or result.stdout or '未知语法错误').strip()[:1200]
                raise InstallError('esbuild 语法门未通过：%s\n%s' % (path, detail))
    print('  esbuild 语法门: 通过')


def install(dry_run=False):
    global _ROLLBACK
    cfg, cfg_with_source = _load_config()
    app_value, app_source = cfg_with_source('app_dir')
    app = os.path.abspath(app_value) if app_value else ''
    out_dir = _require_app(app)
    esbuild_value, esbuild_source = cfg_with_source('esbuild')
    esbuild = os.path.abspath(esbuild_value) if esbuild_value else ''
    _require_esbuild(esbuild)
    stage_value, stage_source = cfg_with_source('stage_dir')
    renderer_value, renderer_source = cfg_with_source('renderer_dir')
    stage = _pick_stage(app, os.path.abspath(stage_value) if stage_value else '', stage_source)
    configured_renderer = os.path.abspath(renderer_value) if renderer_value else ''
    renderer = (configured_renderer or os.path.join(out_dir, 'renderer')) if dry_run else _pick_renderer(
        out_dir, configured_renderer, renderer_source)
    pack = os.path.abspath(cfg('pack_dir')) if cfg('pack_dir') else ''
    backup = os.path.abspath(cfg('backup_dir')) if cfg('backup_dir') else ''
    if not stage:
        raise InstallError(
            '找不到补丁暂存目录。请设置 MD_STAGE_DIR，或在 config.json 中填写 stage_dir。'
        )
    if not backup:
        raise InstallError(
            '找不到备份目录配置。请设置 MD_BACKUP_DIR，或在 config.json 中填写 backup_dir。'
        )
    paths = {
        'app': app, 'source': renderer, 'stage': stage, 'pack': pack,
        'esbuild': esbuild, 'backup': backup,
    }
    if dry_run:
        _dry_run(paths, {'app': app_source, 'esbuild': esbuild_source,
                         'renderer': renderer_source})
        return

    SRC_RENDERER = renderer
    STAGE = stage
    PACK = pack
    if os.path.normcase(os.path.realpath(SRC_RENDERER)) == os.path.normcase(os.path.realpath(STAGE)):
        raise InstallError(
            'renderer_dir 与 stage_dir 不能是同一目录；请分别设置 MD_RENDERER_DIR 和 '
            'MD_STAGE_DIR，或修改 config.json 中的 renderer_dir / stage_dir。'
        )
    try:
        backup_inside_stage = os.path.commonpath(
            [os.path.realpath(backup), os.path.realpath(STAGE)]
        ) == os.path.realpath(STAGE)
    except ValueError:
        backup_inside_stage = False
    if backup_inside_stage:
        raise InstallError(
            'backup_dir 不能位于 stage_dir 内；请设置 MD_BACKUP_DIR，'
            '或修改 config.json 中的 backup_dir。'
        )

    cast = {}
    for name in CAST:
        sheet = os.path.join(PACK, '%s.sheet.png' % name)
        port = os.path.join(PACK, '%s.portrait.png' % name)
        if not (os.path.exists(sheet) and os.path.exists(port)):
            raise InstallError(
                '缺少角色素材：%s。请设置 MD_PACK_DIR，或在 config.json 中填写 pack_dir；'
                '该目录应包含 %s.sheet.png 与 %s.portrait.png。' % (name, name, name)
            )
        cast[name] = {'sheet': data_url(sheet), 'portrait': data_url(port)}

    backup_path = _backup_stage(STAGE, backup)
    _ROLLBACK = (STAGE, backup_path)
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    shutil.copytree(SRC_RENDERER, STAGE)
    print('官方 renderer -> 副本 OK；角色数 %d' % len(cast))

    main_js = floor_js = None
    for f in os.listdir(os.path.join(STAGE, 'assets')):
        fp = os.path.join(STAGE, 'assets', f)
        if f.startswith('index-') and f.endswith('.js') and os.path.getsize(fp) > 3_000_000:
            main_js = f
        if f.startswith('OfficeFloor-') and f.endswith('.js'):
            floor_js = f
    if not main_js or not floor_js:
        raise InstallError('目标 bundle 未找到：%s\assets' % STAGE)
    print('  main :', main_js)
    print('  floor:', floor_js)

    # A + D
    mp = os.path.join(STAGE, 'assets', main_js)
    m = open(mp, encoding='utf-8').read()
    if '__MD_CAST=' in m:
        raise InstallError('主 bundle 已打过补丁：%s' % mp)
    m = 'window.__MD_CAST=%s;\n' % json.dumps(cast, separators=(',', ':')) + m
    old = 'paintPortrait(ctx, c, scale);'
    if m.count(old) != 1:
        raise InstallError('头像锚点异常 %d' % m.count(old))
    m = m.replace(old,
                  'paintPortrait(ctx, c, scale);'
                  'if(window.__MD_CAST&&window.__MD_CAST[c]){'
                  'const __mdIm=new Image();'
                  '__mdIm.onload=()=>{try{'
                  'ctx.clearRect(0,0,cv.width,cv.height);'
                  'ctx.imageSmoothingEnabled=false;'
                  'ctx.drawImage(__mdIm,0,0,__mdIm.naturalWidth,__mdIm.naturalHeight,0,0,cv.width,cv.height);'
                  '}catch(e){}};'
                  '__mdIm.src=window.__MD_CAST[c].portrait;}', 1)
    open(mp, 'w', encoding='utf-8', newline='\n').write(m)
    print('  主 bundle: 注入 %d 个角色 + 头像覆盖' % len(cast))

    # B + C
    fp = os.path.join(STAGE, 'assets', floor_js)
    t = open(fp, encoding='utf-8').read()
    helper = '''const __mdCache=new Map();
function __mdCustomFrames(name){
  const e=window.__MD_CAST&&window.__MD_CAST[name];
  if(!e||!e.sheet) return Promise.resolve(null);
  if(__mdCache.has(name)) return __mdCache.get(name);
  const p=new Promise((resolve)=>{const img=new Image();
    img.onload=()=>{try{
      const tex=Texture.from(img); tex.source.scaleMode="nearest";
      const rows=[];
      for(let r=0;r<3;r++){const row=[];for(let c=0;c<7;c++){row.push(new Texture({source:tex.source,frame:new Rectangle(c*%d,r*%d,%d,%d)}));}rows.push(row);}
      Object.defineProperty(rows,"__mdCustom",{value:true});
      resolve(rows);
    }catch(err){resolve(null);}};
    img.onerror=()=>resolve(null);
    img.src=e.sheet;});
  __mdCache.set(name,p); return p;
}
''' % (CELL_W, CELL_H, CELL_W, CELL_H)

    anchor = 'async function getCastFrames(name) {'
    if t.count(anchor) != 1:
        raise InstallError('getCastFrames 锚点异常 %d' % t.count(anchor))
    t = t.replace(anchor, helper + anchor + '\n  {const __md=await __mdCustomFrames(name); if(__md) return __md;}', 1)

    anim = 'idle: [0]\n};'
    if t.count(anim) != 1:
        raise InstallError('ANIM_FRAMES 锚点异常 %d' % t.count(anim))
    t = t.replace(anim, 'idle: [0]\n};\nconst MD_ANIM_FRAMES = { walk: [0,1,2,1], type: [3,4,3,4], read: [5,6,5,6], idle: [0] };', 1)

    gf = 'return ANIM_FRAMES[anim].map((col) => this.frames[row][col]);'
    if t.count(gf) != 1:
        raise InstallError('getFrames 锚点异常 %d' % t.count(gf))
    t = t.replace(gf, 'const __map=this.frames.__mdCustom?MD_ANIM_FRAMES:ANIM_FRAMES;\n    return __map[anim].map((col) => this.frames[row][col]);', 1)
    open(fp, 'w', encoding='utf-8', newline='\n').write(t)
    print('  OfficeFloor: 帧表优先 + 动作表')

    # E. 坐姿裁剪随帧高缩放（引擎常量按 32px 帧调的；我们 36×64 要按比例放大，否则腿穿桌子）
    seat_old = 'this.sprite.setSeatedCrop(dir === "down" ? SEAT_LEG_CROP : SEAT_BACK_CROP);'
    seat_new = ('this.sprite.setSeatedCrop((dir === "down" ? SEAT_LEG_CROP : SEAT_BACK_CROP)'
                ' * (this.sprite.frameH ? Math.max(1, this.sprite.frameH / 32) : 1)); /*SEAT_CROP_SCALED*/')
    if t.count(seat_old) != 1:
        raise InstallError('坐姿裁剪锚点异常 %d' % t.count(seat_old))
    t = t.replace(seat_old, seat_new, 1)
    open(fp, 'w', encoding='utf-8', newline='\n').write(t)
    print('  OfficeFloor: 坐姿裁剪按帧高缩放')

    # J. 运行时错误探针：把报错写进窗口标题（无人值守也能验收）
    idx = os.path.join(STAGE, 'index.html')
    if os.path.exists(idx):
        h = open(idx, encoding='utf-8').read()
        if '__mdErrHook' not in h:
            hook = ('<script>/*__mdErrHook*/'
                    "window.addEventListener('error',function(e){document.title='ERR: '+(e.message||'')+' @'"
                    "+((e.filename||'').split('/').pop())+':'+e.lineno;});"
                    "window.addEventListener('unhandledrejection',function(e){var r=e.reason;"
                    "document.title='REJ: '+String((r&&(r.stack||r.message))||r).replace(/\\s+/g,' ').slice(0,220);});"
                    '</script>')
            open(idx, 'w', encoding='utf-8', newline='\n').write(h.replace('</head>', hook + '  </head>', 1))
            print('  已注入运行时错误探针')

    # M. SpritePortrait（底部栏/卡片）也优先用自定义头像
    gj = None
    for f in os.listdir(os.path.join(STAGE, 'assets')):
        if f.startswith('global-') and f.endswith('.js'):
            gj = f
    if gj:
        gp = os.path.join(STAGE, 'assets', gj)
        g = open(gp, encoding='utf-8').read()
        old_p = 'if (!cancelled) paintPortrait(ctx, character, paintScale);'
        if old_p in g:
            new_p = ('if (!cancelled) { paintPortrait(ctx, character, paintScale); /*__mdPortraitPatched*/'
                     'if (window.__MD_CAST && window.__MD_CAST[character]) {'
                     'const __mp = new Image();'
                     '__mp.onload = () => { try {'
                     'ctx.setTransform(1,0,0,1,0,0);'
                     'ctx.clearRect(0,0,canvas.width,canvas.height);'
                     'if (background !== "transparent") { ctx.fillStyle = background; ctx.fillRect(0,0,canvas.width,canvas.height); }'
                     'ctx.imageSmoothingEnabled = false;'
                     'ctx.drawImage(__mp, 0,0, __mp.naturalWidth, __mp.naturalHeight, 0,0, canvas.width, canvas.height);'
                     '} catch (e) {} };'
                     '__mp.src = window.__MD_CAST[character].portrait; } }')
            g = g.replace(old_p, new_p, 1)
            open(gp, 'w', encoding='utf-8', newline='\n').write(g)
            print('  M SpritePortrait 已挂自定义头像')
        else:
            print('  M 未匹配到 SpritePortrait 锚点（跳过）')

    # O. 气泡高度适配 96px 角色（原 -38 是按 32px 帧调的，会压在脸上）
    if 'OFFSET_Y = -38' in t:
        t = t.replace('OFFSET_Y = -38', 'OFFSET_Y = -102 /*__mdBubbleFixed*/', 1)
        open(fp, 'w', encoding='utf-8', newline='\n').write(t)
        print('  O 气泡上移到 -102')
    else:
        print('  O 未匹配到 OFFSET_Y = -38（跳过）')

    # 自检
    m2 = open(mp, encoding='utf-8').read()
    t2 = open(fp, encoding='utf-8').read()
    checks = [
        ('注入角色数=%d' % len(cast), m2.count('"sheet":"data:image/png;base64,') == len(cast)),
        ('错误探针', '__mdErrHook' in open(os.path.join(STAGE, 'index.html'), encoding='utf-8').read()),
        ('godCommand 仍在', 'godCommand' in m2),
        ('气泡高度', '__mdBubbleFixed' in t2),
        ('底部头像补丁', any(__import__('os').path.exists(os.path.join(STAGE,'assets',f)) and '__mdPortraitPatched' in open(os.path.join(STAGE,'assets',f),encoding='utf-8').read() for f in __import__('os').listdir(os.path.join(STAGE,'assets')) if f.startswith('global-') and f.endswith('.js'))),
        ('头像覆盖', '__mdIm' in m2),
        ('floor 自定义取帧', '__mdCustomFrames' in t2),
        ('floor 动作表', 'MD_ANIM_FRAMES' in t2),
        ('floor getFrames 分支', 'this.frames.__mdCustom?MD_ANIM_FRAMES' in t2),
        ('坐姿裁剪缩放', 'SEAT_CROP_SCALED' in t2),
        ('格 %dx%d' % (CELL_W, CELL_H), 'c*%d,r*%d,%d,%d' % (CELL_W, CELL_H, CELL_W, CELL_H) in t2),
    ]
    for label, ok in checks:
        print('  %-20s %s' % (label, 'OK' if ok else 'FAIL'))
    if not all(ok for _, ok in checks):
        raise InstallError('自检失败')
    # U2 must survive cast/map regeneration from the official renderer.
    from patch_u2_terminal_restore import patch as patch_u2
    patch_u2(STAGE)
    from patch_quota_renderer import patch as patch_quota
    patch_quota(STAGE)
    from patch_native_events_renderer import patch as patch_native_events
    patch_native_events(STAGE)
    gate_paths = [mp, fp]
    if gj:
        gate_paths.append(os.path.join(STAGE, 'assets', gj))
    _syntax_gate(esbuild, gate_paths)
    _ROLLBACK = None
    print('补丁副本就绪:', STAGE)


def main():
    parser = argparse.ArgumentParser(description='生成可安装的 StarHive renderer 补丁副本')
    parser.add_argument('--dry-run', action='store_true',
                        help='只校验 app 与 esbuild，并打印将修改的文件；不写任何文件')
    args = parser.parse_args()
    try:
        install(dry_run=args.dry_run)
        return 0
    except (InstallError, OSError, RuntimeError, ValueError, ImportError) as exc:
        if _ROLLBACK:
            stage, backup_path = _ROLLBACK
            try:
                _rollback_stage(stage, backup_path)
            except OSError as rollback_exc:
                print('错误：%s' % exc, file=sys.stderr)
                print('回滚也失败：%s' % rollback_exc, file=sys.stderr)
                return 3
        print('错误：%s' % exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
