"""Render the installer's original geometric monogram (not the supplied logo)."""
from pathlib import Path
from PIL import Image, ImageDraw


def build(output):
    image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, 496, 496), radius=112, fill='#401614', outline='#e6b29b', width=14)
    draw.polygon([(256, 48), (465, 256), (256, 465), (48, 256)], fill='#a73c2d')
    for x in (170, 284):
        draw.rounded_rectangle((x, 132, x + 58, 380), radius=10, fill='#fff1e9')
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, sizes=[(x, x) for x in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == '__main__':
    build(Path(__file__).resolve().parents[1] / 'src/installer/windows/runner/resources/app_icon.ico')
