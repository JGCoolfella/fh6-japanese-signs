"""Where every sign sits inside the plain-colour (non-tinted) textures.

PIECES: {texture stem: [(label, box), ...]}  boxes in pixels of the largest version.
Helpers build regular grids. Labels name the ORIGINAL (fictional) sign.
"""


def grid(W, H, cols, rows, labels, x0=0, y0=0):
    out = []
    for k, lab in enumerate(labels):
        if lab is None:
            continue
        c, r = k % cols, k // cols
        out.append((lab, (x0 + round(c * W / cols), y0 + round(r * H / rows),
                          x0 + round((c + 1) * W / cols), y0 + round((r + 1) * H / rows))))
    return out


def rows(W, cuts, labels):
    return [(lab, (0, a, W, b)) for lab, a, b in zip(labels, cuts, cuts[1:]) if lab]


def cols(H, cuts, labels):
    return [(lab, (a, 0, b, H)) for lab, a, b in zip(labels, cuts, cuts[1:]) if lab]


ANIME = "anime / manga poster"

PIECES = {
    # ---------------------------------------------------------------- shop A-boards / blade signs / posters
    "sgn_gbl_shop_aboard_01_a4_bclr": grid(1024, 1024, 3, 1, ["CHROMA", "Cafe Asatsuyu", "COLOR"]),
    "sgn_gbl_shop_aboard_01_a5_bclr": grid(1024, 1024, 3, 2, ["Kadomart", "Maruyama Store", "NMO (Mt Fuji)",
                                                              "Nakaya", "Raku Raku Express", "特別 (special)"]),
    "sgn_gbl_shop_aboard_01_a6_bclr": grid(1024, 512, 3, 2, ["365 Konbini", "Tatsu", "Moriya",
                                                             "Kakimoto Takashi 薬", "免税 TAX FREE", "特別価格! (special price)"]),
    "sgn_gbl_shop_aboard_01_a7_bclr": grid(1024, 512, 3, 2, [None, None, None,
                                                             "期間限定 (limited time)", "激安 (bargain)", "セール (sale)"]),
    "sgn_gbl_shop_aboard_01_a8_bclr": grid(1024, 512, 3, 1, ["Moriya (face logo)", "Kakimoto Takashi 薬", "365 Konbini (vertical)"]),
    "sgn_gbl_shop_vertical_02_a4_bclr": cols(1024, [0, 170, 341, 512], ["CHROMA (red)", "CHROMA (white)", "ISSHIN"]),
    "sgn_gbl_shop_vertical_02_a5_bclr": [("Kadomart", (0, 0, 170, 850)), ("銀行 ATM plate", (0, 850, 170, 1024)),
                                         ("Maruyama Store", (170, 0, 341, 1024)), ("Yamaya 山家", (341, 0, 512, 1024))],
    "sgn_gbl_shop_vertical_02_a6_bclr": cols(1024, [0, 170, 341, 512], ["Medi Pharmacy 薬", "Kakimoto Takashi 薬", "Tatsu"]),
    "sgn_gbl_shop_vertical_02_a7_bclr": cols(1024, [0, 170, 341, 512], ["Regent (cafe)", "そば処 瀬戸屋 (soba)", "サンシャイン歯科 (dentist)"]),
    "sgn_gbl_shop_vertical_02_a8_bclr": cols(1024, [0, 170, 341, 512], ["サン薬局 (pharmacy)", "ネモトサトシ", "タカモトサトシ"]),
    "sgn_gbl_shops_vinyl_poster_01_a4_bclr": grid(1024, 512, 4, 1, ["CHROMA (red)", "CHROMA (white)", "COLOR", "Cafe Asatsuyu"]),
    "sgn_gbl_shops_vinyl_poster_01_a5_bclr": grid(1024, 512, 4, 1, ["Kadomart", "Maruyama Store", "NMO (Mt Fuji)", "Nakaya"]),
    "sgn_gbl_shops_vinyl_poster_01_a6_bclr": grid(1024, 512, 4, 1, ["365 Konbini", "Tatsu", "Moriya 森屋", "Kakimoto Takashi 薬"]),
    "sgn_gbl_shops_vinyl_poster_02_a6_bclr": grid(1024, 512, 4, 1, ["fizi PoP!", "Gacha City Radio", "Molecule", "Kakimoto Takashi 薬"]),
    "sgn_gbl_shop_station_atlas_01_a_bclr": [
        ("Kadomart shop fascia", (0, 0, 512, 400)), ("Kadomart plates (ATM / P / 24h)", (0, 400, 512, 512)),
        ("365 Konbini shop fascia", (512, 0, 1024, 408)), ("365 Konbini plates (ATM / P / 24h)", (512, 408, 1024, 512))],
    "sgn_cty_shop_standingsign_01_records_bclr": grid(1024, 512, 4, 1, ["Gacha City Radio", "Hospital", "Sub Pop Mega Mart", None]),
    "sgn_cty_shops_vinyl_6m_01_a3_bclr": rows(1024, [0, 128, 256, 384], ["Gacha City Radio", "Sub Pop Mega Mart", "Hospital"]),
    "tex_sgn_gbl_shop_standingsign_01_a_bclr": [("Norinavi taxi", (0, 0, 256, 512))],
    # ---------------------------------------------------------------- Akihabara billboard sheets
    "tex_cty_decal_akih_billbrd_atlas_01_a_bclr": [(l, b) for l, b in zip(
        ["Tomitama", "Owner's", "fizi PoP!", "PRAV", "sybil", "Swizzer"],
        [(0, 0, 1024, 650), (1024, 0, 2048, 650), (0, 650, 1024, 1300), (1024, 650, 2048, 1300),
         (0, 1300, 1024, 2048), (1024, 1300, 2048, 2048)])],
    "tex_cty_decal_akih_billbrd_atlas_01_b_bclr": [(l, b) for l, b in zip(
        ["Vaneso Gold", "Gacha City Radio", "Midori Bank", "Brass Harbor", "ON mobile (phone ad)", "Flowzoil"],
        [(0, 0, 1024, 650), (1024, 0, 2048, 650), (0, 650, 1024, 1300), (1024, 650, 2048, 1300),
         (0, 1300, 1024, 2048), (1024, 1300, 2048, 2048)])],
    "tex_cty_decal_akih_billbrd_atlas_01_c_bclr": grid(2048, 2048, 3, 2, ["ON mobile (phone ad)", "Midori Bank", "Vaneso Gold",
                                                                          "sybil", "Brass Harbor", "Gacha City Radio"]),
    "tex_cty_decal_akih_billbrd_atlas_01_d_bclr": grid(2048, 2048, 3, 2, ["ON mobile", "PRAV", "fizi PoP!",
                                                                          "Swizzer", "Tomitama", "Owner's"]),
    "tex_cty_decal_akih_billbrd_atlas_01_square_bclr": grid(2048, 2048, 3, 3, [
        "Medi Pharmacy 薬", "PRAV", "Swizzer", "fizi PoP!", "Kakimoto Takashi 薬", "Moriya",
        "Midori Bank", "ON mobile", "sybil"]),
    "tex_cty_decal_akih_billbrd_atlas_01_horizontal_bclr": rows(2048, [0, 410, 742, 1260, 1560, 2048], [
        "ON mobile", "Kakimoto Takashi", "sybil", "Moriya", "Medi Pharmacy 薬"]),
    "tex_cty_decal_akih_billbrd_atlas_01_vertical_b_bclr": grid(2048, 2048, 3, 1, ["365 Konbini", "ON mobile", "Kakimoto Takashi 薬"]),
    "tex_cty_decal_akih_billbrd_atlas_01_vertical_bclr": grid(2048, 2048, 3, 1, ["Moriya 森屋", "Medi Pharmacy 薬", "Midori Bank"]),
    # ---------------------------------------------------------------- billboards (two-faced boards show one face)
    "sgn_gbl_billboard_01_a_billboard_xsummerx_bclr": [("ON mobile (phone ad)", (0, 0, 1024, 512))],
    "sgn_gbl_billboard_01_b_billboard_xsummerx_bclr": [("Flowzoil", (0, 0, 1024, 512))],
    "sgn_gbl_billboard_01_c_billboard_xsummerx_bclr": [("Tomitama", (0, 0, 1024, 512))],
    "sgn_gbl_billboard_01_d_billboard_xsummerx_bclr": [("Raku Raku Express (drivers wanted)", (0, 0, 1024, 512))],
    "sng_gbl_billboard_01_e_xsummerx_bclr": [("Tatsu", (0, 0, 2048, 1024))],
    "sgn_gbl_crct_billboard_01_a_feature_xsummerx_bclr": [("Techsports Racing", (0, 0, 1024, 512))],
    "sgn_gbl_crct_billboard_01_b_feature_xsummerx_bclr": [("Prorata Wheels", (0, 0, 1024, 512))],
    "sgn_gbl_crct_billboard_01_c_feature_xsummerx_bclr": [("sybil", (0, 0, 1024, 512))],
    "sgn_gbl_crct_billboard_01_d_feature_xsummerx_bclr": [("Reizei", (0, 0, 1024, 512))],
    "sgn_gbl_crct_billboard_01_e_feature_xsummerx_bclr": [("turbopod", (0, 0, 1024, 512))],
    "sgn_gbl_billboard_grassroute_01_abcd_bclr": rows(512, [0, 256, 512, 768, 1024], ["Techsports Racing", "Prorata Wheels", "sybil", "Reizei"]),
    "sgn_gbl_board_grassroute_01_abcd_bclr": rows(512, [0, 256, 512, 768, 1024], [
        "Hikari Dental ひかり歯科", "MONO", "Sakata Barber Shop 坂田理容室", "365 Konbini"]),
    "sgn_gbl_board_grassroute_01_efgh_bclr": rows(512, [0, 256, 512, 768, 1024], [
        "Coin Laundry Kiku", "Raku Raku Express", "GAME (arcade)", "Moriya"]),
    "sgn_gbl_board_grassroute_01_a_xsummerx_bclr": [("Horizon Festival board", (0, 0, 512, 512))],
    "sgn_cty_billboard_rect_01_a_bclr": grid(4096, 2048, 2, 2, ["Norio Kun (" + ANIME + ")", "Sakura (" + ANIME + ")", "DeeLite", "Prorata Wheels"]),
    "sgn_cty_billboard_sqre_lrge_01_a_bclr": grid(2048, 2048, 2, 2, ["Sushi chef (" + ANIME + ")", "fizi PoP!", "Princess (" + ANIME + ")", "Chaser Zero (" + ANIME + ")"]),
    "sgn_cty_billboard_sqre_x2_01_a_bclr": grid(2048, 4096, 2, 4, ["Prorata Wheels", "Irakuzu", "Gacha City Radio", "Chika Pi (" + ANIME + ")",
                                                                  "Sushi chef (" + ANIME + ")", "fizi PoP!", "girl (" + ANIME + ")", "boy (" + ANIME + ")"]),
    "sgn_cty_billboard_screen_02_a_feature_xsummerx_bclr": [("電子機器 5G WIFI 今すぐ購入 (electronics ad)", (0, 0, 1024, 1024))],
    "tex_gbl_sgn_com_billboard_01_a_bclr": [("Division Oil (drivers wanted)", (0, 0, 1024, 665)),
                                            ("ドライバー募集 Courier service 宅急便", (0, 665, 1024, 1366)),
                                            ("新店舗は近日オープン (new store opening)", (0, 1366, 1024, 1560)),
                                            ("車の改造 カスタムカー 2211 (custom car shop)", (0, 1560, 1024, 2048))],
    "tex_gbl_sgn_com_billboard_02_a_bclr": grid(2048, 4096, 2, 2, ["Sushi chef (" + ANIME + ")", "girl (" + ANIME + ")", "Norio Kun (" + ANIME + ")", "Chaser Zero (" + ANIME + ")"]),
    "tex_gbl_sgn_com_billboard_v_01_a_bclr": grid(2048, 2048, 6, 1, ["Kakimoto Takashi 薬"] + [ANIME] * 5),
    # ---------------------------------------------------------------- window stickers / hanging signs
    "tex_gbl_fittings_com_04_a_bclr": [(l, b) for l, b in [
        ("Medi Pharmacy 薬 (hanging)", (205, 0, 410, 148)), ("Medi Pharmacy メディ薬局 strip", (205, 148, 614, 205)),
        ("ON mobile", (614, 0, 819, 205)), ("TAKANO 高野", (819, 0, 1024, 205)), ("GAME (arcade)", (0, 205, 205, 410)),
        ("teapot cafe", (205, 205, 410, 410)), ("免税 TAX FREE", (614, 205, 819, 410)), ("Medi Pharmacy 薬", (0, 410, 205, 614)),
        ("Moriya", (614, 410, 819, 614)), ("Kakimoto Takashi 薬", (0, 614, 205, 819)), ("Cafe Asatsuyu (small)", (410, 614, 614, 696)),
        ("ラーメン真 Ramen Shin", (614, 717, 819, 819)), ("CHROMA", (819, 614, 1024, 819)), ("Regent (cafe)", (0, 819, 205, 1024)),
        ("Cafe Asatsuyu", (205, 819, 410, 1024)), ("Nakaya", (614, 819, 819, 1024))]],
    "tex_gbl_fittings_com_01_a_bclr": "components",
    # ---------------------------------------------------------------- building signage
    "bld_gbl_comm_03_a_features_xsummerx_bclr": [("365 Konbini standalone store fascia (Fuji store)", (0, 0, 1024, 128))],
    "bld_cty_hrise_m_shop_01_a_feature_a_bclr": [("Kadomart blade sign", (683, 17, 876, 671)),
                                                 ("Kadomart fascia", (686, 711, 1007, 905)),
                                                 ("Kadomart fascia (small)", (114, 836, 313, 990))],
    "bld_cst_comm_03_a_feature_xsummerx_bclr": [("Maruyama Store マルヤマストア (coastal store)", (293, 0, 645, 910))],
    "bld_gbl_comm_02_a_decal_bclr": [("Maruyama Store fascia", (0, 0, 1024, 275)), ("Maruyama Store wall lettering", (0, 290, 1024, 500)),
                                     ("window stickers (fizi / 配達 / 免税)", (0, 520, 410, 590)),
                                     ("特別価格! 特産品 (special price)", (279, 600, 506, 740)),
                                     ("いつでも大歓迎 (welcome)", (11, 635, 256, 710)), ("営業中 (open)", (860, 620, 1004, 845)),
                                     ("40% OFF / staff wanted / 24h notices", (796, 705, 853, 1012))],
    "bld_gbl_comm_04_features_2_xsummerx_bclr": [("特売 (sale) tags", (0, 30, 470, 200)),
                                                 ("格安ショップ営業中 (discount shop)", (490, 30, 1024, 200)),
                                                 ("特別価格! banner", (0, 200, 1024, 310))],
    "bld_cty_poi_shibuya_02_a_signage_xsummerx_bclr": [("CHROMA (red, stacked)", (0, 0, 122, 282)), ("CHROMA (white, stacked)", (122, 0, 246, 282)),
                                                       ("Horizon Festival", (246, 0, 368, 282)), ("[CHROMA] (red, wide)", (0, 282, 368, 512)),
                                                       ("CHROMA (red, vertical)", (368, 0, 440, 512)), ("CHROMA (white, vertical)", (440, 0, 512, 512))],
    "bld_cty_poi_shibuya_ent_01_a_feature_xsummerx_bclr": [("Tokyo City Metro 東京シティメトロ", (0, 250, 420, 404)),
                                                           ("metro entrance W + line badges", (0, 404, 887, 603)),
                                                           ("Toshin Line / Ito Line board", (0, 740, 1024, 1010))],
    "bld_gbl_comm_gstation_01_a_decal_bclr": [("Molecule gas station", (0, 0, 512, 512))],
    "bld_gbl_crct_comm_02_a_feature_xsummerx_bclr": [("PLACEHOLFER (circuit building)", (815, 240, 1024, 1024))],
    "bld_rur_comm_03_a_feature_xsummerx_bclr": [("農業機械用部品 (farm machinery parts)", (821, 0, 1010, 1024))],
    "inf_gbl_comm_gstation_01_a_feature_xsummerx_bclr": [("最高のサービス! (gas station canopy)", (0, 180, 950, 760))],
    "bld_cty_comm_m_shop_01_a_decal_1_bclr": [("ramen shop menu board", (0, 0, 1024, 512))],
    "tex_gbl_comm_gstation_machine_02_b_bclr": [("Molecule pump panel", (0, 546, 449, 705)), ("Molecule pump panel (2)", (0, 876, 449, 1024))],
    "tex_gbl_comm_gstation_machine_02_bclr": [("Molecule pump label", (310, 895, 380, 1015))],
    "sgn_cty_digital_02_a_xsummerx_bclr": [("Molecule pylon", (0, 0, 512, 512))],
    "prp_gbl_red_flowzoil_01_a_xsummerx_bclr": [("Flowzoil oil drum", (0, 0, 512, 512))],
    # ---------------------------------------------------------------- flags
    "prp_cty_shop_flag_01_b_bclr": [("カフェ CAFE flag", (0, 0, 560, 2048))],
    "prp_cty_shop_flag_01_c_bclr": [("特別価格 flag", (0, 0, 280, 1024))],
    "prp_cty_shop_flag_a_bclr": [("ゴム印 (rubber stamp shop) flag", (0, 0, 560, 2048))],
    "prp_gbl_flag_01_a_atlas_02_bclr": grid(1024, 512, 4, 1, ["TAX FREE 免税 flag", "販売中 FOR SALE flag", "DayTrip 日帰り旅行 flag", "SIGN UP (Horizon) flag"]),
    "prp_gbl_flag_01_a_atlas_bclr": grid(1024, 512, 4, 1, ["販売中 FOR SALE flag", "特別価格! flag", "いらっしゃいませ flag", "営業中 OPEN flag"]),
    "sgn_fst_banner_pylon_01_bclr": [("Horizon Festival banner", (0, 0, 2048, 2048))],
    "sgn_fst_grassroots_01_a_graphics_diff": rows(1024, [0, 180, 430, 610, 810, 1024], [
        "Hokubu Circuit", "Legend Island Circuit", "Sekibe Circuit", "Shimanoyama Drift Circuit", "Soni Circuit"]),
    # ---------------------------------------------------------------- single shop signs (one texture each)
    "sgn_gbl_yuji_auto_01_a_bclr": [("Yuji's Auto", (0, 0, 1024, 512))],
    "sgn_cst_shop_01_a_xsummerx_bclr": [("新鮮で美味い魚 (fish shop)", (0, 0, 1024, 512))],
    "sgn_cty_digital_03_a_feature_01_xsummerx_bclr": [("PLACE HOLDER / no-bikes sign", (0, 0, 1024, 1024))],
    "sgn_cty_isshin_01_a_xsummerx_bclr": [("Isshin (faded shop sign)", (0, 0, 1024, 1024))],
    "sgn_cty_maru_01_a_xsummerx_bclr": [("Maru (shop sign)", (0, 0, 1024, 1024))],
    "sgn_cty_masaru_01_a_xsummerx_bclr": [("Masaru (faded shop sign)", (0, 0, 1024, 1024))],
    "sgn_cty_murano_01_a_xsummerx_bclr": [("村野 Murano", (0, 0, 1024, 1024))],
    "sgn_cty_open_01_a_xsummerx_bclr": [("営業中 mochi (open sign)", (0, 0, 1024, 1024))],
    "sgn_cty_phrmcy_neon_01_a_xsummerx_bclr": [("pharmacy neon 薬", (0, 0, 1024, 1024))],
    "sgn_cty_shop_02_a_xsummerx_bclr": [("PLACEHOLDER (shop sign 02)", (0, 0, 512, 512))],
    "sgn_cty_shop_03_a_xsummerx_bclr": [("PLACEHOLDER (shop sign 03)", (0, 0, 512, 512))],
    "sgn_cty_shop_horiz_01_a_xsummerx_bclr": [("そば処 江戸屋 (soba)", (0, 0, 1024, 1024))],
    "sgn_cty_shop_horiz_02_a_xsummerx_bclr": [("noren curtain with lantern", (0, 0, 512, 512))],
    "sgn_cty_shop_horiz_03_a_xsummerx_bclr": [("ラーメン勝 (ramen shop)", (0, 0, 1024, 1024))],
    "sgn_cty_shop_office_01_a_decal_xsummerx_bclr": [("office directory 穀物問屋 / 建材店", (0, 0, 512, 512))],
    "sgn_cty_shop_vert_01_a_xsummerx_bclr": [("イメ雅ラン (ramen, round lanterns)", (0, 0, 1024, 1024))],
    "sgn_cty_shop_vert_02_a_xsummerx_bclr": [("placeholder (vertical sign 02)", (0, 0, 512, 512))],
    "sgn_cty_tkmto_stshi_01_a_xsummerx_bclr": [("Takamoto Satoshi (shop sign)", (0, 0, 1024, 1024))],
    "sgn_cty_yamaya_01_a_xsummerx_bclr": [("山家 Yamaya", (0, 0, 1024, 1024))],
    "sgn_gbl_indu_01_a_xsummerx_bclr": [("駐車場 (parking)", (0, 0, 1024, 1024))],
    "prp_cty_vend_drinks_01_a_feature_xsummerx_bclr": [("drinks vending machine", (0, 0, 2048, 1024))],
    "prp_cty_vend_gacha_01_a_xsummerx_bclr": [("gacha capsule machine", (0, 0, 1024, 1024))],
    # ---------------------------------------------------------------- circuit / festival / event dressing
    "bar_gbl_crct_banner_01_a_atlas_bclr": rows(512, [0, 256, 512, 768], ["Irakuzu barrier banner", "Techsports Racing barrier banner", "Prorata Wheels barrier banner"]),
    "dec_fst_branding_atlas_a_xsummerx_bclr": [
        ("#fastertogether (Horizon)", (0, 0, 1138, 296)), ("Flowzoil", (1160, 23, 1991, 375)),
        ("sybil (white)", (0, 330, 933, 560)), ("sybil (black)", (0, 546, 933, 800)), ("sybil (red mark)", (0, 785, 933, 1035)),
        ("Horizon Festival logos", (956, 398, 2025, 1650)), ("Horizon Pulse (radio)", (11, 1058, 296, 1206)),
        ("Horizon XS (radio)", (671, 1047, 933, 1206)), ("Horizon Bass Arena (radio)", (159, 1229, 444, 1377)),
        ("Horizon Wave (radio)", (489, 1217, 808, 1377)), ("Horizon Block Party (radio)", (34, 1388, 307, 1593)),
        ("Horizon Opus (radio)", (626, 1422, 956, 1570)), ("Tomitama (red mark)", (0, 1638, 694, 2048)),
        ("Tomitama (white)", (705, 1638, 1365, 2048)), ("Tomitama (black)", (1388, 1638, 2048, 2048))],
    "inf_fst_tollbooth_01_a_posters_xsummerx_bclr": [("tollbooth poster: Tomitama", (0, 30, 341, 200)),
                                                     ("tollbooth poster: Flowzoil", (0, 200, 341, 350)),
                                                     ("tollbooth poster: sybil", (0, 350, 341, 512))],
    "inf_gbl_tent_crct_ezup_a_decal_a_bclr": [("Prorata Wheels gazebo tent", (0, 0, 1024, 512))],
    "inf_gbl_tent_crct_ezup_a_decal_b_bclr": [("Techsports Racing gazebo tent", (0, 0, 1024, 512))],
    "inf_gbl_tent_crct_ezup_a_decal_c_bclr": [("Irakuzu gazebo tent", (0, 0, 1024, 512))],
    "prp_fst_stalls_01_a_decal_xsummerx_bclr": [("ラーメン真 Ramen Shin food stall", (0, 0, 1024, 1024))],
    "prp_fst_stalls_02_a_decal_xsummerx_bclr": [("Nakaya 中家 food stall", (0, 0, 1024, 512))],
    "inf_cst_spce_tower_fuel_01_a_decal_bclr": [("H-IIA F6 rocket (space centre)", (0, 0, 1024, 1024))],
    "prp_gbl_crct_flag_01_a_feature_xsummerx_bclr": [("Raku Raku Express circuit flag", (0, 0, 300, 1024))],
    "prp_gbl_crct_flag_01_b_feature_xsummerx_bclr": [("DayTrip 日帰り旅行 circuit flag", (0, 0, 300, 1024))],
    "prp_gbl_crct_flag_01_f_feature_xsummerx_bclr": [("Drift Club Japan circuit flag", (0, 0, 300, 1024))],
    "prp_gbl_crct_flag_02_a_xsummerx_bclr": grid(2048, 1024, 8, 1, ["Irakuzu flag", None, "Techsports Racing flag", None, "Prorata Wheels flag"]),
    "prp_gbl_crct_flag_02_b_swatch_xsummerx_bclr": grid(2048, 1024, 8, 1, ["Techsports Racing flag", None, "Prorata Wheels flag"]),
    "prp_gbl_crct_flag_02_c_xsummerx_bclr": grid(2048, 1024, 8, 1, ["Prorata Wheels flag"]),
    "prp_gbl_flag_grassroute_01_a_atlas_bclr": grid(2048, 1024, 10, 1, ["そば処 大和屋 Yamato-ya flag", None, "turbopod flag", None,
                                                                        "Techsports Racing flag", None, "Nakaya 中家 flag", None, "Suzuta-ya 鈴田屋 flag"]),
    "prp_gbl_flag_stories_01_a_atlas_bclr": grid(2048, 1024, 12, 1, ["Yuji's Auto flag", None, "Techsports Racing flag", None,
                                                                     "Prorata Wheels flag", None, "Drift Club Japan flag (red)", None,
                                                                     "Drift Club Japan flag (black)", None, "Moto Auto flag"]),
    # ---------------------------------------------------------------- extra commercial sign sheets
    "tex_gbl_sgn_com_v_03_b_bclr": grid(1024, 512, 4, 1, ["お寿司 sushi poster", "お寿司 sushi poster (2)", "激辛ラーメン spicy ramen poster", "営業中 ラーメン (ramen, open)"]),
    "tex_gbl_sgn_com_v_04_a_bclr": grid(1024, 512, 3, 1, ["激辛ラーメン spicy ramen poster", "お寿司 sushi poster", "営業中 ラーメン (ramen, open)"]),
    "tex_gbl_sgn_com_v_03_d_bclr": grid(1024, 512, 4, 1, ["Horizon Festival poster", "Horizon Festival poster (2)", "Horizon Festival poster (3)"]),
    # ---------------------------------------------------------------- added 2026-10-10 (were untracked)
    "tex_gbl_sgn_com_h_03_a_bclr": rows(1024, [0, 140, 270, 365, 512], [
        "フードレストラン food restaurant (ink-mask colours)", "サンドイッチショップ sandwich shop (ink-mask colours)",
        "仕事場 workplace (ink-mask colours)", "玩具専門店 toy shop (ink-mask colours)"]),
    "gpy_gbl_shop_redlinemag_a_xsummerx_bclr": grid(512, 512, 3, 2, [
        "Moto Auto magazine: Sports Utility Heroes", "Moto Auto magazine: Hypercars", "Moto Auto magazine (3)",
        "Moto Auto magazine: Classic Muscle", "Moto Auto magazine: Cult Cars", "Moto Auto magazine: Retro Super Cars"]),
    "prp_gbl_stall_02_a_xsummerx_bclr": [("Moto Auto magazine rack covers", (0, 190, 420, 960))],
    "prp_gbl_cont_ship_lng_01_a_branding_bclr": [("container ship branding (Horizon + red logo)", (0, 0, 1024, 1024))],
}
