#!/usr/bin/env python3
"""把 index.html 和 assets/ 里的图片打包成一个可以单独分发的 HTML。

用法：python3 build.py            → 生成 dist/花信小筑.html
源文件 index.html 不会被改动；改完游戏后重新运行一次即可。
"""
import base64, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'index.html'
OUT = ROOT / 'dist' / '花信小筑.html'
MAIN = "<script>\n(()=>{'use strict';"
PATH = re.compile(r'assets/[\w./-]+?\.webp')

# 运行时垫片：脚本里拼出来的 assets/… 路径（innerHTML、图片预加载等）换成内嵌图片的 blob 地址
SHIM = r"""(()=>{const A=window.__ASSETS,U={},re=/assets\/[\w.\/-]+?\.webp/g;
for(const k in A){const s=atob(A[k]),b=new Uint8Array(s.length);for(let i=0;i<s.length;i++)b[i]=s.charCodeAt(i);U[k]=URL.createObjectURL(new Blob([b],{type:'image/webp'}))}
delete window.__ASSETS;
const fix=v=>typeof v==='string'&&v.includes('assets/')?v.replace(re,m=>U[m]||m):v;
const wrap=(proto,prop)=>{const d=Object.getOwnPropertyDescriptor(proto,prop);Object.defineProperty(proto,prop,{...d,set(v){d.set.call(this,fix(v))}})};
wrap(Element.prototype,'innerHTML');wrap(Element.prototype,'outerHTML');wrap(HTMLImageElement.prototype,'src');
const iah=Element.prototype.insertAdjacentHTML;Element.prototype.insertAdjacentHTML=function(p,h){return iah.call(this,p,fix(h))};
const sa=Element.prototype.setAttribute;Element.prototype.setAttribute=function(n,v){return sa.call(this,n,fix(v))};
})();"""


def main():
    html = SRC.read_text(encoding='utf8')
    cut = html.rindex(MAIN)
    head, script = html[:cut], html[cut:]

    data = {}
    for f in sorted((ROOT / 'assets').rglob('*.webp')):
        data[f.relative_to(ROOT).as_posix()] = base64.b64encode(f.read_bytes()).decode()

    missing = set()

    def inline(m):
        k = m.group(0)
        if k not in data:
            missing.add(k)
            return k
        return 'data:image/webp;base64,' + data[k]

    # 样式和静态标记里的路径直接换成 data URI，这样首屏不依赖脚本
    head = PATH.sub(inline, head)
    if missing:
        sys.exit('找不到这些图片：' + ', '.join(sorted(missing)))

    boot = '<script>window.__ASSETS=' + json.dumps(data, separators=(',', ':')) + ';\n' + SHIM + '</script>\n'
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(head + boot + script, encoding='utf8')
    print(f'{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1e6:.1f} MB，内嵌图片 {len(data)} 张')


if __name__ == '__main__':
    main()
