"""Which brand swaps are switched on.

catalogue/choices/enabled_brands.json  {"brands": [...]}  brands that are built; every other swap is
  skipped and the game's original sign shows. Add a brand back to switch it on again.
catalogue/choices/disabled_swaps.json  record of every swap that was switched off (catalogue ID -> what it was)

All the jobs stay in the job files; this only decides what gets built.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "catalogue", "choices", "enabled_brands.json")
DEFAULT = {"brands": ["Lawson", "FamilyMart", "UNIQLO"]}

# logo file prefix -> brand (assets/ and assets/custom/)
BRANDS = [("lawson", "Lawson"), ("familymart", "FamilyMart"), ("japanpost", "Japan Post"), ("jp_postal", "Japan Post"),
          ("maruetsu", "Maruetsu"), ("matsukiyo", "Matsumoto Kiyoshi"), ("welcia", "Welcia"), ("smbc", "SMBC"),
          ("eneos", "ENEOS"), ("autobacs", "Autobacs"), ("starbucks", "Starbucks"), ("uniqlo", "UNIQLO"),
          ("docomo", "docomo"), ("nakau", "Nakau"), ("ichiran", "Ichiran"), ("ohsho", "Gyoza no Ohsho"),
          ("tokyofm", "TOKYO FM"), ("hks", "HKS"), ("motul", "Motul"), ("tomica", "Tomica"), ("taito", "Taito Station"),
          ("rays", "RAYS"), ("spoon", "Spoon"), ("mitsuya", "Mitsuya Cider"), ("cclemon", "C.C. Lemon"),
          ("softbank", "SoftBank"), ("beams", "BEAMS"), ("seiyu", "Seiyu"), ("yellowhat", "Yellow Hat"),
          ("boss", "BOSS"), ("kirin", "Kirin"), ("bigecho", "Big Echo"), ("7eleven", "7-Eleven")]


def brand_of(logo_file):
    if not logo_file:
        return None
    f = os.path.basename(logo_file)
    for key, name in BRANDS:
        if f.startswith(key):
            return name
    return None


def config():
    if os.path.exists(CFG):
        c = json.load(open(CFG, encoding="utf-8"))
        return {"brands": c.get("brands", [])}
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    json.dump(DEFAULT, open(CFG, "w", encoding="utf-8"), indent=1)
    return dict(DEFAULT)


ENABLED = set(config()["brands"])


def on(brand):
    return brand is None or brand in ENABLED


def filter_ops(ops, group_brand=None):
    """Drop ops of switched-off brands. A logo op's brand comes from its file; fill/bands/remap ops drawn in
    the same box as a switched-off logo go with it. Ops may carry an explicit "brand"; group_brand covers a
    whole job group whose ops carry no logo of their own."""
    if group_brand is not None:
        return list(ops) if on(group_brand) else []
    off_boxes = [tuple(o["box"]) for o in ops if o["op"] == "logo" and not on(o.get("brand") or brand_of(o["file"]))]
    has_logo = any(o["op"] == "logo" for o in ops)
    if has_logo and not any(o["op"] == "logo" and on(o.get("brand") or brand_of(o["file"])) for o in ops):
        # every logo in this job is switched off: the whole job goes (incl. stripes elsewhere on the texture)
        return [o for o in ops if o["op"] == "restore" or ("brand" in o and on(o["brand"]))]

    def inside(b, c):
        return b[0] >= c[0] - 2 and b[1] >= c[1] - 2 and b[2] <= c[2] + 2 and b[3] <= c[3] + 2

    out = []
    for o in ops:
        if o["op"] == "restore":
            out.append(o)
        elif "brand" in o:
            if on(o["brand"]):
                out.append(o)
        elif o["op"] == "logo":
            if on(brand_of(o["file"])):
                out.append(o)
        elif not has_logo:
            continue  # recolour-only op of unknown brand: off unless the group says otherwise
        elif not any(inside(tuple(o["box"]), c) or inside(c, tuple(o["box"])) for c in off_boxes):
            out.append(o)
    return out


def design_on(design):
    return on(brand_of(design.get("logo")))
