"""Tinted-sign rebrand jobs (see rebrand_masks.py). Variant blocks / cells come from
tools/variants.py: each variant uses one mask sheet (texture ref) and one atlas cell."""

WHITE = (255, 255, 255)

H3 = lambda row: ("cell", 1, row, 1, 3)        # hrzntl 6m and vinyl 3m sheets: 3 rows
H5 = lambda row: ("cell", 1, row, 1, 5)        # vinyl 6m sheets: 5 rows
SQ = lambda col, row: ("cell", col, row, 2, 2)  # square sheets: 2 x 2
HR, V3, V6, SQM = ("sgn_gbl_shop_hrzntl_6m_01_a", "sgn_gbl_shop_vinyl_3m_01_a", "sgn_gbl_shops_vinyl_6m_01_a",
                   "sgn_gbl_shop_square_01_a")

# ---------------------------------------------------------------- Lawson (was 365 Konbini)
LW = {"white": WHITE, "blue": (0, 104, 183), "pink": (240, 160, 190)}
LW_STRIP = {"colours": LW, "bg": "white", "bands": [(0.23, 0.70, "blue"), (0.82, 0.89, "pink")],
            "panel": (0.32, 0.68, "white"), "logo": "lawson_logo.png", "logo_colour": "blue",
            "logo_box": (0.33, 0.25, 0.67, 0.75)}
LW_TILE = {"colours": LW, "bg": "blue", "bands": [(0.80, 0.86, "pink")], "logo": "lawson_logo.png",
           "logo_colour": "white", "logo_box": (0.08, 0.27, 0.92, 0.57)}
LAWSON = [
    (HR, HR + "7", 14, (0, 25, 1024, 140), LW_STRIP),
    (V3, V3 + "7", 14, (0, 30, 512, 140), LW_STRIP),
    (V6, V6 + "5", 2, (0, 14, 1024, 86), LW_STRIP),
    (SQM, SQM + "6", 16, (0, 0, 256, 256), LW_TILE),
]

# ---------------------------------------------------------------- FamilyMart (was Kadomart)
FM = {"white": WHITE, "green": (0, 160, 64), "blue": (0, 136, 208)}
FM_STRIP = {"colours": FM, "bg": "white", "bands": [(0.0, 0.30, "green"), (0.88, 0.96, "blue")],
            "logo": "familymart_wordmark.png", "logo_colour": "blue", "logo_box": (0.28, 0.38, 0.72, 0.82)}
FM_TILE = {"colours": FM, "bg": "white", "bands": [(0.0, 0.20, "green"), (0.84, 0.90, "blue")],
           "logo": "familymart_wordmark.png", "logo_colour": "blue", "logo_box": (0.06, 0.36, 0.94, 0.72)}
FAMILYMART = [
    (HR, HR + "5", 8, (0, 0, 1024, 150), FM_STRIP),
    (V3, V3 + "5", 8, (0, 0, 512, 150), FM_STRIP),
    (V6, V6 + "4", 10, (0, 0, 1024, 90), FM_STRIP),
    (SQM, SQM + "5", 12, (0, 0, 256, 256), FM_TILE),
]

# ---------------------------------------------------------------- batch 2: services
JAPANPOST = {"colours": {"white": WHITE, "red": (220, 0, 25)}, "bg": "white",
             "bands": [(0.0, 0.07, "red"), (0.93, 1.0, "red")], "logo": "japanpost_logo.png",
             "logo_colour": "red", "logo_box": (0.08, 0.2, 0.92, 0.8)}
MARUETSU = {"colours": {"white": WHITE, "green": (0, 140, 70), "red": (230, 60, 40)}, "bg": "white",
            "bands": [(0.0, 0.06, "green"), (0.94, 1.0, "green")], "logo": "maruetsu_logo.png",
            "logo_box": (0.1, 0.16, 0.9, 0.84)}
MATSUKIYO = {"colours": {"blue": (29, 57, 196), "yellow": (255, 225, 0)}, "bg": "blue",
             "bands": [(0.0, 0.05, "yellow"), (0.95, 1.0, "yellow")], "logo": "matsukiyo_logo.png",
             "logo_box": (0.06, 0.18, 0.94, 0.82)}
MATSUKIYO_SQ = {**MATSUKIYO, "logo": "matsukiyo_logo_sq.png", "logo_box": (0.08, 0.12, 0.92, 0.88)}
WELCIA = {"colours": {"white": WHITE, "blue": (35, 125, 195), "navy": (25, 55, 140)}, "bg": "white",
          "logo": "welcia_logo.png", "logo_box": (0.1, 0.1, 0.9, 0.9)}
SMBC = {"colours": {"green": (0, 88, 58), "lime": (175, 205, 70), "white": WHITE}, "bg": "green",
        "logo": "smbc_logo_w.png", "logo_box": (0.08, 0.15, 0.92, 0.85)}

BATCH2 = [
    (HR, HR + "5", 10, H3(3), JAPANPOST), (V3, V3 + "5", 10, H3(3), JAPANPOST), (V6, V6 + "4", 12, H5(3), JAPANPOST),
    (HR, HR + "5", 9, H3(2), MARUETSU), (V3, V3 + "5", 9, H3(2), MARUETSU), (V6, V6 + "4", 11, H5(2), MARUETSU),
    (SQM, SQM + "5", 13, SQ(2, 1), MARUETSU),
    (HR, HR + "8", 4, H3(1), MATSUKIYO), (V3, V3 + "8", 4, H3(1), MATSUKIYO), (V6, V6 + "5", 5, H5(4), MATSUKIYO),
    (SQM, SQM + "6", 3, SQ(2, 2), MATSUKIYO_SQ),
    (HR, HR + "8", 5, H3(2), WELCIA), (V3, V3 + "8", 5, H3(2), WELCIA), (V6, V6 + "5", 6, H5(5), WELCIA),
    (SQM, SQM + "7", 4, SQ(1, 1), WELCIA),
    (SQM, SQM + "7", 5, SQ(2, 1), SMBC),
]

# ---------------------------------------------------------------- batch 3: food
OHSHO = {"colours": {"red": (224, 16, 32), "white": WHITE, "yellow": (250, 210, 0), "green": (0, 160, 80)},
         "bg": "red", "logo": "ohsho_logo.png", "logo_box": (0.08, 0.08, 0.92, 0.92)}
NAKAU = {"colours": {"red": (176, 16, 16), "white": WHITE}, "bg": "red", "logo": "nakau_logo.png",
         "logo_box": (0.1, 0.05, 0.9, 0.95)}
ICHIRAN = {"colours": {"red": (200, 25, 30), "black": (30, 25, 25), "green": (40, 140, 60), "white": WHITE},
           "bg": "red", "logo": "ichiran_logo.png", "logo_box": (0.1, 0.05, 0.9, 0.95)}

BATCH3 = [
    (HR, HR + "7", 2, H3(2), OHSHO), (V3, V3 + "7", 2, H3(2), OHSHO), (V6, V6 + "5", 3, H5(2), OHSHO),
    (SQM, SQM + "6", 17, SQ(2, 1), OHSHO),
    (HR, HR + "6", 11, H3(1), NAKAU), (V3, V3 + "6", 11, H3(1), NAKAU), (V6, V6 + "4", 13, H5(4), NAKAU),
    (SQM, SQM + "5", 15, SQ(2, 2), NAKAU),
    (HR, HR + "6", 12, H3(2), ICHIRAN), (V3, V3 + "6", 12, H3(2), ICHIRAN), (V6, V6 + "4", 14, H5(5), ICHIRAN),
]

JOBS = LAWSON + FAMILYMART + BATCH2 + BATCH3


# ================================================================ cell-based jobs (rebrand_cells.py)
# Every job applies to ALL variants (any model) drawing the same mask cell.
ICHIRAN_2 = {"colours": {"red": (200, 25, 30), "white": (255, 255, 255)}, "bg": "red",
             "logo": "ichiran_text_w.png", "logo_colour": "white", "logo_box": (0.2, 0.12, 0.8, 0.88)}


def _legacy(job):
    model, mask, block, area, d = job
    if d is ICHIRAN:
        d = ICHIRAN_2
    out = {"via": (model, block), "design": d}
    if area and area[0] != "cell":
        out["area"] = area
    return out


WT = (255, 255, 255)
SEIYU = {"colours": {"white": WT, "red": (230, 0, 18), "dark": (40, 30, 30)}, "bg": "white",
         "logo": "seiyu_logo.png", "logo_box": (0.08, 0.2, 0.92, 0.8)}
SEIYU_V = {**SEIYU, "rotate": -90, "logo_box": (0.15, 0.05, 0.85, 0.95)}
UNIQLO_T = {"colours": {"red": (224, 16, 32), "white": WT}, "bg": "red", "logo": "uniqlo_text_w.png",
            "logo_colour": "white", "logo_box": (0.12, 0.2, 0.88, 0.8)}
STARBUCKS = {"colours": {"green": (0, 112, 74), "white": WT}, "bg": "green", "logo": "starbucks_logo.png",
             "logo_box": (0.3, 0.06, 0.7, 0.94)}
STARBUCKS_V = {**STARBUCKS, "logo_box": (0.08, 0.2, 0.92, 0.8)}
NAKAU_C = {"colours": {"red": (176, 16, 16), "white": WT}, "bg": "red", "logo": "nakau_logo.png",
           "logo_box": (0.08, 0.05, 0.92, 0.95)}
DOCOMO = {"colours": {"white": WT, "blue": (32, 112, 176)}, "bg": "white", "logo": "docomo_logo.png",
          "logo_colour": "blue", "logo_box": (0.08, 0.2, 0.92, 0.8)}
DOCOMO_V = {**DOCOMO, "rotate": -90, "logo_box": (0.12, 0.05, 0.88, 0.95)}
FMT = {"colours": {"white": WT, "blue": (0, 140, 210)}, "bg": "white", "logo": "tokyofm_logo.png",
       "logo_colour": "blue", "logo_box": (0.08, 0.2, 0.92, 0.8)}
TAITO = {"colours": {"white": WT, "blue": (20, 40, 230)}, "bg": "white", "logo": "taitostation_logo.png",
         "logo_colour": "blue", "logo_box": (0.06, 0.25, 0.94, 0.75)}
TAITO_V = {**TAITO, "rotate": -90, "logo_box": (0.1, 0.04, 0.9, 0.96)}
ICHIRAN_V = {"colours": {"red": (200, 25, 30), "white": WT}, "bg": "red", "logo": "ichiran_text_w.png",
             "logo_colour": "white", "rotate": -90, "logo_box": (0.1, 0.05, 0.9, 0.95)}
SMBC_C = {"colours": {"green": (0, 88, 58), "lime": (175, 205, 70), "white": WT}, "bg": "green",
          "logo": "smbc_logo_w.png", "logo_box": (0.08, 0.15, 0.92, 0.85)}
BEAMS_C = {"colours": {"white": WT, "orange": (240, 100, 20)}, "bg": "white", "logo": "beams_logo.png",
           "logo_colour": "orange", "rotate": -90, "logo_box": (0.15, 0.05, 0.85, 0.95)}
SOFTBANK_C = {"colours": {"white": WT, "grey": (140, 140, 145)}, "bg": "white", "logo": "softbank_logo.png",
              "logo_colour": "grey", "logo_box": (0.06, 0.25, 0.94, 0.75)}
WELCIA_C = {"colours": {"white": WT, "blue": (35, 125, 195), "navy": (25, 55, 140)}, "bg": "white",
            "logo": "welcia_logo.png", "logo_box": (0.08, 0.2, 0.92, 0.8)}
WELCIA_CV = {**WELCIA_C, "rotate": -90, "logo_box": (0.12, 0.05, 0.88, 0.95)}
MK_CV = {"colours": {"blue": (29, 57, 196), "yellow": (255, 225, 0)}, "bg": "blue", "logo": "matsukiyo_logo_v.png",
         "bands": [(0.0, 0.03, "yellow"), (0.97, 1.0, "yellow")], "logo_box": (0.1, 0.06, 0.9, 0.94)}
OHSHO_C = {"colours": {"red": (224, 16, 32), "white": WT, "yellow": (250, 210, 0), "green": (0, 160, 80)},
           "bg": "red", "logo": "ohsho_logo.png", "rotate": -90, "logo_box": (0.1, 0.05, 0.9, 0.95)}
NAKAU_CV = {**NAKAU_C, "logo_box": (0.08, 0.3, 0.92, 0.7)}

GH, GV3, GV6, GSQ, GVT = ("sgn_gbl_shop_hrzntl_6m_01_a", "sgn_gbl_shop_vinyl_3m_01_a", "sgn_gbl_shops_vinyl_6m_01_a",
                          "sgn_gbl_shop_square_01_a", "sgn_gbl_shop_vertical_01_a")
CH, CV3, CV6, CSQ, CAB, CVT, CVT2, CSS, CVR2 = (
    "sgn_cty_shop_hrzntl_6m_01_a", "sgn_cty_shop_vinyl_3m_01_a", "sgn_cty_shops_vinyl_6m_01_a",
    "sgn_cty_shop_square_01_a", "sgn_cty_shop_aboard_01_a", "sgn_cty_shop_vertical_01_a",
    "sgn_cty_shop_vertical_02_a", "sgn_cty_shop_standingsign_01_a", "sgn_cty_shop_vert_02_a")
B04, B05, B06 = "sgn_cty_billboard_04_a", "sgn_cty_billboard_05_a", "sgn_cty_billboard_06_a"

NEW_CELLS = [
    # Moriya -> Seiyu
    {"via": (GH, 3), "design": SEIYU}, {"via": (GV3, 3), "design": SEIYU}, {"via": (GV3, 13), "design": SEIYU},
    {"via": (GV6, 4), "design": SEIYU}, {"via": (GSQ, 2), "design": SEIYU}, {"via": (GVT, 8), "design": SEIYU_V},
    {"via": (B05, 2), "design": SEIYU_V},
    # CHROMA -> UNIQLO (single-channel masks)
    {"via": (GH, 1), "design": UNIQLO_T}, {"via": (GV3, 1), "design": UNIQLO_T}, {"via": (GV6, 1), "design": UNIQLO_T},
    # Cafe Asatsuyu -> Starbucks
    {"via": (GH, 7), "design": STARBUCKS}, {"via": (GV3, 7), "design": STARBUCKS}, {"via": (GV6, 7), "design": STARBUCKS},
    {"via": (CH, 8), "design": STARBUCKS},
    # Nakaya -> Nakau
    {"via": (GVT, 4), "design": NAKAU_CV}, {"via": (B05, 3), "design": NAKAU_CV},
    # ON mobile -> docomo
    {"via": (CH, 5), "design": DOCOMO}, {"via": (CV3, 5), "design": DOCOMO}, {"via": (CSQ, 7), "design": DOCOMO},
    {"via": (CAB, 7), "design": DOCOMO}, {"via": (CVT, 2), "design": DOCOMO_V},
    {"via": (CSS, 27), "design": DOCOMO}, {"via": (CVR2, 21), "design": DOCOMO},
    # Gacha -> FM Tokyo
    {"via": (CV3, 7), "design": FMT}, {"via": (B06, 2), "design": FMT},
    # GAME -> Taito Station
    {"via": (CSS, 15), "design": TAITO_V}, {"via": (CVR2, 9), "design": TAITO_V},
    {"via": (B04, 0), "design": TAITO_V}, {"via": (B05, 4), "design": TAITO_V},
    # Ramen Shin -> Ichiran
    {"via": (CVT2, 7), "design": ICHIRAN_V},
    # Midori Bank -> SMBC
    {"via": (CV6, 12), "design": SMBC_C},
    # cty billboards 04/05/06
    {"via": (B04, 4), "design": BEAMS_C}, {"via": (B05, 0), "design": OHSHO_C}, {"via": (B05, 1), "design": WELCIA_CV},
    {"via": (B05, 5), "design": MK_CV}, {"via": (B06, 0), "design": SOFTBANK_C}, {"via": (B06, 1), "design": WELCIA_C},
]

import jobs_user  # noqa: E402
CELL_JOBS = [_legacy(j) for j in JOBS] + NEW_CELLS + jobs_user.CELLS  # user choices last (they win)
import brand_filter  # noqa: E402
CELL_JOBS = [j for j in CELL_JOBS if brand_filter.design_on(j["design"])]
