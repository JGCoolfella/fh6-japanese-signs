"""The user's own per-sign choices from the catalogue (catalogue/choices/choices.csv, 2026-10-10).
Custom artwork lives in assets/custom/ (built by make_custom_assets.py; *_t = trimmed to content).
These run after the standard jobs and override them for the same sign.
"""
import json
import os

_BG = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "custom", "bg.json")))


def art(box, name, fill=0.9):
    """Plain texture: fill the sign with the artwork's own background and fit the artwork inside."""
    return [{"op": "logo", "box": box, "file": f"custom/{name}_t.png", "bg": tuple(_BG[name]), "fill": fill}]


def restore(box):
    return [{"op": "restore", "box": box}]


FM_G, FM_B = (2, 171, 82), (20, 170, 226)       # colours of the user's FamilyMart logo
AB4, AB8, VT4, VP4, VP6 = ("sgn_gbl_shop_aboard_01_a4_bclr", "sgn_gbl_shop_aboard_01_a8_bclr", "sgn_gbl_shop_vertical_02_a4_bclr",
                           "sgn_gbl_shops_vinyl_poster_01_a4_bclr", "sgn_gbl_shops_vinyl_poster_01_a6_bclr")
SHIB, F4 = "bld_cty_poi_shibuya_02_a_signage_xsummerx_bclr", "tex_gbl_fittings_com_04_a_bclr"

# ---------------------------------------------------------------- plain textures (P)
PLAIN = [
    # P001 CHROMA A-board: katakana logo only. In game this A-board squashes its texture ~2.4x vertically
    # (measured from the ID-label ring in the user's screenshot), so the logo is pre-stretched 2.4x tall.
    (AB4, [{"op": "logo", "box": (0, 0, 341, 1024), "file": "uniqlo_logo.png", "bg": (250, 250, 250), "fill": 0.9,
            "squash": 2.4}]),
    (VT4, art((0, 0, 170, 1024), "uniqlo_stack", 0.92)),            # P022 CHROMA (red)
    (VT4, art((170, 0, 341, 1024), "uniqlo_stack", 0.92)),          # P023 CHROMA (white)
    (VP4, art((0, 0, 256, 512), "uniqlo_stack", 0.92)),             # P038 CHROMA (red)
    (VP4, art((256, 0, 512, 512), "uniqlo_stack", 0.92)),           # P039 CHROMA (white)
    (SHIB, art((0, 0, 122, 282), "uniqlo_stack", 0.92)),            # P211 CHROMA (red, stacked)
    (SHIB, art((122, 0, 246, 282), "uniqlo_stack", 0.92)),          # P212 CHROMA (white, stacked)
    (SHIB, art((368, 0, 440, 512), "uniqlo_stack", 0.92)),          # P215 CHROMA (red, vertical)
    (SHIB, [{"op": "logo", "box": (440, 0, 512, 512), "file": "custom/uniqlo_pair_v.png", "bg": (254, 254, 254),
             "fill": 0.98}]),                                       # P216 CHROMA (white, vertical): user's pair, turned 270
    (SHIB, art((0, 282, 368, 512), "uniqlo_pair_wide", 0.92)),      # P214 [CHROMA] (red, wide)
    (AB8, art((683, 0, 1024, 512), "lawson_station", 0.94)),        # P021 365 Konbini (vertical)
    (VP6, art((0, 0, 256, 512), "lawson_station", 0.94)),           # P046 365 Konbini
    ("sgn_gbl_board_grassroute_01_efgh_bclr", art((0, 512, 512, 768), "taito_wide", 0.92)),  # P129 GAME
    (F4, art((0, 205, 205, 410), "taito_game", 0.92)),              # P167 GAME
    (F4, art((819, 614, 1024, 819), "uniqlo_square", 0.96)),        # P175 CHROMA
    # P197 FamilyMart blade sign: user's logo turned to read downwards, full height (art matches the box aspect)
    ("bld_cty_hrise_m_shop_01_a_feature_a_bclr",
     [{"op": "logo", "box": (683, 17, 876, 671), "file": "custom/familymart_blade.png", "bg": (255, 255, 255), "fill": 1.0}]),
    # P198 / P199 fascia panels: same bands as the blade (green 22% / white / blue 7%, logo colours)
    ("bld_cty_hrise_m_shop_01_a_feature_a_bclr",
     [{"op": "bands", "box": (686, 711, 1007, 905), "bg": (255, 255, 255), "bands": [(0.0, 0.22, FM_G), (0.93, 1.0, FM_B)],
       "brand": "FamilyMart"},
      {"op": "bands", "box": (114, 836, 313, 990), "bg": (255, 255, 255), "bands": [(0.0, 0.07, FM_B), (0.78, 1.0, FM_G)],
       "vertical": True, "brand": "FamilyMart"}]),
    # keep original
    ("sgn_gbl_shop_vertical_02_a6_bclr", restore((341, 0, 512, 1024))),             # P031 Tatsu
    ("sgn_cty_shops_vinyl_6m_01_a3_bclr", restore((0, 0, 1024, 128))),              # P061 Gacha City Radio
    ("tex_cty_decal_akih_billbrd_atlas_01_c_bclr", restore((1365, 0, 2048, 1024))), # P079 Vaneso Gold
    ("sgn_cty_billboard_sqre_x2_01_a_bclr", restore((0, 1024, 1024, 2048))),        # P142 Gacha City Radio
    ("tex_gbl_sgn_com_billboard_v_01_a_bclr", restore((0, 0, 341, 2048))),          # P157 Kakimoto Takashi
]

# ---------------------------------------------------------------- tinted signs (T): cell jobs
WH = (252, 252, 252)
TAITO = {"colours": {"red": (252, 4, 4), "white": WH}, "bg": "red", "logo": "custom/taito_game_t.png",
         "logo_box": (0.06, 0.06, 0.94, 0.94)}
UQ_PAIR = {"colours": {"white": WH, "red": (236, 28, 36)}, "bg": "white", "logo": "custom/uniqlo_pair_t.png",
           "logo_box": (0.04, 0.08, 0.96, 0.92)}
LAWSON_ST = {"colours": {"white": WH, "blue": (4, 108, 188)}, "bg": "white", "logo": "custom/lawson_station_t.png",
             "logo_box": (0.04, 0.04, 0.96, 0.96)}
SB_WORD = {"colours": {"white": WH, "green": (0, 96, 64)}, "bg": "white", "logo": "custom/starbucks_word_t.png",
           "logo_box": (0.04, 0.15, 0.96, 0.85)}
SOFTBANK = {"colours": {"white": WH, "grey": (80, 80, 80), "yellow": (248, 188, 8)}, "bg": "white",
            "logo": "custom/softbank_t.png", "logo_box": (0.06, 0.2, 0.94, 0.8)}

LAWSON_WORD = {"colours": {"white": WH, "blue": (0, 88, 207), "pink": (247, 48, 103)}, "bg": "white",
               "bands": [(0.80, 0.90, "pink")], "logo": "custom/lawson_word_t.png", "logo_colour": "blue",
               "logo_box": (0.01, 0.05, 0.99, 0.75)}

# T125: the user's improved strip, bands extended to the strip's full length (assets/custom/lawson_t125_wide.png)
LAWSON_T125 = {"colours": {"white": WH, "blue": (0, 88, 207), "pink": (232, 160, 186)}, "bg": "white",
               "logo": "custom/lawson_t125_wide.png", "logo_box": (0.0, 14 / 102, 1.0, 86 / 102)}   # art rows 14-86 of the cell
# T079 (main city fascia): whole cell drawn, lettering + pink line inside the visible strip (rows 25-140 of 170)
LAWSON_WORD_HR = {"colours": {"white": WH, "blue": (0, 88, 207), "pink": (247, 48, 103)}, "bg": "white",
                  "bands": [(0.688, 0.755, "pink")], "logo": "custom/lawson_word_t.png", "logo_colour": "blue",
                  "logo_box": (0.01, 0.181, 0.99, 0.654)}
# T073: FamilyMart fascia - green band, lettering at full height, blue band; laid over the whole cell so
# whatever part the sign shows (art in the original sits in rows ~0-130 of 170) is covered
FM_STRIP = {"colours": {"white": WH, "green": (2, 171, 82), "blue": (20, 170, 226)}, "bg": "white",
            "bands": [(0.0, 0.26, "green"), (0.73, 0.82, "blue")], "logo": "custom/familymart_word_t.png",
            "logo_colour": "blue", "logo_box": (0.02, 0.30, 0.98, 0.69)}

UQ_SQUARE = {"colours": {"white": WH, "red": (237, 28, 36)}, "bg": "white", "logo": "uniqlo_logo.png",
             "logo_box": (0.06, 0.06, 0.94, 0.94)}

CELLS = [
    # found in the catalogue's section X sweep (single-channel ink masks)
    {"mask": "sgn_gbl_shop_square_01_a4_mask", "cell": (1, 1), "design": UQ_SQUARE},            # CHROMA [ ] square sign
    {"mask": "sgn_cty_shop_square_01_a1_mask", "cell": (2, 2), "design": TAITO},                # GAME + pixel car square sign
    {"mask": "tex_gbl_sgn_com_billboard_03_a_pack_maskrgba", "cell": (1, 1), "design": TAITO},  # T198 GAME / Level Up Station billboard
    {"mask": "sgn_gbl_shops_vinyl_6m_01_a5_pack_maskrgba", "cell": (1, 1), "design": LAWSON_T125},                                                                            # T125 (user's improved strip)
    {"mask": "sgn_gbl_shop_hrzntl_6m_01_a5_pack_maskrgba", "cell": (1, 1), "design": FM_STRIP},           # T073
    {"mask": "sgn_gbl_shop_hrzntl_6m_01_a7_pack_maskrgba", "cell": (1, 1), "design": LAWSON_WORD_HR},                                                                            # T079 main city fascia
    {"mask": "sgn_cty_shops_vinyl_poster_01_a1_mask", "cell": (4, 1), "design": TAITO},                   # T062
    {"mask": "sgn_gbl_shop_hrzntl_6m_01_a4_mask", "cell": (1, 2), "design": UQ_PAIR},                     # T071
    {"mask": "sgn_gbl_shop_square_01_a6_pack_maskrgba", "cell": (1, 1), "design": LAWSON_ST},             # T089
    {"mask": "sgn_gbl_shop_vinyl_3m_01_a4_mask", "cell": (1, 2), "design": UQ_PAIR},                      # T102
    {"mask": "sgn_gbl_shops_vinyl_6m_01_a3_mask", "cell": (1, 2), "design": UQ_PAIR},                     # T117
    {"mask": "tex_gbl_sgn_com_billboard_04_a_atlas1_pack_maskrgba", "cell": (1, 1), "design": TAITO},     # T172
    {"mask": "tex_gbl_sgn_com_billboard_05_a_atlas2_pack_maskrgba", "cell": (2, 1), "design": TAITO},     # T182
    {"mask": "tex_gbl_sgn_com_billboard_06_a_pack_maskrgba", "cell": (1, 1), "design": SOFTBANK},         # T184
]
# keep original: no job at all for these cells
KEEP_CELLS = {
    ("sgn_gbl_shops_vinyl_6m_01_a5_pack_maskrgba", (1, 5)),                 # T129 Medi Pharmacy
    ("tex_gbl_sgn_com_billboard_04_a_atlas2_pack_maskrgba", (1, 1)),        # T176 PRAV
    ("tex_gbl_sgn_com_billboard_05_a_atlas1_pack_maskrgba", (1, 1)),        # T178 Tatsu
    ("tex_gbl_sgn_com_billboard_05_a_atlas1_pack_maskrgba", (2, 1)),        # T179 Medi Pharmacy
    ("tex_gbl_sgn_com_billboard_05_a_atlas1_pack_maskrgba", (3, 1)),        # T180 Moriya
    ("tex_gbl_sgn_com_billboard_06_a_pack_maskrgba", (1, 2)),               # T185 Medi Pharmacy
    ("tex_gbl_sgn_com_billboard_06_a_pack_maskrgba", (1, 3)),               # T186 Gacha City Radio
}

# ---------------------------------------------------------------- POI stickers (S): key = atlas letter, row, col
# upright artwork placed as is (the original stickers in these cells read normally)
POI = {
    "a12": ("custom/tomica_sticker.png", None, 1.0),          # S011
    "d16": ("custom/mitsuya_sticker.png", None, 1.0),         # S083
    "c06": ("custom/softbank_t.png", WH, 0.92),               # S055
    "c10": ("custom/softbank_t.png", WH, 0.92),               # S057
    "d01": ("custom/softbank_t.png", WH, 0.92),               # S071
    "d02": ("custom/softbank_t.png", WH, 0.92),               # S072
    "d03": ("custom/softbank_t.png", WH, 0.92),               # S073
}
POI_KEEP = {"b20", "c04", "c21", "c23", "c25", "d00", "d12"}   # S044 S053 S066 S068 S069 S070 S079


# ---------------------------------------------------------------- "keep original" chosen in the catalogue
# Read straight from catalogue/choices/choices.json, so any sign marked keep original is reset.
def _keeps():
    import csv
    import re
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "catalogue")
    try:
        state = json.load(open(os.path.join(root, "choices", "choices.json"), encoding="utf-8"))
        cat = {r["id"]: r for r in csv.DictReader(open(os.path.join(root, "catalogue.csv"), encoding="utf-8-sig"))}
    except (OSError, ValueError):
        return
    for sid, st in state.items():
        if (st.get("choice") or "").strip().lower() != "keep original" or sid not in cat:
            continue
        src, where = cat[sid]["source_texture"], cat[sid]["where"]
        if sid[0] == "P":
            m = re.match(r"x(\d+)-(\d+) y(\d+)-(\d+)", where)
            x0, x1, y0, y1 = map(int, m.groups())
            PLAIN.append((src, restore((x0, y0, x1, y1))))
        elif sid[0] == "T":
            m = re.match(r"cell col (\d+) row (\d+)", where)
            KEEP_CELLS.add((src, (int(m.group(1)), int(m.group(2)))))
        elif sid[0] == "S":
            m = re.match(r"cell row (\d+) col (\d+)", where)
            POI_KEEP.add(src.split("_")[-2] + m.group(1) + m.group(2))
        elif sid[0] == "D":
            m = re.match(r"tile row (\d+) col (\d+)", where)
            X9_KEEP.add((int(m.group(1)) - 1, int(m.group(2)) - 1))


X9_KEEP = set()   # directory board tiles (row, col), 0-based
_keeps()
