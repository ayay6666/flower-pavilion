#!/usr/bin/env python3
"""把 index.html 和 assets/ 里的图片打包成一个可以单独分发的 HTML。

用法：
  python3 build.py                → 生成 dist/花信小筑.html（单文件离线版）
  python3 build.py --subset-font  → 按当前展示文案重新提取并更新 index.html 内嵌书法字体子集
"""
import base64, json, pathlib, re, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'index.html'
OUT = ROOT / 'dist' / '花信小筑.html'
MAIN = "<script>\n(()=>{'use strict';"
PATH = re.compile(r'assets/[\w./-]+?\.webp')
CSS_URL = re.compile(r"""url\((['"]?)(assets/[\w./-]+?\.webp)\1\)""")

# 惰性图片垫片：首屏零同步解码、不劫持 DOM 原型；首次请求某张图时才生成 Blob URL 并释放 Base64，同时保留 Blob 供画片离线导出
SHIM = r"""(()=>{const A=window.__ASSETS,U={},B={};delete window.__ASSETS;window.__B=B;
window.__A=p=>{if(U[p])return U[p];if(p==='assets/mountains.webp'){const m=document.getElementById('mtn');if(m&&m.src)return U[p]=m.src}
const s=A[p];if(!s)return p;delete A[p];
const bin=atob(s),u8=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u8[i]=bin.charCodeAt(i);
const blob=new Blob([u8],{type:'image/webp'}),url=URL.createObjectURL(blob);B[url]=blob;return U[p]=url};
})();"""

POETIC_EXTRA = (
    '一二三四五六七八九十百千万上下左右中大小春秋冬夏朝暮晨晚昼夜晴雨雪风霜露云雾烟霞星月日'
    '山川水溪泉池海湖林木森松竹梅兰菊莲荷桃杏梨柳桂枫茶琴棋书画诗酒歌笛箫香影梦魂心意情思念恋'
    '欢喜乐安宁静闲幽雅清素淡浓深浅远近高低长短新旧故古今芳华锦绣翠碧青白红紫黄蓝墨玉金银珠'
    '轩斋阁亭台楼院窗门帘阶径桥舟帆鹤燕蝶鱼鸟蝉萤折枝拾翠暗疏斜浮生若如笑醉倚听看望寻归客岁寒'
    '知音良辰美景清风明月流水高山松间石上花下竹里半日浮云人间四时序曲'
)


def collect_display_chars(html: str, include_poetic: bool = True) -> str:
    cut = html.index('</head>')
    src_text = html[cut:]
    parts = []
    for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', src_text):
        parts.append(re.sub(r'\$\{[^}]*\}|<[^>]+>', '', m.group(1)))
    for m in re.finditer(r"\b[a-z]+:\{n:'([^']+)'[^\n]*?lang:'([^']+)'", src_text):
        parts.extend([m.group(1), m.group(2)])
    parts += re.findall(r"(?<=')([黄红紫白粉蓝橙绿青墨])(?=')", src_text)
    parts += re.findall(r"\[\d+,\d+,'([^']+)'", src_text)
    for blk_pat in [r"const VTYPE=\{.*?\};", r"const VASES=\{.*?\n\};"]:
        m = re.search(blk_pat, src_text, re.S)
        if m:
            parts += re.findall(r"\bn:'([^']+)'", m.group(0))
    parts += re.findall(r"who:'([^']+)'", src_text)
    for m in re.finditer(r"\{id:'\w+',n:'([^']+)',role:'[^']+',ch:'([^']+)'", src_text):
        parts.extend([m.group(1), m.group(2)])
    m_bdg = re.search(r"const BADGE=\[(.*?)\];\n", src_text)
    if m_bdg:
        parts += re.findall(r"\['b\d+','([^']+)'", m_bdg.group(1))
    # 山野探险：地图名、地段名、乡邻名、拾遗名、小游戏标题都用书法字
    for blk in [r"const WMAPS=\{.*?\}\};", r"const WQ=\{.*?\}\]\}\};"]:
        m = re.search(blk, src_text, re.S)
        if m:
            parts += re.findall(r"\bn:'([^']+)'", m.group(0))
            parts += re.findall(r"\[[\d.]+,'([^']+)'\]", m.group(0))
    m = re.search(r"const WCU=\{.*?\};", src_text, re.S)
    if m:
        parts += re.findall(r"\w+:\['([^']+)'", m.group(0))
    parts += re.findall(r"wxGameOpen\([^,]+,'([^']+)'", src_text)
    parts += ['个漂咕咚山野拾遗花丛荷塘溪边草丛寻信花信归来旅人邮差书斋']
    # 弹窗朱印：标题上方的小字会收进印里
    parts += re.findall(r"letter-spacing:\.3em[^>]*>([^<$]+)<", src_text)
    for pat in [
        r"const GRADES=\[\[.*?\]\];",
        r"const NAMES=\{.*?\};",
        r"const dockPlaces=\[.*?\];",
        r"function stretchName\(k\)\{.*?\}",
        r"pick\(\['初心'[^\)]+\]\)",
    ]:
        m = re.search(pat, src_text, re.S)
        if m:
            parts.append(''.join(ch for ch in m.group(0) if ord(ch) > 127))
    parts.append('花信小筑小院花铺花艺山野小镇花材调整时令当令需用上品珍藏神品妙品能品佳作连种连采连浇照料未知的花未见的花色无题无名窑禾知花✓…×·！？，。：（）Lv.0123456789 ')
    if include_poetic:
        parts.append(POETIC_EXTRA)
    return ''.join(sorted(set(''.join(parts)) - {'\n', '\r', '\t'}))


def embedded_font_cps(html: str) -> set[str]:
    cps = set()
    for line in html.splitlines():
        if line.startswith("@font-face{font-family:'Ma Shan Zheng'"):
            for ur in re.findall(r'unicode-range:([^;}]+)', line):
                for a, b in re.findall(r'U\+([0-9a-fA-F]+)(?:-([0-9a-fA-F]+))?', ur):
                    a_i = int(a, 16)
                    b_i = int(b, 16) if b else a_i
                    for cp in range(a_i, b_i + 1):
                        cps.add(chr(cp))
    return cps


def subset_font():
    html = SRC.read_text(encoding='utf8')
    chars = collect_display_chars(html, include_poetic=True)
    mid = (len(chars) + 1) // 2
    rules = []
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    for ch in (chars[:mid], chars[mid:]):
        url = 'https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&text=' + urllib.parse.quote(ch)
        css = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': ua}), timeout=20).read().decode('utf8')
        m_url = re.search(r'src:\s*url\((https://[^)]+)\)', css)
        m_ur = re.search(r'unicode-range:\s*([^;]+);', css)
        woff2 = urllib.request.urlopen(m_url.group(1), timeout=20).read()
        b64 = base64.b64encode(woff2).decode('ascii')
        rules.append(
            f"@font-face{{font-family:'Ma Shan Zheng';font-style:normal;font-weight:400;font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{m_ur.group(1).replace(' ', '')}}}"
        )
    lines = html.splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("@font-face{font-family:'Ma Shan Zheng'")]
    if not idx:
        sys.exit('未找到内嵌 Ma Shan Zheng @font-face 行')
    new_lines = lines[:idx[0]] + rules + lines[idx[-1] + 1:]
    SRC.write_text('\n'.join(new_lines) + '\n', encoding='utf8')
    print(f'已更新内嵌书法字体子集：{len(chars)} 字，共 {sum(len(r) for r in rules) / 1024:.1f} KB')


def build():
    html = SRC.read_text(encoding='utf8')

    # 检查展示文案是否有生字未纳入内嵌书法字体
    covered = embedded_font_cps(html)
    needed_cjk = [c for c in collect_display_chars(html, include_poetic=False) if '\u4e00' <= c <= '\u9fff' and c not in covered]
    if needed_cjk:
        print('提示：以下展示汉字尚未包含在内嵌书法字体中（可运行 python3 build.py --subset-font 更新）：' + ''.join(needed_cjk))

    cut = html.rindex(MAIN)
    head, script = html[:cut], html[cut:]

    data = {}
    for f in sorted((ROOT / 'assets').rglob('*.webp')):
        data[f.relative_to(ROOT).as_posix()] = base64.b64encode(f.read_bytes()).decode()

    missing = set()
    head_inlined = set()

    # 1. CSS 中重复引用的背景/边框图提取为 :root CSS 变量，避免同一张图在样式表中重复内嵌多次
    css_counts = {}
    for m in CSS_URL.finditer(head):
        css_counts[m.group(2)] = css_counts.get(m.group(2), 0) + 1
    css_vars = {}
    var_defs = []
    for k, cnt in sorted(css_counts.items()):
        if k not in data:
            missing.add(k)
            continue
        if cnt > 1:
            vn = f'--u{len(css_vars)}'
            css_vars[k] = vn
            var_defs.append(f'{vn}:url(data:image/webp;base64,{data[k]})')
            head_inlined.add(k)

    def repl_css(m):
        k = m.group(2)
        if k in css_vars:
            return f'var({css_vars[k]})'
        if k not in data:
            missing.add(k)
            return m.group(0)
        head_inlined.add(k)
        return f'url(data:image/webp;base64,{data[k]})'

    head = CSS_URL.sub(repl_css, head)
    if var_defs:
        head = head.replace('</style>\n</head>', ':root{' + ';'.join(var_defs) + '}\n</style>\n</head>', 1)

    # 2. 静态 HTML <img> 里的路径换成 data URI；左右前景角花（#fgl / #fgr）共用同一份数据避免重复 235 KB
    seen_corner = False

    def repl_html(m):
        nonlocal seen_corner
        k = m.group(0)
        if k not in data:
            missing.add(k)
            return k
        head_inlined.add(k)
        if k == 'assets/corner.webp':
            if not seen_corner:
                seen_corner = True
            else:
                return '__FGR_CORNER__'
        return 'data:image/webp;base64,' + data[k]

    head = PATH.sub(repl_html, head)
    if '__FGR_CORNER__' in head:
        head = head.replace(
            'src="__FGR_CORNER__"',
            'src="data:image/gif;base64,R0lGODlhAQABAAAAACw="',
            1,
        ).replace(
            '<canvas id="fx"></canvas>',
            "<script>document.getElementById('fgr').src=document.getElementById('fgl').src</script><canvas id=\"fx\"></canvas>",
            1,
        )

    if missing:
        sys.exit('找不到这些图片：' + ', '.join(sorted(missing)))

    # 3. 仅将脚本动态用到的图片打入 window.__ASSETS，消除与首屏静态资源的双重内嵌
    script_literals = set(PATH.findall(script)) - {'assets/mountains.webp'}
    js_data = {k: v for k, v in data.items() if k not in head_inlined or k in script_literals}

    boot = '<script>window.__ASSETS=' + json.dumps(js_data, separators=(',', ':')) + ';\n' + SHIM + '</script>\n'
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(head + boot + script, encoding='utf8')
    print(f'{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1e6:.2f} MB（首屏内嵌 {len(head_inlined)} 张，按需懒加载 {len(js_data)} 张，共 {len(data)} 张）')


if __name__ == '__main__':
    if '--subset-font' in sys.argv[1:]:
        subset_font()
    else:
        build()
