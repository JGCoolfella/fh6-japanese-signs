"""Plain-colour rebrand jobs: {texture stem: [ops]} — see rebrand_plain.py for op types.
Boxes are in pixels of the largest version of each texture."""

WHITE = (244, 245, 246)
GREY = (228, 228, 228)

# ---------------------------------------------------------------- Lawson (was 365 Konbini)
LW_BLUE, LW_PINK, LW_WHITE = (0, 104, 183), (240, 160, 190), (250, 251, 252)
LW_WORD = "lawson_logo.png"


def lawson_tile(box, vertical=False):
    return [
        {"op": "bands", "box": box, "bg": LW_BLUE, "bands": [(0.80, 0.86, LW_PINK)], "vertical": vertical},
        {"op": "logo", "box": box, "file": LW_WORD, "colour": (255, 255, 255),
         "rotate": -90 if vertical else 0, "fill": 0.84 if vertical else 0.84, "valign": 0.42},
    ]


LAWSON = {
    "sgn_gbl_shop_aboard_01_a6_bclr": lawson_tile((0, 0, 342, 256)),
    "sgn_gbl_shop_aboard_01_a8_bclr": lawson_tile((682, 0, 1024, 512), vertical=False),
    "sgn_gbl_board_grassroute_01_abcd_bclr": lawson_tile((0, 768, 512, 1024)),
    "sgn_gbl_shops_vinyl_poster_01_a6_bclr": lawson_tile((0, 0, 256, 512), vertical=True),
    "tex_cty_decal_akih_billbrd_atlas_01_vertical_b_bclr": lawson_tile((0, 0, 683, 2048), vertical=True),
    # plain shopfront sheet, right half: two stripe strips (upper one mirrored), wordmark panel, plates
    "sgn_gbl_shop_station_atlas_01_a_bclr": [
        {"op": "bands", "box": (512, 296, 1024, 408), "bg": LW_WHITE, "bands": [(0.23, 0.70, LW_BLUE), (0.82, 0.89, LW_PINK)]},
        {"op": "bands", "box": (512, 0, 1024, 112), "bg": LW_WHITE, "bands": [(0.11, 0.18, LW_PINK), (0.30, 0.77, LW_BLUE)]},
        {"op": "fill", "box": (512, 112, 1024, 296), "rgb": (255, 255, 255)},
        {"op": "logo", "box": (527, 112, 893, 296), "file": LW_WORD, "colour": LW_BLUE, "fill": 0.9, "squash": 1.9},
        {"op": "remap", "box": (512, 408, 1024, 512), "map": [((255, 230, 0), (255, 255, 255)), ((238, 238, 238), (238, 238, 238)),
                                                             ((235, 30, 50), (235, 30, 50)), ((20, 70, 160), (20, 70, 160)), ((60, 60, 60), (60, 60, 60))]},
    ],
}

# ---------------------------------------------------------------- FamilyMart (was Kadomart)
FM_GREEN, FM_BLUE = (0, 160, 64), (0, 136, 208)
KADO_ORANGE, KADO_NAVY, KADO_NAVY2 = (252, 156, 0), (24, 48, 108), (0, 24, 84)
FM_WORD = "familymart_wordmark.png"

FAMILYMART = {
    # plain shopfront sheet, left half (right half is the Lawson fascia)
    "sgn_gbl_shop_station_atlas_01_a_bclr": [
        {"op": "remap", "box": (0, 0, 512, 400), "map": [(GREY, WHITE), (KADO_ORANGE, FM_GREEN), (KADO_NAVY, FM_BLUE)]},
        {"op": "bands", "box": (0, 0, 512, 112), "bg": WHITE, "bands": [(0.12, 0.48, FM_GREEN), (0.80, 0.90, FM_BLUE)]},
        {"op": "logo", "box": (0, 190, 330, 390), "file": FM_WORD, "colour": FM_BLUE, "bg": WHITE, "fill": 0.86},
        # plates: ATM / 24h blue with white text, P green
        {"op": "remap", "box": (11, 400, 139, 501), "map": [(KADO_ORANGE, FM_BLUE), (KADO_NAVY, (255, 255, 255))]},
        {"op": "remap", "box": (261, 400, 387, 501), "map": [(KADO_ORANGE, FM_BLUE), (KADO_NAVY, (255, 255, 255))]},
        {"op": "remap", "box": (146, 400, 253, 501), "map": [(KADO_NAVY, FM_GREEN), (GREY, (255, 255, 255))]},
    ],
    # A-board atlas: Kadomart tile top-left
    "sgn_gbl_shop_aboard_01_a5_bclr": [
        {"op": "bands", "box": (0, 0, 342, 512), "bg": WHITE, "bands": [(0.0, 0.09, FM_GREEN), (0.155, 0.195, FM_BLUE)]},
        {"op": "logo", "box": (0, 250, 342, 470), "file": FM_WORD, "colour": FM_BLUE, "fill": 0.86},
    ],
    # vertical multi-tenant sign: Kadomart column (bank ATM plate below is kept)
    "sgn_gbl_shop_vertical_02_a5_bclr": [
        {"op": "bands", "box": (0, 0, 168, 850), "bg": WHITE, "bands": [(0.0, 0.034, FM_GREEN), (0.06, 0.075, FM_BLUE)]},
        {"op": "logo", "box": (2, 105, 166, 205), "file": FM_WORD, "colour": FM_BLUE, "fill": 0.95},
    ],
    # vinyl poster atlas: Kadomart tile
    "sgn_gbl_shops_vinyl_poster_01_a5_bclr": [
        {"op": "bands", "box": (0, 0, 256, 512), "bg": WHITE, "bands": [(0.0, 0.08, FM_GREEN), (0.155, 0.195, FM_BLUE)]},
        {"op": "logo", "box": (0, 300, 256, 480), "file": FM_WORD, "colour": FM_BLUE, "fill": 0.88},
    ],
    # high-rise shop facade: blade sign + fascia pieces
    "bld_cty_hrise_m_shop_01_a_feature_a_bclr": [
        {"op": "remap", "box": (683, 17, 876, 671), "map": [(GREY, GREY), ((252, 252, 252), (252, 252, 252)), (KADO_NAVY2, FM_BLUE), (KADO_ORANGE, FM_GREEN)]},
        {"op": "fill", "box": (712, 100, 818, 578), "rgb": (236, 236, 236)},
        {"op": "logo", "box": (712, 100, 818, 578), "file": FM_WORD, "colour": FM_BLUE, "rotate": -90, "fill": 0.96},
        {"op": "remap", "box": (686, 711, 1007, 905), "map": [(GREY, GREY), ((252, 252, 252), (252, 252, 252)), (KADO_NAVY2, FM_BLUE), (KADO_ORANGE, FM_GREEN)]},
        {"op": "remap", "box": (114, 836, 313, 990), "map": [(GREY, GREY), ((252, 252, 252), (252, 252, 252)), (KADO_NAVY2, FM_BLUE), (KADO_ORANGE, FM_GREEN)]},
    ],
}

# ---------------------------------------------------------------- batch 2: services
MK_BLUE, MK_YEL = (29, 57, 196), (255, 225, 0)              # Matsumoto Kiyoshi (was Kakimoto Takashi)
WC_WHITE = (250, 250, 250)                                   # Welcia (was Medi Pharmacy)
SMBC_GREEN = (0, 88, 58)                                     # SMBC (was Midori Bank)
EN_ORANGE, EN_WHITE = (238, 120, 0), (248, 248, 246)         # ENEOS (was Molecule)
ME_GREEN, ME_WHITE = (0, 140, 70), (250, 250, 248)           # Maruetsu (was Maruyama Store)
AB_ORANGE = (240, 95, 10)                                    # Autobacs (was Yuji's Auto)


def mk_tile(box, vertical=False):
    return [
        {"op": "bands", "box": box, "bg": MK_BLUE, "bands": [(0.0, 0.04, MK_YEL), (0.96, 1.0, MK_YEL)]},
        {"op": "logo", "box": box, "file": "matsukiyo_logo_v.png" if vertical else "matsukiyo_logo.png", "fill": 0.86},
    ]


def wc_tile(box, vertical=False):
    return [{"op": "fill", "box": box, "rgb": WC_WHITE},
            {"op": "logo", "box": box, "file": "welcia_logo.png", "rotate": -90 if vertical else 0, "fill": 0.84}]


def smbc_tile(box, vertical=False):
    return [{"op": "fill", "box": box, "rgb": SMBC_GREEN},
            {"op": "logo", "box": box, "file": "smbc_logo_w.png", "rotate": -90 if vertical else 0, "fill": 0.86}]


def eneos_tile(box, vertical=False):
    return [{"op": "bands", "box": box, "bg": EN_WHITE, "bands": [(0.86, 0.94, EN_ORANGE)]},
            {"op": "logo", "box": box, "file": "eneos_logo.png", "rotate": -90 if vertical else 0, "fill": 0.84, "valign": 0.4}]


def me_tile(box, vertical=False):
    return [{"op": "bands", "box": box, "bg": ME_WHITE, "bands": [(0.0, 0.05, ME_GREEN), (0.95, 1.0, ME_GREEN)]},
            {"op": "logo", "box": box, "file": "maruetsu_logo.png", "rotate": -90 if vertical else 0, "fill": 0.86}]


AKH, AKS, AKV, AKVB = ("tex_cty_decal_akih_billbrd_atlas_01_horizontal_bclr", "tex_cty_decal_akih_billbrd_atlas_01_square_bclr",
                      "tex_cty_decal_akih_billbrd_atlas_01_vertical_bclr", "tex_cty_decal_akih_billbrd_atlas_01_vertical_b_bclr")
BATCH2 = [
    # Matsumoto Kiyoshi
    (AKH, [{"op": "fill", "box": (0, 410, 2048, 742), "rgb": MK_BLUE},
           {"op": "logo", "box": (60, 430, 1990, 722), "file": "matsukiyo_logo.png", "fill": 0.9}]),
    (AKS, [{"op": "bands", "box": (683, 683, 1365, 1365), "bg": MK_BLUE, "bands": [(0.0, 0.04, MK_YEL), (0.96, 1.0, MK_YEL)]},
           {"op": "logo", "box": (683, 683, 1365, 1365), "file": "matsukiyo_logo_sq.png", "fill": 0.84}]),
    (AKVB, mk_tile((1365, 0, 2048, 2048), vertical=True)),
    ("sgn_gbl_shop_aboard_01_a6_bclr", mk_tile((0, 256, 342, 512))),
    ("sgn_gbl_shop_aboard_01_a8_bclr", mk_tile((342, 0, 683, 512), vertical=True)),
    ("sgn_gbl_shops_vinyl_poster_01_a6_bclr", mk_tile((768, 0, 1024, 512), vertical=True)),
    ("sgn_gbl_shops_vinyl_poster_02_a6_bclr", mk_tile((768, 0, 1024, 512), vertical=True)),
    ("sgn_gbl_shop_vertical_02_a6_bclr", mk_tile((171, 0, 341, 1024), vertical=True)),
    # Welcia
    (AKH, wc_tile((0, 1560, 2048, 2048))),
    (AKS, wc_tile((0, 0, 683, 683))),
    (AKV, wc_tile((683, 0, 1365, 2048), vertical=True)),
    ("sgn_gbl_shop_vertical_02_a6_bclr", wc_tile((0, 0, 170, 1024), vertical=True)),
    # SMBC
    (AKS, smbc_tile((0, 1365, 683, 2048))),
    (AKV, smbc_tile((1365, 0, 2048, 2048), vertical=True)),
    # ENEOS
    ("sgn_cty_digital_02_a_xsummerx_bclr", eneos_tile((30, 30, 236, 460))),
    ("bld_gbl_comm_gstation_01_a_decal_bclr", [
        {"op": "bands", "box": (0, 0, 512, 512), "bg": EN_WHITE, "bands": [(0.80, 0.92, EN_ORANGE)]},
        {"op": "logo", "box": (20, 20, 492, 220), "file": "eneos_logo.png", "fill": 0.92}]),
    ("bld_gbl_comm_gstation_01_a_feature_xsummerx_bclr", [
        {"op": "remap", "box": (0, 585, 512, 772), "map": [((125, 25, 25), EN_ORANGE), ((150, 40, 40), EN_ORANGE),
                                                         ((90, 95, 105), (90, 95, 105)), ((200, 200, 200), (200, 200, 200))]}]),
    ("sgn_gbl_shops_vinyl_poster_02_a6_bclr", eneos_tile((512, 0, 768, 512), vertical=True)),
    # Maruetsu
    ("bld_gbl_comm_02_a_decal_bclr", [
        {"op": "bands", "box": (0, 30, 1024, 240), "bg": ME_WHITE, "bands": [(0.0, 0.06, ME_GREEN), (0.94, 1.0, ME_GREEN)]},
        {"op": "logo", "box": (80, 45, 944, 225), "file": "maruetsu_logo.png", "fill": 0.92},
        {"op": "remap", "box": (0, 280, 1024, 500), "map": [((225, 30, 35), (196, 196, 194)), ((196, 196, 194), (196, 196, 194))]},
        {"op": "logo", "box": (80, 290, 944, 490), "file": "maruetsu_logo.png", "fill": 0.9}]),
    # keep the pylon's own stripe structure (compresses like the original): yellow->white, white->green
    ("bld_cst_comm_03_a_feature_xsummerx_bclr", [
        {"op": "remap", "box": (293, 15, 643, 905), "map": [((255, 196, 37), ME_WHITE), ((238, 238, 238), ME_GREEN), ((225, 40, 50), ME_WHITE)]},
        {"op": "logo", "box": (340, 220, 596, 700), "file": "maruetsu_logo.png", "colour": ME_GREEN, "rotate": -90, "fill": 0.9}]),
    ("sgn_gbl_shop_aboard_01_a5_bclr", me_tile((341, 0, 683, 512))),
    ("sgn_gbl_shop_vertical_02_a5_bclr", me_tile((171, 0, 336, 1024), vertical=True)),
    ("sgn_gbl_shops_vinyl_poster_01_a5_bclr", me_tile((256, 0, 512, 512), vertical=True)),
    # Autobacs
    ("sgn_gbl_yuji_auto_01_a_bclr", [
        {"op": "fill", "box": (0, 0, 1024, 288), "rgb": (250, 250, 250)},
        {"op": "logo", "box": (40, 10, 984, 280), "file": "autobacs_logo_t.png", "fill": 0.95},
        {"op": "remap", "box": (0, 395, 1024, 512), "map": [((60, 80, 140), AB_ORANGE), ((220, 220, 225), (255, 255, 255))]}]),
]

# ---------------------------------------------------------------- batch 3: food, phones, fashion
SB_GREEN = (0, 112, 74)                                      # Starbucks (was Cafe Asatsuyu)
UQ_RED = (224, 16, 32)                                       # UNIQLO (was CHROMA)
DC_BLUE, DC_WHITE = (32, 112, 176), (244, 244, 244)          # docomo (was ON mobile)
OH_RED = (224, 16, 32)                                       # Gyoza no Ohsho (was Tatsu)
NK_RED = (176, 16, 16)                                       # Nakau (was Nakaya)


def tile(box, bg, logo, rotate=0, fill=0.86, valign=0.5, colour=None):
    return [{"op": "fill", "box": box, "rgb": bg},
            {"op": "logo", "box": box, "file": logo, "rotate": rotate, "fill": fill, "valign": valign, "colour": colour}]


SHIB = "bld_cty_poi_shibuya_02_a_signage_xsummerx_bclr"
BATCH3 = [
    # Starbucks
    ("sgn_gbl_shop_aboard_01_a4_bclr", tile((341, 0, 683, 1024), SB_GREEN, "starbucks_logo.png", fill=0.8)),
    ("sgn_gbl_shops_vinyl_poster_01_a4_bclr", tile((768, 0, 1024, 512), SB_GREEN, "starbucks_logo.png", fill=0.8)),
    # UNIQLO
    ("sgn_gbl_shop_aboard_01_a4_bclr", tile((0, 0, 341, 1024), UQ_RED, "uniqlo_logo.png", fill=0.84)),
    ("sgn_gbl_shops_vinyl_poster_01_a4_bclr", tile((0, 0, 256, 512), UQ_RED, "uniqlo_logo.png", fill=0.84)),
    ("sgn_gbl_shops_vinyl_poster_01_a4_bclr", tile((256, 0, 512, 512), (245, 245, 245), "uniqlo_logo_en.png", fill=0.84)),
    (SHIB, tile((0, 0, 124, 282), UQ_RED, "uniqlo_logo.png", fill=0.9)),
    (SHIB, tile((124, 0, 247, 282), (245, 245, 245), "uniqlo_logo_en.png", fill=0.9)),
    (SHIB, tile((0, 282, 367, 512), UQ_RED, "uniqlo_logo_en.png", fill=0.8)),
    (SHIB, tile((367, 0, 439, 512), UQ_RED, "uniqlo_logo.png", fill=0.9)),
    (SHIB, tile((439, 0, 512, 512), (245, 245, 245), "uniqlo_logo_en.png", fill=0.9)),
    # docomo
    (AKH, tile((0, 0, 2048, 384), DC_WHITE, "docomo_logo.png", fill=0.8)),
    (AKS, tile((683, 1365, 1365, 2048), DC_WHITE, "docomo_logo.png", fill=0.84)),
    # (vertical_b sheet keeps ON mobile: three brands on that sheet no longer fit its slot)
    ("sgn_gbl_billboard_01_a_billboard_xsummerx_bclr", tile((0, 415, 440, 508), (240, 240, 240), "docomo_logo.png", fill=0.9)),
    ("sgn_gbl_billboard_01_a_billboard_xsummerx_bclr", tile((0, 925, 440, 1018), (240, 240, 240), "docomo_logo.png", fill=0.9)),
    # Gyoza no Ohsho
    ("sgn_gbl_shop_aboard_01_a6_bclr", tile((342, 0, 683, 256), OH_RED, "ohsho_logo.png", fill=0.92)),
    ("sgn_gbl_shops_vinyl_poster_01_a6_bclr", tile((256, 0, 512, 512), OH_RED, "ohsho_logo.png", fill=0.94)),
    ("sgn_gbl_shop_vertical_02_a6_bclr", tile((342, 0, 512, 1024), OH_RED, "ohsho_logo.png", fill=0.94)),
    # Nakau
    ("sgn_gbl_shop_aboard_01_a5_bclr", tile((0, 512, 342, 1024), NK_RED, "nakau_logo.png", fill=0.9)),
    ("sgn_gbl_shops_vinyl_poster_01_a5_bclr", tile((768, 0, 1024, 512), NK_RED, "nakau_logo.png", fill=0.9)),
]

# ---------------------------------------------------------------- batch 4: car culture, drinks, radio
AKA, AKB, AKC, AKD = ("tex_cty_decal_akih_billbrd_atlas_01_a_bclr", "tex_cty_decal_akih_billbrd_atlas_01_b_bclr",
                      "tex_cty_decal_akih_billbrd_atlas_01_c_bclr", "tex_cty_decal_akih_billbrd_atlas_01_d_bclr")
OFFW = (236, 236, 234)


def halves(logo, bg, fill=0.8):
    """Roadside/circuit billboards: the texture holds the board twice (top/bottom)."""
    return tile((14, 14, 1010, 498), bg, logo, fill=fill) + tile((14, 526, 1010, 1010), bg, logo, fill=fill)


BATCH4 = [
    ("sgn_gbl_billboard_01_b_billboard_xsummerx_bclr", halves("motul_logo.png", OFFW, 0.86)),     # Flowzoil -> Motul
    ("sgn_gbl_billboard_01_c_billboard_xsummerx_bclr", halves("tomica_logo.png", OFFW, 0.86)),    # Tomitama -> Tomica
    ("sgn_gbl_billboard_01_a_billboard_xsummerx_bclr", halves("docomo_logo.png", OFFW, 0.8)),     # ON mobile -> docomo
    ("sng_gbl_billboard_01_e_xsummerx_bclr",
     tile((28, 28, 2020, 1000), (224, 16, 32), "ohsho_logo.png", fill=0.86)
     + tile((28, 1052, 2020, 2020), (224, 16, 32), "ohsho_logo.png", fill=0.86)),                # Tatsu -> Ohsho
    ("sgn_gbl_crct_billboard_01_a_feature_xsummerx_bclr", halves("spoon_logo.png", (0, 60, 150), 0.8)),  # Techsports -> Spoon
    ("sgn_gbl_crct_billboard_01_b_feature_xsummerx_bclr", halves("rays_logo.png", (20, 20, 22), 0.8)),   # Prorata -> RAYS
    ("sgn_gbl_crct_billboard_01_e_feature_xsummerx_bclr", halves("hks_logo.png", OFFW, 0.7)),            # turbopod -> HKS
    # Akihabara billboard sheets
    (AKA, tile((0, 0, 1024, 650), OFFW, "tomica_logo.png", fill=0.8)),
    (AKA, tile((0, 650, 1024, 1300), OFFW, "mitsuya_logo.png", fill=0.84)),
    (AKD, tile((683, 1024, 1365, 2048), OFFW, "tomica_logo.png", fill=0.84)),
    (AKD, tile((1365, 0, 2048, 1024), OFFW, "mitsuya_logo.png", fill=0.84)),
    (AKD, tile((0, 0, 683, 1024), DC_WHITE, "docomo_logo.png", fill=0.84)),
    (AKB, tile((1024, 0, 2048, 650), (245, 245, 245), "tokyofm_logo.png", fill=0.84)),
    (AKB, tile((1024, 1300, 2048, 2048), (230, 20, 30), "motul_logo.png", fill=0.84)),
    (AKB, tile((0, 1300, 1024, 2048), DC_WHITE, "docomo_logo.png", fill=0.8)),
    (AKB, tile((0, 650, 1024, 1300), SMBC_GREEN, "smbc_logo_w.png", fill=0.84)),
    (AKC, tile((0, 0, 683, 1024), DC_WHITE, "docomo_logo.png", fill=0.84)),
    (AKC, tile((683, 0, 1365, 1024), SMBC_GREEN, "smbc_logo_w.png", fill=0.84)),
    (AKC, tile((1365, 1024, 2048, 2048), (245, 245, 245), "tokyofm_logo.png", fill=0.84)),
    ("sgn_gbl_shops_vinyl_poster_02_a6_bclr", tile((256, 0, 512, 512), (245, 245, 245), "tokyofm_logo.png", rotate=-90, fill=0.86)),
    ("sgn_gbl_shops_vinyl_poster_02_a6_bclr", tile((0, 0, 256, 512), OFFW, "mitsuya_logo.png", rotate=-90, fill=0.86)),
]

# ---------------------------------------------------------------- batch 5: window stickers / hanging signs
F1, F4 = "tex_gbl_fittings_com_01_a_bclr", "tex_gbl_fittings_com_04_a_bclr"
IC_RED = (200, 25, 30)


def fit(box, kind):
    """Pick a logo/colour by brand and by the sticker's shape."""
    x0, y0, x1, y1 = box
    tall = (y1 - y0) > 1.3 * (x1 - x0)
    if kind == "mk":
        return [{"op": "bands", "box": box, "bg": MK_BLUE, "bands": [(0.0, 0.05, MK_YEL), (0.95, 1.0, MK_YEL)]},
                {"op": "logo", "box": box, "file": "matsukiyo_logo_v.png" if tall else "matsukiyo_logo_sq.png", "fill": 0.86}]
    table = {"wc": (WC_WHITE, "welcia_logo.png"), "dc": (DC_WHITE, "docomo_logo.png"),
             "fm": ((245, 245, 245), "tokyofm_logo.png"), "oh": (OH_RED, "ohsho_logo.png"),
             "ab": ((250, 250, 250), "autobacs_logo_t.png"), "sb": (SB_GREEN, "starbucks_logo.png"),
             "nk": (NK_RED, "nakau_logo.png"), "ic": (IC_RED, "ichiran_logo.png"),
             "uq": (UQ_RED, "uniqlo_logo.png"), "ts": ((240, 240, 240), "taitostation_logo.png")}
    bg, logo = table[kind]
    rot = -90 if tall and kind in ("wc", "dc", "fm", "ts") else 0
    return tile(box, bg, logo, rotate=rot, fill=0.86)


BATCH5 = [
    # window stickers
    (F1, fit((67, 108, 184, 159), "oh")), (F1, fit((356, 148, 481, 328), "dc")), (F1, fit((569, 74, 655, 125), "ab")),
    (F1, fit((657, 72, 712, 125), "mk")), (F1, fit((454, 351, 499, 415), "wc")), (F1, fit((336, 481, 415, 543), "mk")),
    (F1, fit((82, 524, 171, 643), "nk")), (F1, fit((591, 499, 701, 655), "fm")), (F1, fit((983, 689, 1019, 739), "dc")),
    (F1, fit((309, 784, 404, 835), "dc")), (F1, fit((863, 776, 1019, 835), "nk")), (F1, fit((775, 860, 829, 940), "mk")),
    (F1, fit((932, 18, 973, 80), "sb")), (F1, fit((673, 397, 707, 449), "sb")),
    # hanging window signs
    (F4, fit((205, 0, 410, 205), "wc")), (F4, fit((410, 148, 614, 205), "wc")), (F4, fit((614, 0, 819, 205), "dc")),
    (F4, fit((0, 205, 205, 410), "ts")), (F4, fit((0, 410, 205, 614), "wc")), (F4, fit((0, 614, 205, 819), "mk")),
    (F4, fit((410, 614, 614, 696), "sb")), (F4, fit((205, 819, 410, 1024), "sb")), (F4, fit((614, 717, 819, 819), "ic")),
    (F4, fit((614, 819, 819, 1024), "nk")), (F4, fit((819, 614, 1024, 819), "uq")),
]

# ---------------------------------------------------------------- batch 6: user-chosen brands
SB, BM, SY, YH, BO, CL, KI = ("softbank_logo.png", "beams_logo.png", "seiyu_logo.png", "yellowhat_logo.png",
                              "boss_logo.png", "cclemon_logo.png", "kirin_logo.png")
WH, YEL, CLY = (246, 246, 246), (250, 215, 0), (255, 222, 0)
BATCH6 = [
    # Akihabara sheets
    (AKA, tile((1024, 0, 2048, 650), YEL, YH, fill=0.84)),            # Owner's -> Yellow Hat
    (AKA, tile((1024, 650, 2048, 1300), WH, BM, fill=0.8)),           # PRAV -> BEAMS
    (AKA, tile((0, 1300, 1024, 2048), WH, SB, fill=0.84)),            # sybil -> SoftBank
    (AKA, tile((1024, 1300, 2048, 2048), CLY, CL, fill=0.7)),         # Swizzer -> C.C. Lemon
    (AKB, tile((0, 0, 1024, 650), WH, BO, fill=0.7)),                 # Vaneso Gold -> BOSS
    (AKB, tile((1024, 650, 2048, 1300), WH, KI, fill=0.8)),           # Brass Harbor -> Kirin
    (AKC, tile((1365, 0, 2048, 1024), WH, BO, fill=0.8)),
    (AKC, tile((0, 1024, 683, 2048), WH, SB, fill=0.86)),
    (AKC, tile((683, 1024, 1365, 2048), WH, KI, fill=0.86)),
    (AKD, tile((683, 0, 1365, 1024), WH, BM, fill=0.86)),
    (AKD, tile((0, 1024, 683, 2048), CLY, CL, fill=0.8)),
    (AKD, tile((1365, 1024, 2048, 2048), YEL, YH, fill=0.86)),
    (AKS, tile((683, 0, 1365, 683), WH, BM, fill=0.86)),
    (AKS, tile((1365, 0, 2048, 683), CLY, CL, fill=0.8)),
    (AKS, tile((0, 683, 683, 1365), OFFW, "mitsuya_logo.png", fill=0.86)),
    (AKS, tile((1365, 683, 2048, 1365), WH, SY, fill=0.86)),
    (AKS, tile((1365, 1365, 2048, 2048), WH, SB, fill=0.86)),
    (AKH, tile((0, 742, 2048, 1260), WH, SB, fill=0.8)),
    (AKH, tile((0, 1260, 2048, 1560), WH, SY, fill=0.8)),
    (AKV, tile((0, 0, 683, 2048), WH, SY, rotate=-90, fill=0.86)),
    # city billboards
    ("sgn_cty_billboard_sqre_lrge_01_a_bclr", tile((1024, 0, 2048, 1024), OFFW, "mitsuya_logo.png", fill=0.84)),
    ("sgn_cty_billboard_rect_01_a_bclr", tile((2048, 1024, 4096, 2048), (20, 20, 22), "rays_logo.png", fill=0.8)),
    ("sgn_cty_billboard_sqre_x2_01_a_bclr", tile((0, 0, 1024, 1024), (20, 20, 22), "rays_logo.png", fill=0.84)
     + tile((0, 1024, 1024, 2048), (245, 245, 245), "tokyofm_logo.png", fill=0.86)
     + tile((1024, 2048, 2048, 3072), OFFW, "mitsuya_logo.png", fill=0.86)),
    ("tex_gbl_sgn_com_billboard_v_01_a_bclr", mk_tile((0, 0, 256, 2048), vertical=True)),
    ("sgn_cty_shops_vinyl_6m_01_a3_bclr", tile((0, 0, 1024, 128), (245, 245, 245), "tokyofm_logo.png", fill=0.8)),
    ("sgn_cty_shop_standingsign_01_records_bclr", tile((0, 0, 256, 512), (245, 245, 245), "tokyofm_logo.png", fill=0.84)),
    # roadside / circuit boards
    ("sgn_gbl_billboard_grassroute_01_abcd_bclr", tile((0, 0, 512, 256), (0, 60, 150), "spoon_logo.png", fill=0.8)
     + tile((0, 256, 512, 512), (20, 20, 22), "rays_logo.png", fill=0.8)
     + tile((0, 512, 512, 768), WH, SB, fill=0.84)),
    ("sgn_gbl_board_grassroute_01_efgh_bclr", tile((0, 512, 512, 768), (240, 240, 240), "taitostation_logo.png", fill=0.9)
     + tile((0, 768, 512, 1024), WH, SY, fill=0.84)),
    ("sgn_gbl_crct_billboard_01_c_feature_xsummerx_bclr", halves(SB, WH, 0.8)),
    # window stickers / hanging signs: Moriya -> Seiyu
    (F1, tile((67, 160, 170, 297), WH, SY, rotate=-90, fill=0.9)),
    (F1, tile((395, 758, 449, 814), WH, SY, fill=0.9)),
    (F4, tile((614, 410, 819, 614), WH, SY, fill=0.86)),
]

import brand_filter  # noqa: E402  (which brands are switched on: catalogue/choices/enabled_brands.json)

JOBS = {}
for group, group_brand in ((LAWSON, "Lawson"), (FAMILYMART, "FamilyMart")):
    for stem, ops in group.items():
        JOBS.setdefault(stem, []).extend(brand_filter.filter_ops(ops, group_brand))
for stem, ops in BATCH2 + BATCH3 + BATCH4 + BATCH5 + BATCH6:
    gb = "ENEOS" if "gstation" in stem and not any(o["op"] == "logo" for o in ops) else None
    JOBS.setdefault(stem, []).extend(brand_filter.filter_ops(ops, gb))

# user's per-sign choices (catalogue) override everything above
import jobs_user  # noqa: E402
for stem, ops in jobs_user.PLAIN:
    JOBS.setdefault(stem, []).extend(brand_filter.filter_ops(ops))
JOBS = {k: v for k, v in JOBS.items() if v}
