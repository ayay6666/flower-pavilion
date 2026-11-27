"""生成 GitHub Pages 静态站点到 dist/pages，图片编码依赖 cwebp。"""
import base64
import hashlib
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'dist' / 'pages'

# 宽度按实际显示尺寸保留高像素密度余量。小镇地图可平移，保留原图分辨率。
IMAGE_WIDTHS = {
    'cottage': 360, 'bough': 720, 'corner': 420, 'splash': 800,
    'ic_coin': 80, 'di_book': 96, 'ic_dew': 96, 'ic_bfly': 96, 'ic_can': 96,
    'mountains': None, 'meadow': None, 'town_x': None, 'town_px': None,
}


def build():
    if not shutil.which('cwebp'):
        raise SystemExit('请先安装 WebP 命令行工具 cwebp')
    assets = SITE / 'assets'
    shutil.copytree(ROOT / 'assets', assets, dirs_exist_ok=True)
    for name, width in IMAGE_WIDTHS.items():
        source = ROOT / 'assets' / f'{name}.webp'
        target = assets / source.name
        resize = ['-resize', str(width), '0'] if width else []
        subprocess.run(['cwebp', '-quiet', '-m', '6', '-q', '78', *resize,
                        str(source), '-o', str(target)], check=True)
        if target.stat().st_size >= source.stat().st_size:
            shutil.copyfile(source, target)

    # 让浏览器先解析页面和发现首屏图片，书法字体可按需请求并独立缓存。
    def external_font(match):
        data = base64.b64decode(match[1], validate=True)
        filename = 'title-' + hashlib.sha256(data).hexdigest()[:12] + '.woff2'
        (assets / filename).write_bytes(data)
        return f'url(assets/{filename})'

    html = (ROOT / 'index.html').read_text(encoding='utf8')
    html = re.sub(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', external_font, html)
    (SITE / 'index.html').write_text(html, encoding='utf8')
    (SITE / '.nojekyll').touch()


if __name__ == '__main__':
    build()
