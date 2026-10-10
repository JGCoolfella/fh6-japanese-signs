"""Build labelled contact sheets of colour textures from extracted .pb files."""
import sys, glob, os, re
sys.path.insert(0, os.path.dirname(__file__))
import swatch
from PIL import Image, ImageDraw

def build(pattern, out_prefix, include=r"bclr|diff|basecol|maskrgba|decal", cols=5, per_page=30, thumb=300):
    best = {}
    for f in glob.glob(pattern, recursive=True):
        base = os.path.basename(f)
        if not re.search(include, base, re.I) or re.search(r"nrml|extra|xwinterx", base, re.I):
            continue
        d = open(f, "rb").read()
        if d[:4] != b"burG":
            continue
        try:
            img, info = swatch.to_image(d)
        except Exception:
            continue
        key = re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{27}.*", "", base)
        if key not in best or info["width"] * info["height"] > best[key][1]["width"] * best[key][1]["height"]:
            best[key] = (img, info, f)
    items = sorted(best.items())
    pages = []
    for p in range(0, len(items), per_page):
        chunk = items[p:p + per_page]
        rows = (len(chunk) + cols - 1) // cols
        cw, ch = thumb + 10, thumb + 40
        sheet = Image.new("RGB", (cols * cw, rows * ch), (40, 40, 40))
        dr = ImageDraw.Draw(sheet)
        for k, (key, (img, info, f)) in enumerate(chunk):
            x, y = (k % cols) * cw, (k // cols) * ch
            t = img.convert("RGB"); t.thumbnail((thumb, thumb))
            sheet.paste(t, (x + 5, y + 5))
            dr.text((x + 5, y + thumb + 8), f"#{p + k} {key[:44]}", fill=(255, 255, 255))
            dr.text((x + 5, y + thumb + 22), f"{key[44:88]} {info['width']}x{info['height']}", fill=(170, 170, 170))
        path = f"{out_prefix}_{p // per_page + 1}.png"
        sheet.save(path); pages.append(path)
    with open(f"{out_prefix}_index.txt", "w") as fh:
        for k, (key, (img, info, f)) in enumerate(items):
            fh.write(f"#{k}\t{key}\t{info['width']}x{info['height']}\t{swatch.FORMATS[info['format']][0]}\t{f}\n")
    return pages, len(items)

if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2]))
