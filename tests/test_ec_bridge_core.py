# -*- coding: utf-8 -*-
"""ec_bridge_core の回帰テスト。

- ``ReconstructedOriginal*`` : 旧 EC_Bridge.py / EC_Bridge_for_kanme_nakano.py
  （コミット 3fe6c7c 時点）のロジックを関数として再現したもの。行番号は当時の
  ソースを指す。
- ``RegressionTests`` : 挙動を維持すべき部分が旧実装と一致することを確認する。
- ``IntentionalChangeTests`` : 全面書き直しで意図的に変えた挙動を固定する。
- ``PriceTagTests`` : 実物の値札テンプレートに対する出力を検証する。
- ``GuiSmokeTests`` : Tk を生成して画面遷移まわりを確認する（表示不可の環境では skip）。

実行: ``python -m unittest test_ec_bridge_core -v``
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(TESTS_DIR), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import ec_bridge_core as core          # noqa: E402
from ec_bridge_core import Item        # noqa: E402

REAL_TEMPLATE = os.path.join(SRC_DIR, "ネット用値札.ods")
SAMPLE_CSV = os.path.join(TESTS_DIR, "auctions_sample.csv")

# EC_Bridge.py / EC_Bridge_for_kanme_nakano.py が持つ差分（当時のソースより）
MEDAMAYA = dict(gui_size=" サイズ", gui_color=" ", web_size=" サイズ ", web_color=" ")
KANME = dict(gui_size=" サイズ: ", gui_color=" カラー: ",
             web_size=" サイズ: ", web_color=" カラー: ")


# ---------------------------------------------------------------------------
# 旧実装の再現
# ---------------------------------------------------------------------------

def orig_datetime_parts(year: int, month: int, day: int):
    """旧 Datetime() 相当（month/day を 10 未満のときだけゼロ埋め文字列に）。"""

    m = "0" + str(month) if month < 10 else month
    d = "0" + str(day) if day < 10 else day
    return year, m, d


def orig_management_number(shop_id: int, year: int, month: int, day: int, seq: int) -> int:
    # 旧 EC_Bridge.py L1006 / L1247
    y, m, d = orig_datetime_parts(year, month, day)
    return int(str(shop_id) + str(y % 100) + str(m) + str(d) + str(seq).zfill(3))


def orig_measurement_html(genre: str, m1: str, m2: str, m3: str, m4: str):
    # 旧 EC_Bridge.py add_to_input2 (L254-265 ほか)
    if genre == "トップス":
        return f"着丈:{m1}cm<BR>\n肩幅:{m2}cm<BR>\n身幅:{m3}cm<BR>\n袖丈:{m4}cm<BR>"
    if genre == "ボトムス":
        return f"ウエスト:{m1}cm<BR>\n股上:{m2}cm<BR>\n股下:{m3}cm<BR>\n裾幅:{m4}cm<BR>"
    if genre == "シューズ":
        return f"アウトソール:{m1}cm<BR>\n幅:{m2}cm<BR>"
    if genre == "バッグ":
        return f"横:{m1}cm<BR>\n縦:{m2}cm<BR>\nマチ:{m3}cm<BR>"
    if genre == "腕時計":
        return f"ケース縦:{m1}cm<BR>\nケース縦:{m2}cm<BR>\nベルト幅:{m3}cm<BR>"
    if genre == "その他":
        return "-"
    return None


def orig_tag_info(it: Item) -> str:
    # 旧 EC_Bridge.py calc (L1234-1245)
    c = ""
    if it.notated_size != "":
        c += "サイズ" + it.notated_size
    if it.tag_condition != "":
        c += "/" + re.sub(r"[ 　、]+", "/", it.tag_condition)
    if it.motion != "":
        c += "/" + it.motion
    if it.gender == "レディース":
        c += "/" + it.gender
    c += "/" + it.situation + "/オーク"
    return c


def orig_cond_medamaya(situation: str, ss_raw: str, motion: str, genre: str) -> str:
    # 旧 EC_Bridge.py update_s_text（各ジャンル / その他）
    ss = re.sub(r"[ 　]+", "、", ss_raw)
    if ss != "":
        ss = "と" + ss
    body = f"少々使用感{ss}はありますが、大きなダメージはなく中古並の状態です。"
    if genre == "その他" and motion != "":
        return f"{motion}です。{body}"
    return body


def orig_cond_kanme(situation: str, ss_raw: str, motion: str, genre: str) -> str:
    # 旧 EC_Bridge_for_kanme_nakano.py update_s_text
    ss = re.sub(r"[ 　]+", "、", ss_raw)
    if ss != "":
        ss = ss + "あり。"
    verb = "着用" if genre in ("トップス", "ボトムス") else "使用"
    body = f"{situation}。通常の{verb}に伴う状態。{ss}"
    if motion != "":
        return f"{motion}。{body}"
    return body


def orig_gui_title(it: Item, size_pfx: str, color_pfx: str) -> str:
    # 旧 update_t_text（ジャンル別クロージャ）
    genre_value = "" if it.genre == core.GENRE_PLACEHOLDER else it.genre
    text = f"{it.brand} {it.brand_kana} {it.name}"
    if it.notated_size != "":
        text += size_pfx + it.notated_size
    if it.color != "":
        text += color_pfx + it.color
    if it.situation != "中古品":
        text += " " + it.situation
    if genre_value == "その他":
        if it.motion != "":
            text += " " + it.motion
    else:
        text += " " + genre_value
    if genre_value in ("トップス", "ボトムス"):
        text += " " + it.gender
    return text


def orig_web_title(it: Item, size_pfx: str, color_pfx: str) -> str:
    # 旧 yahoo_auction a2 生成（L1004-1019）
    genre = "" if it.genre == "その他" else it.genre
    text = f"{it.brand} {it.brand_kana} {it.name}"
    if it.notated_size != "":
        text += size_pfx + it.notated_size
    if it.color != "":
        text += color_pfx + it.color
    if it.situation != "中古品":
        text += " " + it.situation
    if genre in ("トップス", "ボトムス"):
        if it.gender != "記入無し":     # 内部値は "" なので実質常に真
            text += " " + it.gender
    text += " " + genre
    return text


def orig_web_description(it: Item, shop_images: str) -> str:
    # 旧 yahoo_auction a3..a145（L1021-1034, L1107）
    a3 = ("<TABLE BORDER=1 WIDTH=700px CELLSPACING=4 CELLPADDING=10 BORDER=1> </TD> </TR> "
          "<TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>ランク付け</TD> <TD WIDTH=75%>\n")
    a4 = it.rank
    a5 = "\n</TD></TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>状態</TD> <TD WIDTH=75%>\n"
    a6 = f"{it.brand} {it.name}です。<BR>\n"
    a7 = it.condition_text + "<BR>\n"
    a8 = "<TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>表記サイズ</TD> <TD WIDTH=75%>\n"
    a9 = it.notated_size if it.notated_size != "" else "-"
    a10 = "\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>実寸サイズ</TD> <TD WIDTH=75%>\n"
    a11 = orig_measurement_html(it.genre, it.m1, it.m2, it.m3, it.m4)
    a12 = "\n</TD> </TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>カラー</TD> <TD WIDTH=75%>\n"
    a13 = it.color if it.color != "" else "-"
    a14 = ("\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>保管店舗</TD> <TD WIDTH=75%>"
           + it.shop + "</TD> </TR>  </TABLE>")
    joined = a3 + a4 + a5 + a6 + a7 + a8 + a9 + a10 + a11 + a12 + a13 + a14 + shop_images
    return joined.replace("\n", " ")   # 競りナビは説明列の改行を受け付けない


def orig_price_tag_cell(position: int):
    """旧 calc の分岐（L1251-1278）を (row, data_col, label_col) で返す。"""

    if position >= 16:
        r = (position - 16) * 7
        return r, 9, 10
    if position >= 11:
        r = (position - 11) * 7
        return r, 6, 7
    if position >= 6:
        r = (position - 6) * 7
        return r, 3, 4
    r = (position - 1) * 7
    return r, 0, 1


# ---------------------------------------------------------------------------
# サンプルデータ
# ---------------------------------------------------------------------------

def sample_item(**overrides) -> Item:
    base = dict(
        shop="上池袋", brand="ナイキ", brand_kana="ナイキ", name="スニーカー",
        color="黒", price="3000", gender="メンズ", genre="トップス",
        situation="美中古品", rank="B", rank2="やや傷や汚れあり",
        tag_condition="使用感 スレ", postage="700",
        notated_size="M", motion="", m1="60", m2="45", m3="50", m4="58",
    )
    base.update(overrides)
    it = Item(**base)
    return it


def medamaya_config():
    return core.make_config("上池袋")


def kanme_config():
    return core.make_config("中野")


# ---------------------------------------------------------------------------
# 回帰テスト
# ---------------------------------------------------------------------------

class RegressionTests(unittest.TestCase):

    def test_management_number_current_dates(self):
        for (y, m, d) in [(2026, 8, 28), (2026, 11, 5), (2027, 1, 1), (2026, 12, 31)]:
            for shop_id in (22, 11, 44):
                for seq in (1, 7, 42, 123):
                    got = core.management_number(shop_id, y, m, d, seq)
                    want = str(orig_management_number(shop_id, y, m, d, seq))
                    self.assertEqual(got, want, f"{shop_id}/{y}-{m}-{d}/{seq}")

    def test_tag_info_matches_original(self):
        cases = [
            dict(notated_size="M", tag_condition="使用感 スレ", motion="",
                 gender="メンズ", situation="美中古品"),
            dict(notated_size="", tag_condition="", motion="", gender="レディース",
                 situation="中古品"),
            dict(notated_size="27", tag_condition="黄ばみ　毛玉", motion="動作確認済み",
                 gender="レディース", situation="ジャンク品", genre="その他"),
            dict(notated_size="", tag_condition="スレ", motion="", gender="",
                 situation="現状品"),
        ]
        for c in cases:
            it = sample_item(**c)
            self.assertEqual(core.build_tag_info(it), orig_tag_info(it), c)

    def test_measurement_html_matches_original_except_watch(self):
        for genre in ["トップス", "ボトムス", "シューズ", "バッグ", "その他"]:
            it = sample_item(genre=genre)
            self.assertEqual(
                core.measurement_html(it),
                orig_measurement_html(genre, it.m1, it.m2, it.m3, it.m4),
                genre,
            )

    def test_condition_text_medamaya_matches_original(self):
        cfg = medamaya_config()
        cases = [
            ("美中古品", "使用感、スレ", "", "トップス"),
            ("中古品", "", "", "シューズ"),
            ("現状品", "黄ばみ、毛羽立ち", "動作確認済み", "その他"),
            ("ジャンク品", "", "通電未確認", "その他"),
            ("美中古品", "スレ", "動作確認済み", "バッグ"),   # 非その他は motion 無視
        ]
        for situation, note, motion, genre in cases:
            got = cfg.condition_text(situation, core.join_tag_note(note), motion, genre)
            want = orig_cond_medamaya(situation, note, motion, genre)
            self.assertEqual(got, want, (situation, note, motion, genre))

    def test_condition_text_kanme_matches_original(self):
        cfg = kanme_config()
        cases = [
            ("美中古品", "使用感、スレ", "", "トップス"),
            ("美中古品", "使用感", "", "ボトムス"),
            ("中古品", "", "", "シューズ"),
            ("現状品", "黄ばみ", "動作確認済み", "その他"),
            ("稼働品", "", "簡易動作確認済み", "腕時計"),
        ]
        for situation, note, motion, genre in cases:
            got = cfg.condition_text(situation, core.join_tag_note(note), motion, genre)
            want = orig_cond_kanme(situation, note, motion, genre)
            self.assertEqual(got, want, (situation, note, motion, genre))

    def test_price_tag_cell_placement_matches_original(self):
        for position in range(1, core.ITEMS_PER_SHEET + 1):
            row, data_col = core._price_tag_block(position)
            o_row, o_col, o_label = orig_price_tag_cell(position)
            self.assertEqual((row, data_col, data_col + 1),
                             (o_row, o_col, o_label), position)

    def test_gui_title_matches_original_for_selected_genre(self):
        for cfg_key, cfg in (("M", medamaya_config()), ("K", kanme_config())):
            pfx = MEDAMAYA if cfg_key == "M" else KANME
            for genre in ["トップス", "ボトムス", "シューズ", "バッグ", "腕時計"]:
                for gender in ["メンズ", "レディース"]:
                    for situation in ["中古品", "美中古品"]:
                        it = sample_item(genre=genre, gender=gender, situation=situation)
                        got = core.build_title(it, cfg, web=False)
                        want = orig_gui_title(it, pfx["gui_size"], pfx["gui_color"])
                        self.assertEqual(got, want, (cfg_key, genre, gender, situation))

    def test_gui_title_other_with_motion_matches_original(self):
        for cfg_key, cfg in (("M", medamaya_config()), ("K", kanme_config())):
            pfx = MEDAMAYA if cfg_key == "M" else KANME
            it = sample_item(genre="その他", motion="動作確認済み", gender="")
            got = core.build_title(it, cfg, web=False)
            want = orig_gui_title(it, pfx["gui_size"], pfx["gui_color"])
            self.assertEqual(got, want, cfg_key)

    def test_web_title_matches_original_when_gender_set(self):
        for cfg_key, cfg in (("M", medamaya_config()), ("K", kanme_config())):
            pfx = MEDAMAYA if cfg_key == "M" else KANME
            for genre in ["トップス", "ボトムス"]:
                for gender in ["メンズ", "レディース"]:
                    it = sample_item(genre=genre, gender=gender, situation="美中古品")
                    got = core.build_title(it, cfg, web=True)
                    want = orig_web_title(it, pfx["web_size"], pfx["web_color"])
                    self.assertEqual(got, want, (cfg_key, genre, gender))

    def test_web_title_matches_original_for_non_apparel(self):
        for cfg_key, cfg in (("M", medamaya_config()), ("K", kanme_config())):
            pfx = MEDAMAYA if cfg_key == "M" else KANME
            for genre in ["シューズ", "バッグ", "腕時計"]:
                it = sample_item(genre=genre, situation="美中古品")
                got = core.build_title(it, cfg, web=True)
                want = orig_web_title(it, pfx["web_size"], pfx["web_color"])
                self.assertEqual(got, want, (cfg_key, genre))

    def test_web_description_matches_original(self):
        cfg_m = medamaya_config()
        for genre in ["トップス", "シューズ", "その他"]:
            it = sample_item(genre=genre, situation="美中古品")
            it.condition_text = cfg_m.condition_text(
                it.situation, core.join_tag_note(it.tag_condition), it.motion, it.genre)
            got = core.build_web_description(it, cfg_m)
            want = orig_web_description(it, core.SHOPS[it.shop].images)
            self.assertEqual(got, want, genre)

    def test_web_description_kanme_nakano_image_override(self):
        cfg_k = kanme_config()
        it = sample_item(shop="中野", genre="バッグ")
        it.condition_text = "x"
        got = core.build_web_description(it, cfg_k)
        want = orig_web_description(it, cfg_k.shop("中野").images)
        self.assertEqual(got, want)
        self.assertIn("rank.jpg", got)

    def test_shop_ids_consistent(self):
        self.assertEqual({n: core.SHOPS[n].shop_id for n in core.SHOP_NAMES},
                         {"上池袋": 22, "要町": 11, "中野": 44})

    def test_join_tag_note_no_surrounding_space(self):
        self.assertEqual(core.join_tag_note("使用感 スレ"), "使用感、スレ")
        self.assertEqual(core.join_tag_note("黄ばみ　毛玉"), "黄ばみ、毛玉")


# ---------------------------------------------------------------------------
# 意図的に変えた挙動
# ---------------------------------------------------------------------------

class IntentionalChangeTests(unittest.TestCase):

    def test_watch_measurement_label_fixed(self):
        """腕時計の実寸: 旧「ケース縦」二重表記 -> 「ケース縦 / ケース横」。"""

        it = sample_item(genre="腕時計")
        self.assertEqual(
            core.measurement_html(it),
            f"ケース縦:{it.m1}cm<BR>\nケース横:{it.m2}cm<BR>\nベルト幅:{it.m3}cm<BR>",
        )
        self.assertNotEqual(
            core.measurement_html(it),
            orig_measurement_html("腕時計", it.m1, it.m2, it.m3, it.m4),
        )

    def test_titles_no_stray_space_when_gender_blank(self):
        """性別「記入無し」でも余分な空白を出さない（旧版は空白が入っていた）。"""

        cfg = medamaya_config()
        it = sample_item(genre="トップス", gender="", situation="中古品")
        for web in (True, False):
            title = core.build_title(it, cfg, web=web)
            self.assertNotIn("  ", title)
            self.assertFalse(title.endswith(" "))
            self.assertTrue(title.endswith("トップス"))

    def test_web_title_other_includes_motion(self):
        """その他 + 動作確認は Web タイトルにも出す（旧版は欠落＋末尾空白）。"""

        cfg = medamaya_config()
        it = sample_item(genre="その他", motion="動作確認済み", gender="", situation="中古品")
        self.assertTrue(core.build_title(it, cfg, web=True).endswith("動作確認済み"))

    def test_management_number_zero_pads_old_years(self):
        """2010 年より前でも桁が崩れない（旧版は年下2桁が1桁になり得た）。"""

        self.assertEqual(core.management_number(22, 2007, 3, 4, 1), "22070304001")
        # 旧実装は str(2007 % 100) == "7" で年が1桁になり、桁数が崩れていた
        self.assertNotEqual(str(orig_management_number(22, 2007, 3, 4, 1)),
                            core.management_number(22, 2007, 3, 4, 1))

    def test_price_tags_written_to_fixed_name_and_overwrites(self):
        """テンプレートは触らず、output/ネット用値札.ods を毎回上書き更新する。"""

        import ezodf
        before = os.path.getmtime(REAL_TEMPLATE)
        out_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(out_dir, ignore_errors=True))

        out1 = core.write_price_tags([sample_item(brand="一回目")],
                                     medamaya_config(), out_dir)
        self.assertEqual(os.path.basename(out1), "ネット用値札.ods")
        self.assertEqual(os.path.dirname(out1), out_dir)
        self.assertNotEqual(os.path.abspath(out1), os.path.abspath(REAL_TEMPLATE))
        self.assertEqual(os.path.getmtime(REAL_TEMPLATE), before)  # テンプレは不変

        out2 = core.write_price_tags([sample_item(brand="二回目")],
                                     medamaya_config(), out_dir)
        self.assertEqual(out1, out2)                               # 同じパス
        self.assertEqual(ezodf.opendoc(out2).sheets[0][0, 0].value, "二回目")
        self.assertEqual(sorted(os.listdir(out_dir)), ["ネット用値札.ods"])  # .bak 無し


# ---------------------------------------------------------------------------
# 値札出力（実テンプレート / 合成テンプレート）
# ---------------------------------------------------------------------------

def make_template_file(path: str, sheet_count: int) -> str:
    """指定枚数の空シートを持つ値札テンプレートを作る。"""

    import ezodf

    doc = ezodf.newdoc(doctype="ods", filename=path)
    for i in range(sheet_count):
        doc.sheets += ezodf.Sheet(f"S{i}", size=(40, 12))
    doc.save()
    return path


class PriceTagTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            import ezodf  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"ezodf 未インストール: {exc}")
        import ezodf
        if not os.path.isfile(REAL_TEMPLATE):
            raise unittest.SkipTest("値札テンプレートが無い")
        cls.sheet_count = len(ezodf.opendoc(REAL_TEMPLATE).sheets)

    def _tmpdir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        return d

    def _write(self, items, config, template=None, out_dir=None):
        out = core.write_price_tags(items, config, out_dir or self._tmpdir(),
                                    template_path=template or REAL_TEMPLATE)
        self.addCleanup(lambda: os.path.exists(out) and os.remove(out))
        return out

    def _synthetic_template(self, sheet_count, config):
        return make_template_file(
            os.path.join(self._tmpdir(), config.price_tag_filename), sheet_count)

    def test_single_item_cells(self):
        import ezodf
        it = sample_item(shop="中野", brand="ブランドA", name="商品名 テスト",
                         price="12800", notated_size="L", rank="AB")
        out = self._write([it], medamaya_config())
        sheet = ezodf.opendoc(out).sheets[0]
        self.assertEqual(sheet[0, 0].value, "ブランドA")
        self.assertEqual(int(sheet[1, 0].value),
                         int(core.management_number(44, *core.today_ymd(), 1)))
        self.assertEqual(int(sheet[2, 0].value), 12800)
        self.assertEqual(sheet[2, 1].value, "AB")
        self.assertEqual(sheet[4, 0].value, "商品名/テスト")
        self.assertEqual(sheet[5, 0].value, core.build_tag_info(it))

    def test_positions_span_four_columns(self):
        import ezodf
        items = [sample_item(brand=f"B{i}", name=f"N{i}", price=str(1000 + i))
                 for i in range(12)]
        out = self._write(items, medamaya_config())
        sheet = ezodf.opendoc(out).sheets[0]
        # 6件目 -> 位置6 -> row0,col3 ; 11件目 -> 位置11 -> row0,col6
        self.assertEqual(sheet[0, 3].value, "B5")
        self.assertEqual(sheet[0, 6].value, "B10")
        self.assertEqual(sheet[7, 0].value, "B1")   # 2件目 -> 位置2 -> row7,col0

    def test_multi_sheet_split(self):
        import ezodf
        for cfg in (medamaya_config(), kanme_config()):
            tpl = self._synthetic_template(3, cfg)
            items = [sample_item(brand=f"B{i}", name=f"N{i}", price="100")
                     for i in range(core.ITEMS_PER_SHEET + 3)]
            out = self._write(items, cfg, template=tpl)
            doc = ezodf.opendoc(out)
            self.assertEqual(doc.sheets[0][0, 0].value, "B0", cfg.name)
            self.assertEqual(doc.sheets[1][0, 0].value,        # 21件目は2タブ目の先頭
                             f"B{core.ITEMS_PER_SHEET}", cfg.name)
            self.assertIsNone(doc.sheets[2][0, 0].value, cfg.name)

    def test_both_variants_start_from_first_tab(self):
        import ezodf
        for cfg in (medamaya_config(), kanme_config()):
            tpl = self._synthetic_template(2, cfg)
            out = self._write([sample_item(brand="FIRST", price="100")], cfg,
                              template=tpl)
            doc = ezodf.opendoc(out)
            self.assertEqual(doc.sheets[0][0, 0].value, "FIRST", cfg.name)

    def test_capacity_is_tabs_times_20(self):
        import ezodf
        cfg = medamaya_config()
        tpl = self._synthetic_template(2, cfg)
        items = [sample_item(brand=f"B{i}", price="100")
                 for i in range(2 * core.ITEMS_PER_SHEET)]        # ちょうど40件
        out = self._write(items, cfg, template=tpl)
        doc = ezodf.opendoc(out)
        self.assertEqual(doc.sheets[1][4 * 7, 9].value, "B39")   # 40件目=2タブ目の20番目

    def test_sheet_shortage_raises_with_helpful_message(self):
        cfg = medamaya_config()
        tpl = self._synthetic_template(1, cfg)
        too_many = [sample_item(price="100") for _ in range(core.ITEMS_PER_SHEET + 1)]
        with self.assertRaises(ValueError) as ctx:
            core.write_price_tags(too_many, cfg, self._tmpdir(), template_path=tpl)
        self.assertIn("タブを1つ追加", str(ctx.exception))


# ---------------------------------------------------------------------------
# GUI スモーク
# ---------------------------------------------------------------------------

def _new_app(testcase, config):
    """一時ディレクトリを出力先・設定先に使う EcBridgeApp を作る。"""

    import shutil
    tmp = tempfile.mkdtemp()
    testcase.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
    testcase.tmp_dir = tmp
    return core.EcBridgeApp(testcase.root, config, out_dir=tmp, settings_dir=tmp)


class GuiSmokeTests(unittest.TestCase):

    def setUp(self):
        import tkinter as tk
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"Tk 利用不可: {exc}")
        self.root.withdraw()
        self.app = _new_app(self, medamaya_config())
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def _fill(self, **kw):
        setters = {
            "brand": self.app.v_brand, "name": self.app.v_name,
            "price": self.app.v_price, "genre": self.app.v_genre,
            "color": self.app.v_color, "gender": self.app.v_gender,
            "notated": self.app.v_notated, "m1": self.app.v_m1, "m2": self.app.v_m2,
        }
        for key, value in kw.items():
            setters[key].set(value)
        self.root.update()

    def test_next_saves_and_advances(self):
        self._fill(brand="A", price="1000", genre="トップス", m1="60")
        self.app.on_next()
        self.assertEqual(len(self.app.items), 1)
        self.assertEqual(self.app.index, 1)
        self.assertEqual(self.app.v_counter.get(), "2/2")

    def test_validation_blocks_next(self):
        self._fill(brand="A", price="abc", genre="トップス")
        self.app.on_next()
        self.assertEqual(self.app.items, [])
        self.assertEqual(self.app.v_error.get(), "値段を入力してください")
        self._fill(price="1000", genre=core.GENRE_PLACEHOLDER)
        self.app.on_next()
        self.assertEqual(self.app.v_error.get(), "ジャンルを選択してください")

    def test_price_field_rejects_non_digits(self):
        e = self.app.price_entry
        self.assertEqual(e.cget("validate"), "key")
        e.insert("end", "12")
        e.insert("end", "abc")          # 拒否
        e.insert("end", "３")            # 全角も拒否
        e.insert("end", "5")
        self.root.update()
        self.assertEqual(self.app.v_price.get(), "125")
        self.app.v_price.set("999")     # プログラムからの設定（データ読込）は通る
        self.assertEqual(self.app.v_price.get(), "999")

    def test_prev_from_blank_new_slot_creates_no_phantom(self):
        self._fill(brand="A", price="1000", genre="トップス")
        self.app.on_next()
        self._fill(brand="B", price="2000", genre="バッグ")
        self.app.on_next()                       # 新規空スロットへ
        self.assertEqual(len(self.app.items), 2)
        self.app.on_prev()
        self.app.on_prev()
        self.assertEqual(len(self.app.items), 2)  # 幽霊アイテムが増えない
        self.assertEqual(self.app.v_brand.get(), "A")

    def test_edit_existing_item_persists(self):
        self._fill(brand="A", price="1000", genre="トップス")
        self.app.on_next()
        self._fill(brand="B", price="2000", genre="バッグ")
        self.app.on_next()
        self.app.on_prev()                       # -> B
        self._fill(brand="B2")
        self.app.on_prev()                       # -> A（Bを保存）
        self.app.on_next()                       # -> B2
        self.assertEqual(self.app.v_brand.get(), "B2")
        self.assertEqual(len(self.app.items), 2)

    def test_delete_removes_current(self):
        for brand, genre in [("A", "トップス"), ("B", "バッグ"), ("C", "シューズ")]:
            self._fill(brand=brand, price="100", genre=genre)
            self.app.on_next()
        self.app.on_prev()          # -> C (index 2)
        self.app.on_prev()          # -> B (index 1)
        self.app.on_delete()
        self.assertEqual([i.brand for i in self.app.items], ["A", "C"])

    def test_delete_with_no_items_shows_error(self):
        self.app.on_delete()
        self.assertEqual(self.app.v_error.get(), "削除するデータが存在しません")

    def test_measurement_panel_rebuilds_on_genre_change(self):
        self._fill(genre="トップス")
        self.assertTrue(any(isinstance(w, __import__("tkinter").ttk.Entry)
                            for w in self.app._measure_widgets))
        count_tops = len(self.app._measure_widgets)
        self._fill(genre="シューズ")
        self.assertLess(len(self.app._measure_widgets), count_tops)
        self._fill(genre="その他")
        widgets = self.app._measure_widgets
        self.assertTrue(any(isinstance(w, __import__("tkinter").ttk.Combobox)
                            for w in widgets))

    def test_roundtrip_preserves_measurements(self):
        self._fill(brand="A", price="1000", genre="トップス",
                   notated="M", m1="60", m2="45")
        self.app.on_next()
        self._fill(brand="B", price="2000", genre="ボトムス", m1="80")
        self.app.on_next()
        self.app.on_prev()
        self.app.on_prev()                       # -> item A
        self.assertEqual(self.app.v_genre.get(), "トップス")
        self.assertEqual(self.app.v_m1.get(), "60")
        self.assertEqual(self.app.v_m2.get(), "45")
        self.assertEqual(self.app.v_notated.get(), "M")

    def test_title_and_counter_update(self):
        self._fill(brand="ナイキ", name="Tシャツ", genre="トップス", gender="メンズ",
                   price="1000", notated="M")
        self.assertIn("ナイキ", self.app.v_title.get())
        self.assertIn("トップス", self.app.v_title.get())
        self.assertTrue(self.app.v_charcount.get().startswith("文字数:"))

    def test_settings_roundtrip(self):
        path = self.app.settings_path
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.app.v_shop.set("要町")
        self.root.update()
        self.assertEqual(core.load_settings(path).get("last_shop"), "要町")


# ---------------------------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------------------------

class HelperTests(unittest.TestCase):

    def test_is_digits_or_empty(self):
        for ok in ("", "0", "5", "1234", "00", "999999"):
            self.assertTrue(core._is_digits_or_empty(ok), ok)
        for ng in ("a", "12a", "-5", "1.5", "1,000", " 1", "1 ", "１２３", "５", "٣"):
            self.assertFalse(core._is_digits_or_empty(ng), ng)

    def test_title_length_counts_fullwidth_1_halfwidth_half(self):
        self.assertEqual(core.title_length("あいう"), 3.0)
        self.assertEqual(core.title_length("abcd"), 2.0)
        self.assertEqual(core.title_length("あ a"), 1.0 + 0.5 + 0.5)
        self.assertEqual(core.title_length(""), 0.0)

    def test_title_length_matches_old_ord_rule_for_common_text(self):
        def old(text):
            return sum(1 if ord(ch) > 255 else 0.5 for ch in text)
        for sample in ["ナイキ スニーカー 黒 M トップス メンズ",
                       "Supreme Box Logo Tee White L"]:
            self.assertEqual(core.title_length(sample), old(sample), sample)

    def test_join_tag_note_collapses_runs_and_trims(self):
        self.assertEqual(core.join_tag_note("  使用感   スレ　　毛玉 "), "使用感、スレ、毛玉")
        self.assertEqual(core.join_tag_note(""), "")
        self.assertEqual(core.join_tag_note("キズ"), "キズ")

    def test_management_number_is_str(self):
        self.assertIsInstance(core.management_number(22, 2026, 8, 28, 1), str)

    def test_item_defaults(self):
        it = Item()
        self.assertEqual(it.genre, core.GENRE_PLACEHOLDER)
        self.assertEqual(it.situation, "中古品")
        self.assertEqual(it.rank, "C")
        self.assertEqual(it.rank2, "目立った傷や汚れなし")
        self.assertEqual(it.postage, "700")
        self.assertEqual(it.measurement_values(), ["", "", "", ""])

    def test_measurement_html_unknown_and_other_is_dash(self):
        self.assertEqual(core.measurement_html(sample_item(genre="その他")), "-")
        self.assertEqual(core.measurement_html(sample_item(genre=core.GENRE_PLACEHOLDER)), "-")

    def test_paths_point_at_src_and_output(self):
        self.assertEqual(core.SRC_DIR, SRC_DIR)
        self.assertEqual(os.path.basename(core.default_output_dir()), "output")
        self.assertTrue(core.default_template_path(medamaya_config())
                        .endswith(os.path.join("src", "ネット用値札.ods")))
        # 設定は exe(=PROJECT_DIR) の隣、出力先ではない
        self.assertEqual(os.path.dirname(core.settings_file_path(medamaya_config())),
                         core.PROJECT_DIR)


# ---------------------------------------------------------------------------
# 設定ファイル
# ---------------------------------------------------------------------------

class SettingsTests(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.path = os.path.join(tempfile.mkdtemp(), "x_settings.json")

    def test_missing_file_returns_empty_dict(self):
        self.assertEqual(core.load_settings(self.path), {})

    def test_roundtrip(self):
        core.save_settings(self.path, {"last_shop": "中野"})
        self.assertEqual(core.load_settings(self.path), {"last_shop": "中野"})

    def test_corrupt_json_returns_empty_dict(self):
        with open(self.path, "w", encoding="utf-8") as fp:
            fp.write("{ this is not json ")
        self.assertEqual(core.load_settings(self.path), {})

    def test_non_object_json_returns_empty_dict(self):
        with open(self.path, "w", encoding="utf-8") as fp:
            fp.write("[1, 2, 3]")
        self.assertEqual(core.load_settings(self.path), {})

    def test_settings_filename_uses_config_name(self):
        self.assertEqual(
            core.settings_file_path(medamaya_config(), "/base"),
            os.path.join("/base", "EC_Bridge_settings.json"))
        # 省略時は exe の隣（PROJECT_DIR）
        self.assertEqual(os.path.dirname(core.settings_file_path(medamaya_config())),
                         core.PROJECT_DIR)

    def test_make_config_variant_by_shop(self):
        self.assertEqual(core.make_config("上池袋").condition_text,
                         core.medamaya_condition_text)
        for shop in ("要町", "中野"):
            cfg = core.make_config(shop)
            self.assertEqual(cfg.condition_text, core.kanme_condition_text)
            self.assertEqual(cfg.default_shop, shop)
            self.assertEqual(cfg.gui_size_prefix, " サイズ: ")
        # 中野は画像差し替えあり、上池袋・要町は無し
        self.assertIn("rank.jpg", core.make_config("中野").shop("中野").images)
        self.assertIn("ranku.jpg", core.make_config("上池袋").shop("中野").images)
        # 不正な店舗名は上池袋にフォールバック
        self.assertEqual(core.make_config("架空店").default_shop, "上池袋")


# ---------------------------------------------------------------------------
# マスタ定数（旧ソースの値と一致するか）
# ---------------------------------------------------------------------------

class MasterDataTests(unittest.TestCase):

    def test_shop_master_matches_original(self):
        expected = {
            "上池袋": dict(shop_id=22, store_keyword="上池袋店 XXX", city="豊島区",
                          prefecture_name="東京都", folder_path="新NEW上池袋在庫"),
            "要町": dict(shop_id=11, store_keyword="要町店 XXX", city="豊島区",
                        prefecture_name="東京都", folder_path="新NEW要町在庫"),
            "中野": dict(shop_id=44, store_keyword="中野店 XXX", city="中野区",
                        prefecture_name="東京都", folder_path="新NEW中野店在庫"),
        }
        for name, want in expected.items():
            spec = core.SHOPS[name]
            self.assertEqual(spec.shop_id, want["shop_id"], name)
            self.assertEqual(spec.store_keyword, want["store_keyword"], name)
            self.assertEqual(spec.city, want["city"], name)
            self.assertEqual(spec.prefecture_name, want["prefecture_name"], name)
            self.assertEqual(spec.folder_path, want["folder_path"], name)

    def test_condition_csv_map_covers_all_rank2(self):
        self.assertEqual(set(core.YAHOO_CONDITION_CSV), set(core.RANK2S))
        self.assertEqual(core.YAHOO_CONDITION_CSV["未使用品"], "未使用")
        self.assertEqual(core.YAHOO_CONDITION_CSV["未使用品に近い"], "未使用に近い")
        self.assertEqual(core.YAHOO_CONDITION_CSV["傷や汚れあり"], "傷や汚れあり")

    def test_delivery_group_mapping(self):
        self.assertEqual(core.AUCTION_DELIVERY_GROUP, {"700": "1", "2000": "2"})
        self.assertEqual(set(core.AUCTION_DELIVERY_GROUP), set(core.POSTAGES))

    def test_genre_measurements_keys(self):
        self.assertEqual(set(core.GENRE_MEASUREMENTS), set(core.GENRES))
        self.assertEqual(core.GENRE_MEASUREMENTS["その他"], [])
        self.assertEqual(len(core.GENRE_MEASUREMENTS["トップス"]), 4)
        self.assertEqual(len(core.GENRE_MEASUREMENTS["シューズ"]), 2)

    def test_option_lists_match_original(self):
        self.assertEqual(core.RANKS, ["A", "AB", "B", "BC", "C", "CD", "D", "DE", "E"])
        self.assertEqual(core.SITUATIONS[5], "中古品")
        self.assertEqual(core.MOTIONS[0], "")
        self.assertIn("動作確認済み", core.MOTIONS)

    def test_csv_header_is_53_columns(self):
        self.assertEqual(len(core.AUCTION_CSV_HEADER), 53)
        self.assertEqual(core.AUCTION_CSV_HEADER[0], "管理番号")
        self.assertEqual(core.AUCTION_CSV_HEADER[-1], "発送までの日数")
        self.assertEqual(core.AUCTION_CSV_HEADER[50], "商品保存先フォルダパス")


# ---------------------------------------------------------------------------
# 商品説明の端条件
# ---------------------------------------------------------------------------

class DescriptionEdgeTests(unittest.TestCase):

    def test_dash_fallback_for_empty_notated_and_color(self):
        it = sample_item(genre="その他", notated_size="", color="", motion="")
        it.condition_text = "x"
        html = core.build_web_description(it, medamaya_config())
        self.assertIn("表記サイズ</TD> <TD WIDTH=75%> - ", html)
        self.assertIn("カラー</TD> <TD WIDTH=75%> - ", html)

    def test_description_has_no_newlines(self):
        """競りナビの一括アップロードは説明列の改行を弾くため、1物理行にする。"""

        it = sample_item(genre="トップス")
        it.condition_text = "x"
        self.assertNotIn("\n", core.build_web_description(it, medamaya_config()))

    def test_condition_and_brand_line_present(self):
        it = sample_item(genre="トップス", brand="ブランド", name="品名")
        it.condition_text = "状態テキスト"
        html = core.build_web_description(it, medamaya_config())
        self.assertIn("ブランド 品名です。<BR> 状態テキスト<BR> ", html)

    def test_tag_info_leading_slash_when_size_empty(self):
        it = sample_item(notated_size="", tag_condition="スレ", motion="", gender="",
                         situation="中古品")
        self.assertEqual(core.build_tag_info(it), "/スレ/中古品/オーク")


# ---------------------------------------------------------------------------
# GUI 追加
# ---------------------------------------------------------------------------

class GuiExtraTests(unittest.TestCase):

    def setUp(self):
        import tkinter as tk
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"Tk 利用不可: {exc}")
        self.root.withdraw()
        self.app = _new_app(self, medamaya_config())
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_prev_at_first_shows_error(self):
        self.app.on_prev()
        self.assertEqual(self.app.v_error.get(), "前のデータは存在しません")

    def test_clear_fields_resets_defaults(self):
        self.app.v_brand.set("A")
        self.app.v_genre.set("シューズ")
        self.app.v_situation.set("ジャンク品")
        self.root.update()
        self.app._clear_fields()
        self.assertEqual(self.app.v_brand.get(), "")
        self.assertEqual(self.app.v_genre.get(), core.GENRE_PLACEHOLDER)
        self.assertEqual(self.app.v_situation.get(), "中古品")
        self.assertEqual(self.app.v_rank.get(), "C")

    def test_condition_recomputes_on_situation_change(self):
        self.app.v_genre.set("トップス")
        self.app.v_situation.set("美中古品")
        self.app.v_tag_condition.set("使用感")
        self.root.update()
        self.assertEqual(
            self.app.v_condition.get(),
            "少々使用感と使用感はありますが、大きなダメージはなく中古並の状態です。")

    def test_char_count_value(self):
        self.app.v_brand.set("")
        self.app.v_brand_kana.set("")
        self.app.v_name.set("あいう")   # 全角3 + 半角スペース2(base の空白) = 4.0
        self.root.update()
        self.assertEqual(self.app.v_charcount.get(), "文字数: 4.0/65")

    def test_other_genre_shows_motion_combobox_not_measurements(self):
        import tkinter.ttk as ttk
        self.app.v_genre.set("その他")
        self.root.update()
        kinds = [type(w).__name__ for w in self.app._measure_widgets]
        self.assertIn("Combobox", kinds)
        self.assertNotIn("cm", [getattr(w, "cget", lambda *_: "")("text")
                                for w in self.app._measure_widgets if isinstance(w, ttk.Label)])

    def test_web_title_via_collect(self):
        self.app.v_brand.set("ナイキ")
        self.app.v_name.set("スニーカー")
        self.app.v_genre.set("シューズ")
        self.app.v_price.set("3000")
        self.root.update()
        it = self.app._collect()
        self.assertEqual(core.build_title(it, self.app.config, web=True),
                         "ナイキ  スニーカー シューズ")

    def test_delete_middle_keeps_others_in_order(self):
        for b, g in [("A", "トップス"), ("B", "バッグ"), ("C", "シューズ"), ("D", "腕時計")]:
            self.app.v_brand.set(b)
            self.app.v_price.set("100")
            self.app.v_genre.set(g)
            self.root.update()
            self.app.on_next()
        self.app.on_prev()   # D
        self.app.on_prev()   # C
        self.app.on_prev()   # B
        self.app.on_delete()
        self.assertEqual([i.brand for i in self.app.items], ["A", "C", "D"])


# ---------------------------------------------------------------------------
# GUI: 実寸パネル（全ジャンル）
# ---------------------------------------------------------------------------

class _GuiBase(unittest.TestCase):
    config_factory = staticmethod(medamaya_config)

    def setUp(self):
        import tkinter as tk
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"Tk 利用不可: {exc}")
        self.root.withdraw()
        self.app = _new_app(self, self.config_factory())
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def entries(self):
        import tkinter.ttk as ttk
        return [w for w in self.app._measure_widgets
                if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]

    def labels(self):
        import tkinter.ttk as ttk
        return [w.cget("text") for w in self.app._measure_widgets
                if isinstance(w, ttk.Label)]

    def comboboxes(self):
        import tkinter.ttk as ttk
        return [w for w in self.app._measure_widgets if isinstance(w, ttk.Combobox)]


class GuiMeasurementPanelTests(_GuiBase):

    EXPECT = {
        "選択してください": (1, [], 0),
        "トップス": (5, ["着丈:", "肩幅:", "身幅:", "袖丈:"], 0),
        "ボトムス": (5, ["ウエスト:", "股上:", "股下:", "裾幅:"], 0),
        "シューズ": (3, ["アウトソール全長:", "幅:"], 0),
        "バッグ": (4, ["横:", "縦:", "マチ:"], 0),
        "腕時計": (4, ["ケース縦:", "ケース横:", "ベルト幅:"], 0),
        "その他": (1, [], 1),
    }

    def test_every_genre_builds_expected_panel(self):
        for genre, (n_entries, want_labels, n_combo) in self.EXPECT.items():
            self.app.v_genre.set(genre)
            self.root.update()
            self.assertEqual(len(self.entries()), n_entries, genre)
            self.assertEqual(len(self.comboboxes()), n_combo, genre)
            for lbl in want_labels:
                self.assertIn(lbl, self.labels(), f"{genre}: {lbl}")

    def test_notated_size_field_always_present(self):
        for genre in self.EXPECT:
            self.app.v_genre.set(genre)
            self.root.update()
            self.assertIn("表記サイズ", self.labels(), genre)

    def test_measurement_values_retained_across_genre_switch(self):
        self.app.v_genre.set("トップス")
        self.root.update()
        for var, val in [(self.app.v_m1, "60"), (self.app.v_m2, "45"),
                         (self.app.v_m3, "50"), (self.app.v_m4, "58"),
                         (self.app.v_notated, "M")]:
            var.set(val)
        self.app.v_genre.set("バッグ")     # m4 欄は消える
        self.root.update()
        self.app.v_genre.set("トップス")   # 戻す
        self.root.update()
        self.assertEqual(
            [self.app.v_m1.get(), self.app.v_m2.get(),
             self.app.v_m3.get(), self.app.v_m4.get(), self.app.v_notated.get()],
            ["60", "45", "50", "58", "M"])

    def test_hidden_measurement_still_collected(self):
        self.app.v_genre.set("トップス")
        self.app.v_m4.set("58")
        self.root.update()
        self.app.v_genre.set("シューズ")   # m3/m4 欄は無い
        self.app.v_price.set("100")
        self.root.update()
        self.app.on_next()
        self.assertEqual(self.app.items[0].m4, "58")


# ---------------------------------------------------------------------------
# GUI: すべての選択肢が状態・派生出力に反映されるか
# ---------------------------------------------------------------------------

class GuiChoiceReflectionTests(_GuiBase):

    def _collect(self):
        self.root.update()
        return self.app._collect()

    def test_all_shops_selectable_and_saved(self):
        path = self.app.settings_path
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        for shop in core.SHOP_NAMES:
            self.app.v_shop.set(shop)
            self.assertEqual(self._collect().shop, shop)
            self.assertEqual(core.load_settings(path).get("last_shop"), shop)

    def test_all_genders_reflected_in_title(self):
        self.app.v_brand.set("A")
        self.app.v_genre.set("トップス")
        for gender, ends in [("メンズ", "トップス メンズ"),
                             ("レディース", "トップス レディース"),
                             ("", "トップス")]:
            self.app.v_gender.set(gender)
            self.root.update()
            self.assertTrue(self.app.v_title.get().endswith(ends), gender)

    def test_all_postage_values_collected(self):
        for postage in core.POSTAGES:
            self.app.v_postage.set(postage)
            self.assertEqual(self._collect().postage, postage)

    def test_all_ranks_collected(self):
        for rank in core.RANKS:
            self.app.v_rank.set(rank)
            self.assertEqual(self._collect().rank, rank)

    def test_all_rank2_values_collected(self):
        for rank2 in core.RANK2S:
            self.app.v_rank2.set(rank2)
            self.assertEqual(self._collect().rank2, rank2)

    def test_all_situations_reflected_in_title_and_condition(self):
        self.app.v_brand.set("A")
        self.app.v_genre.set("トップス")
        for situation in core.SITUATIONS:
            self.app.v_situation.set(situation)
            self.root.update()
            title = self.app.v_title.get()
            if situation == "中古品":
                self.assertNotIn(" 中古品", title)
            else:
                self.assertIn(f" {situation} ", title + " ")
            self.assertEqual(
                self.app.v_condition.get(),
                self.app.config.condition_text(situation, "", "", "トップス"))

    def test_all_motion_values_in_other_genre(self):
        cfg = self.app.config
        self.app.v_brand.set("A")
        self.app.v_genre.set("その他")
        self.root.update()
        for motion in core.MOTIONS:
            self.app.v_motion.set(motion)
            self.root.update()
            it = self.app._collect()
            self.assertEqual(it.motion, motion)
            self.assertEqual(
                self.app.v_condition.get(),
                cfg.condition_text(it.situation, "", motion, "その他"))
            if motion:
                self.assertTrue(self.app.v_title.get().endswith(motion))

    def test_kana_color_notated_feed_title(self):
        self.app.v_genre.set("シューズ")
        self.app.v_brand.set("ナイキ")
        self.app.v_brand_kana.set("ナイキ")
        self.app.v_name.set("エアマックス")
        self.app.v_color.set("白")
        self.app.v_notated.set("27")
        self.root.update()
        self.assertEqual(self.app.v_title.get(),
                         "ナイキ ナイキ エアマックス サイズ27 白 シューズ")

    def test_tag_condition_spaces_become_ten(self):
        self.app.v_genre.set("トップス")
        self.app.v_situation.set("美中古品")
        self.app.v_tag_condition.set("使用感  スレ　毛玉")
        self.root.update()
        self.assertEqual(
            self.app.v_condition.get(),
            "少々使用感と使用感、スレ、毛玉はありますが、"
            "大きなダメージはなく中古並の状態です。")

    def test_manual_condition_edit_survives_navigation(self):
        self.app.v_brand.set("A")
        self.app.v_price.set("100")
        self.app.v_genre.set("トップス")
        self.root.update()
        self.app.v_condition.set("手動で書き換えた説明文")
        self.app.on_next()                      # 2件目（新規）
        self.app.v_brand.set("B")
        self.app.v_price.set("200")
        self.app.v_genre.set("バッグ")
        self.app.on_prev()                      # 1件目へ戻る
        self.assertEqual(self.app.v_condition.get(), "手動で書き換えた説明文")
        self.assertEqual(self.app.items[0].condition_text, "手動で書き換えた説明文")


class GuiChoiceReflectionKanmeTests(GuiChoiceReflectionTests):
    """要町・中野版の設定でも同じ選択肢網羅を確認する。"""

    config_factory = staticmethod(kanme_config)

    def test_tag_condition_spaces_become_ten(self):
        self.app.v_genre.set("トップス")
        self.app.v_situation.set("美中古品")
        self.app.v_tag_condition.set("使用感  スレ")
        self.root.update()
        self.assertEqual(
            self.app.v_condition.get(),
            "美中古品。通常の着用に伴う状態。使用感、スレあり。")

    def test_kana_color_notated_feed_title(self):
        self.app.v_genre.set("シューズ")
        self.app.v_brand.set("ナイキ")
        self.app.v_name.set("エアマックス")
        self.app.v_color.set("白")
        self.app.v_notated.set("27")
        self.root.update()
        self.assertEqual(self.app.v_title.get(),
                         "ナイキ  エアマックス サイズ: 27 カラー: 白 シューズ")


# ---------------------------------------------------------------------------
# GUI: ボタン操作（外部連携は mock で遮断）
# ---------------------------------------------------------------------------

class GuiActionTests(_GuiBase):

    def _fill_valid(self, **kw):
        base = dict(brand="A", price="1000", genre="トップス")
        base.update(kw)
        for k, v in base.items():
            getattr(self.app, f"v_{k}").set(v)
        self.root.update()

    def test_on_price_tags_validates_before_writing(self):
        from unittest import mock
        self.app.v_price.set("abc")
        with mock.patch.object(core, "write_price_tags") as w:
            self.app.on_price_tags()
        w.assert_not_called()
        self.assertEqual(self.app.v_error.get(), "値段を入力してください")

    def test_on_price_tags_writes_current_and_opens(self):
        from unittest import mock
        self._fill_valid(brand="X", price="500", genre="シューズ")
        with mock.patch("os.startfile", create=True) as opener, \
             mock.patch.object(core, "write_price_tags",
                               return_value="dummy.ods") as writer:
            self.app.on_price_tags()
        writer.assert_called_once()
        items = writer.call_args[0][0]
        self.assertEqual([i.brand for i in items], ["X"])   # 現在の入力が保存される
        opener.assert_called_once_with("dummy.ods")

    def test_on_price_tags_shows_error_dialog_on_shortage(self):
        from unittest import mock
        self._fill_valid(price="100")
        with mock.patch.object(core, "write_price_tags",
                               side_effect=ValueError("シート不足")), \
             mock.patch.object(core.messagebox, "showerror") as err:
            self.app.on_price_tags()
        err.assert_called_once()
        self.assertIn("シート不足", err.call_args[0][1])

    def test_output_from_blank_new_slot_uses_saved_items(self):
        from unittest import mock
        for brand in ("A", "B", "C"):
            self._fill_valid(brand=brand, price="100", genre="トップス")
            self.app.on_next()                      # 3件保存 → 空の新規スロットへ
        self.assertEqual(self.app.v_error.get(), "")
        with mock.patch("os.startfile", create=True), \
             mock.patch.object(core, "write_price_tags",
                               return_value="d.ods") as pt, \
             mock.patch.object(core, "export_auction_csv",
                               return_value="d.csv") as csv_:
            self.app.on_price_tags()
            self.app.on_export_csv()
        self.assertEqual([i.brand for i in pt.call_args[0][0]], ["A", "B", "C"])
        self.assertEqual([i.brand for i in csv_.call_args[0][0]], ["A", "B", "C"])
        self.assertEqual(self.app.v_error.get(), "")    # 検証エラーを出さない
        self.assertEqual(len(self.app.items), 3)        # 空スロットは保存されない

    def test_output_with_no_items_shows_error(self):
        from unittest import mock
        with mock.patch.object(core, "write_price_tags") as pt, \
             mock.patch.object(core, "export_auction_csv") as csv_:
            self.app.on_price_tags()
            self.assertEqual(self.app.v_error.get(), "出力する商品がありません")
            self.app.on_export_csv()
            self.assertEqual(self.app.v_error.get(), "出力する商品がありません")
        pt.assert_not_called()
        csv_.assert_not_called()

    def test_output_still_blocks_on_partial_current_entry(self):
        from unittest import mock
        self._fill_valid(brand="A", price="100", genre="トップス")
        self.app.on_next()                              # 1件保存
        self.app.v_brand.set("途中")                     # 新規スロットに入力しかけ
        self.app.v_price.set("500")                      # 値段は入れたがジャンル未選択
        self.root.update()
        with mock.patch.object(core, "write_price_tags") as pt:
            self.app.on_price_tags()
        pt.assert_not_called()
        self.assertEqual(self.app.v_error.get(), "ジャンルを選択してください")

    def test_on_export_csv_validates_before_writing(self):
        from unittest import mock
        self.app.v_price.set("abc")
        with mock.patch.object(core, "export_auction_csv") as w:
            self.app.on_export_csv()
        w.assert_not_called()
        self.assertEqual(self.app.v_error.get(), "値段を入力してください")

    def test_on_export_csv_writes_current_and_opens(self):
        from unittest import mock
        self._fill_valid(brand="P", price="9800", genre="バッグ")
        with mock.patch("os.startfile", create=True) as opener, \
             mock.patch.object(core, "export_auction_csv",
                               return_value="dummy.csv") as writer:
            self.app.on_export_csv()
        writer.assert_called_once()
        items = writer.call_args[0][0]
        self.assertEqual([i.brand for i in items], ["P"])   # 現在の入力が保存される
        opener.assert_called_once_with("dummy.csv")

    def test_on_export_csv_shows_error_dialog(self):
        from unittest import mock
        self._fill_valid(price="100")
        with mock.patch.object(core, "export_auction_csv",
                               side_effect=ValueError("出力する商品がありません。")), \
             mock.patch.object(core.messagebox, "showerror") as err:
            self.app.on_export_csv()
        err.assert_called_once()
        self.assertIn("商品がありません", err.call_args[0][1])

    def test_close_confirmed_saves_settings(self):
        from unittest import mock
        path = self.app.settings_path
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.app.v_shop.set("要町")
        with mock.patch.object(core.messagebox, "askokcancel", return_value=True), \
             mock.patch.object(self.root, "destroy") as destroy:
            self.app._on_close()
        destroy.assert_called_once()
        self.assertEqual(core.load_settings(path).get("last_shop"), "要町")

    def test_close_cancelled_keeps_window(self):
        from unittest import mock
        with mock.patch.object(core.messagebox, "askokcancel", return_value=False), \
             mock.patch.object(self.root, "destroy") as destroy:
            self.app._on_close()
        destroy.assert_not_called()


# ---------------------------------------------------------------------------
# GUI: 店舗をまたぐ入力フロー
# ---------------------------------------------------------------------------

class GuiMultiShopTests(_GuiBase):

    def test_each_item_keeps_own_shop_through_price_tags(self):
        from unittest import mock
        rows = [("上池袋", "A"), ("中野", "B"), ("要町", "C")]
        for i, (shop, brand) in enumerate(rows):
            self.app.v_shop.set(shop)
            self.app.v_brand.set(brand)
            self.app.v_price.set("1000")
            self.app.v_genre.set("トップス")
            self.root.update()
            if i < len(rows) - 1:
                self.app.on_next()          # 最後の1件は on_price_tags に保存させる
        self.assertEqual(len(self.app.items), 2)

        captured = {}

        def fake_write(items, config, base):
            captured["nums"] = [
                core.management_number(core.SHOPS[it.shop].shop_id,
                                       *core.today_ymd(), n)
                for n, it in enumerate(items, start=1)]
            return "x.ods"

        with mock.patch.object(core, "write_price_tags", side_effect=fake_write), \
             mock.patch("os.startfile", create=True):
            self.app.on_price_tags()
        self.assertEqual(captured["nums"][0][:2], "22")
        self.assertEqual(captured["nums"][1][:2], "44")
        self.assertEqual(captured["nums"][2][:2], "11")

    def test_shop_change_does_not_rewrite_saved_items(self):
        self.app.v_shop.set("上池袋")
        self.app.v_brand.set("A")
        self.app.v_price.set("100")
        self.app.v_genre.set("トップス")
        self.root.update()
        self.app.on_next()
        self.app.v_shop.set("中野")           # 2件目の入力中に店舗変更
        self.root.update()
        self.assertEqual(self.app.items[0].shop, "上池袋")

    def test_export_csv_uses_each_items_shop(self):
        from unittest import mock
        for shop, brand in [("上池袋", "A"), ("中野", "B")]:
            self.app.v_shop.set(shop)
            self.app.v_brand.set(brand)
            self.app.v_price.set("1000")
            self.app.v_genre.set("トップス")
            self.root.update()
            if brand == "A":
                self.app.on_next()
        captured = {}

        def fake_export(items, config, base):
            captured["rows"] = [core.build_auction_row(it, config, n, core.today_ymd())
                                for n, it in enumerate(items, start=1)]
            return "x.csv"

        with mock.patch.object(core, "export_auction_csv", side_effect=fake_export), \
             mock.patch("os.startfile", create=True):
            self.app.on_export_csv()
        rows = captured["rows"]
        self.assertEqual(rows[0][0][:2], "22")                 # 上池袋
        self.assertEqual(rows[1][0][:2], "44")                 # 中野
        self.assertEqual(rows[0][50], "新NEW上池袋在庫")
        self.assertEqual(rows[1][50], "新NEW中野店在庫")


# ---------------------------------------------------------------------------
# GUI: 出力先フォルダ
# ---------------------------------------------------------------------------

class GuiOutputDirTests(_GuiBase):

    def _valid(self, **kw):
        base = dict(brand="A", price="1000", genre="トップス")
        base.update(kw)
        for k, v in base.items():
            getattr(self.app, f"v_{k}").set(v)
        self.root.update()

    def test_output_dir_uses_passed_default_when_no_saved_value(self):
        self.assertEqual(self.app.v_output_dir.get(), self.tmp_dir)

    def test_first_run_output_dir_is_empty(self):
        import tkinter as tk
        root2 = tk.Tk()
        root2.withdraw()
        self.addCleanup(root2.destroy)
        settings_dir = tempfile.mkdtemp()   # 設定なし = 初回起動
        self.addCleanup(
            lambda: __import__("shutil").rmtree(settings_dir, ignore_errors=True))
        fresh = core.EcBridgeApp(root2, medamaya_config(), settings_dir=settings_dir)
        self.assertEqual(fresh.v_output_dir.get(), "")   # 参照で選ばせる

    def test_browse_updates_output_dir(self):
        from unittest import mock
        target = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(target, ignore_errors=True))
        with mock.patch.object(core.filedialog, "askdirectory", return_value=target):
            self.app._browse_output_dir()
        self.assertEqual(self.app.v_output_dir.get(), os.path.normpath(target))

    def test_browse_cancel_keeps_output_dir(self):
        from unittest import mock
        before = self.app.v_output_dir.get()
        with mock.patch.object(core.filedialog, "askdirectory", return_value=""):
            self.app._browse_output_dir()
        self.assertEqual(self.app.v_output_dir.get(), before)

    def test_price_tags_and_csv_land_in_chosen_dir(self):
        from unittest import mock
        target = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(target, ignore_errors=True))
        self.app.v_output_dir.set(target)
        self._valid(m1="60", m2="45")
        with mock.patch("os.startfile", create=True):
            self.app.on_price_tags()
            self.app.on_export_csv()
        y, m, d = core.today_ymd()
        self.assertTrue(os.path.isfile(os.path.join(target, "ネット用値札.ods")))
        self.assertTrue(os.path.isfile(
            os.path.join(target, f"auctions_{y:04d}{m:02d}{d:02d}.csv")))

    def test_nonexistent_output_dir_is_created(self):
        from unittest import mock
        target = os.path.join(tempfile.mkdtemp(), "新規サブ")
        self.addCleanup(lambda: __import__("shutil").rmtree(
            os.path.dirname(target), ignore_errors=True))
        self.app.v_output_dir.set(target)
        self._valid()
        with mock.patch("os.startfile", create=True):
            self.app.on_price_tags()
        self.assertTrue(os.path.isfile(os.path.join(target, "ネット用値札.ods")))

    def test_empty_output_dir_shows_error(self):
        from unittest import mock
        self.app.v_output_dir.set("")
        self._valid()
        with mock.patch.object(core, "write_price_tags") as w:
            self.app.on_price_tags()
        w.assert_not_called()
        self.assertEqual(self.app.v_error.get(), "出力先フォルダを指定してください")

    def test_output_dir_persisted_and_restored(self):
        target = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(target, ignore_errors=True))
        self.app.v_output_dir.set(target)
        self.root.update()
        saved = core.load_settings(self.app.settings_path)
        self.assertEqual(saved.get("output_dir"), target)
        # 設定ディレクトリを引き継いだ新しいアプリで復元される
        import tkinter as tk
        root2 = tk.Tk()
        root2.withdraw()
        try:
            app2 = core.EcBridgeApp(
                root2, medamaya_config(),
                settings_dir=os.path.dirname(self.app.settings_path))
            self.assertEqual(app2.v_output_dir.get(), target)
        finally:
            root2.destroy()


# ---------------------------------------------------------------------------
# GUI: 複製ボタン
# ---------------------------------------------------------------------------

class GuiDuplicateTests(_GuiBase):

    def _add(self, brand, **kw):
        base = dict(price="100", genre="トップス")
        base.update(kw)
        self.app.v_brand.set(brand)
        for k, v in base.items():
            getattr(self.app, f"v_{k}").set(v)
        self.root.update()
        self.app.on_next()

    def test_duplicate_middle_item_inserts_copy_after(self):
        for b in ("A", "B", "C"):
            self._add(b)
        self.app.on_prev()                       # C
        self.app.on_prev()                       # B  (index 1)
        self.app.on_duplicate()
        self.assertEqual([i.brand for i in self.app.items], ["A", "B", "B", "C"])
        self.assertEqual(self.app.index, 2)          # 複製先を表示
        self.assertEqual(self.app.v_brand.get(), "B")
        self.assertEqual(self.app.v_counter.get(), "3/4")

    def test_duplicate_shifts_following_items(self):
        for b in ("A", "B", "C", "D"):
            self._add(b)
        self.app.on_prev(); self.app.on_prev(); self.app.on_prev()   # -> B (index 1)
        self.app.on_duplicate()
        self.assertEqual([i.brand for i in self.app.items],
                         ["A", "B", "B", "C", "D"])

    def test_duplicate_reflects_unsaved_edits(self):
        self._add("A")
        self._add("B")
        self.app.on_prev()                       # -> B (index 1, last saved)
        self.app.v_color.set("赤")               # 画面で編集（次へは押さない）
        self.root.update()
        self.app.on_duplicate()
        self.assertEqual(self.app.items[1].color, "赤")
        self.assertEqual(self.app.items[2].color, "赤")   # 複製にも反映

    def test_duplicate_is_independent_copy(self):
        self._add("A")
        self.app.on_prev()
        self.app.on_duplicate()                  # items: [A, A'], index 1
        self.app.v_brand.set("A2")
        self.root.update()
        self.app.on_next()                       # 複製を保存
        self.assertEqual([i.brand for i in self.app.items], ["A", "A2"])

    def test_duplicate_from_new_slot_with_content(self):
        self._add("A")
        self.app.v_brand.set("B")                # 新規スロットに入力（次へは押さない）
        self.app.v_price.set("200")
        self.app.v_genre.set("バッグ")
        self.root.update()
        self.app.on_duplicate()
        self.assertEqual([i.brand for i in self.app.items], ["A", "B", "B"])
        self.assertEqual(self.app.index, 2)
        self.assertEqual(self.app.v_brand.get(), "B")

    def test_duplicate_last_item_appends(self):
        self._add("A")
        self._add("B")
        self.app.on_prev()                       # -> B (index 1, last)
        self.app.on_duplicate()
        self.assertEqual([i.brand for i in self.app.items], ["A", "B", "B"])
        self.assertEqual(self.app.index, 2)

    def test_duplicate_on_blank_slot_shows_error(self):
        self.app.on_duplicate()
        self.assertEqual(self.app.v_error.get(), "複製するデータがありません")
        self.assertEqual(self.app.items, [])


# ---------------------------------------------------------------------------
# ヤフオク一括出品CSV
# ---------------------------------------------------------------------------

def _read_csv(path):
    with open(path, encoding="cp932", newline="") as fp:
        return list(csv.reader(fp))


class AuctionCsvTests(unittest.TestCase):

    def _export(self, items, config=None):
        import shutil
        out_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(out_dir, ignore_errors=True))
        return core.export_auction_csv(items, config or medamaya_config(), out_dir)

    def _row(self, **kw):
        it = sample_item(**kw)
        it.condition_text = medamaya_config().condition_text(
            it.situation, core.join_tag_note(it.tag_condition), it.motion, it.genre)
        return core.build_auction_row(it, medamaya_config(), 4, (2026, 8, 28))

    def col(self, name):
        return core.AUCTION_CSV_HEADER.index(name)

    def test_row_has_53_columns(self):
        self.assertEqual(len(self._row()), 53)

    def test_core_fields(self):
        row = self._row(shop="中野", price="3980", rank2="やや傷や汚れあり",
                        postage="2000", notated_size="27")
        self.assertEqual(row[self.col("管理番号")], "44260828004")
        self.assertEqual(row[self.col("カテゴリ")], "2084207680")
        self.assertEqual(row[self.col("開始価格")], "3980")
        self.assertEqual(row[self.col("ストア内商品検索用キーワード")], "中野店 XXX")
        self.assertEqual(row[self.col("商品発送元の都道府県")], "東京都")
        self.assertEqual(row[self.col("商品発送元の市区町村")], "中野区")
        self.assertEqual(row[self.col("商品の状態")], "やや傷や汚れあり")
        self.assertEqual(row[self.col("商品保存先フォルダパス")], "新NEW中野店在庫")
        self.assertEqual(row[self.col("配送グループ")], "2")

    def test_constant_fields(self):
        row = self._row()
        for name, want in [("即決価格", "0"), ("個数", "1"), ("期間", "7"),
                           ("終了時間", "22"), ("送料負担", "落札者"),
                           ("代金先払い、後払い", "代金先払い"), ("最低評価", "-5"),
                           ("悪評割合制限", "いいえ"), ("入札者認証制限", "いいえ"),
                           ("自動延長", "はい"), ("商品の自動再出品", "3"),
                           ("注目のオークション", "0"), ("消費税設定", "10"),
                           ("税込みフラグ", "いいえ"), ("発送までの日数", "1")]:
            self.assertEqual(row[self.col(name)], want, name)

    def test_image_and_spec_fields_blank(self):
        row = self._row()
        for name in ["画像1", "画像1コメント", "画像10コメント", "自動値下げ",
                     "重量設定", "JANコード・ISBNコード", "ブランドID",
                     "商品スペックサイズ種別", "商品スペックサイズID", "商品分類ID"]:
            self.assertEqual(row[self.col(name)], "", name)

    def test_condition_maps_unused_to_yahoo_label(self):
        self.assertEqual(self._row(rank2="未使用品")[self.col("商品の状態")], "未使用")
        self.assertEqual(self._row(rank2="未使用品に近い")[self.col("商品の状態")],
                         "未使用に近い")

    def test_title_and_description_reuse_web_builders(self):
        it = sample_item(genre="シューズ", situation="美中古品")
        it.condition_text = medamaya_config().condition_text(
            it.situation, "", "", it.genre)
        row = core.build_auction_row(it, medamaya_config(), 1, (2026, 8, 28))
        self.assertEqual(row[self.col("タイトル")],
                         core.build_title(it, medamaya_config(), web=True))
        self.assertEqual(row[self.col("説明")],
                         core.build_web_description(it, medamaya_config()))

    def test_kanme_config_folder_and_prefixes(self):
        it = sample_item(shop="中野", genre="トップス", gender="メンズ",
                         notated_size="M")
        it.condition_text = "x"
        row = core.build_auction_row(it, kanme_config(), 1, (2026, 8, 28))
        self.assertIn("サイズ: M", row[self.col("タイトル")])
        self.assertEqual(row[self.col("商品保存先フォルダパス")], "新NEW中野店在庫")

    def test_export_writes_shift_jis_crlf_file(self):
        items = [sample_item(brand=f"B{i}", name=f"N{i}", price=str(1000 + i))
                 for i in range(3)]
        for it in items:
            it.condition_text = "x"
        path = self._export(items)
        y, m, d = core.today_ymd()
        self.assertEqual(os.path.basename(path), f"auctions_{y:04d}{m:02d}{d:02d}.csv")
        with open(path, "rb") as fp:
            raw = fp.read()
        self.assertNotIn(raw[:1], (b"\xef",))          # BOM 無し
        self.assertEqual(raw.count(b"\r\n"), 4)         # ヘッダ + 3行
        self.assertEqual(raw.count(b"\n"), 4)           # 埋め込み改行なし（競りナビ対策）
        rows = _read_csv(path)
        self.assertEqual(rows[0], core.AUCTION_CSV_HEADER)
        self.assertEqual(len(rows) - 1, 3)
        self.assertEqual([r[2] for r in rows[1:]],
                         [core.build_title(it, medamaya_config(), web=True)
                          for it in items])

    def test_export_sequential_management_numbers(self):
        items = [sample_item(brand=f"B{i}", price="100") for i in range(5)]
        for it in items:
            it.condition_text = "x"
        rows = _read_csv(self._export(items))
        y, m, d = core.today_ymd()
        self.assertEqual(
            [r[0] for r in rows[1:]],
            [core.management_number(22, y, m, d, n) for n in range(1, 6)])

    def test_export_empty_raises(self):
        with self.assertRaises(ValueError):
            core.export_auction_csv([], medamaya_config(), tempfile.mkdtemp())

    def test_export_same_day_overwrites_next_day_new_file(self):
        from unittest import mock
        out_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(out_dir, ignore_errors=True))
        it = sample_item(brand="X", price="100")
        it.condition_text = "x"

        with mock.patch.object(core, "today_ymd", return_value=(2026, 8, 28)):
            p1 = core.export_auction_csv([it], medamaya_config(), out_dir)
            p1b = core.export_auction_csv([it, it], medamaya_config(), out_dir)
        self.assertEqual(p1, p1b)                           # 同日は同じファイル
        self.assertEqual(os.path.basename(p1), "auctions_20260828.csv")
        self.assertEqual(len(_read_csv(p1b)) - 1, 2)        # 上書きされている

        with mock.patch.object(core, "today_ymd", return_value=(2026, 8, 29)):
            p2 = core.export_auction_csv([it], medamaya_config(), out_dir)
        self.assertEqual(os.path.basename(p2), "auctions_20260829.csv")
        self.assertTrue(os.path.isfile(p1))                 # 前日分は残る

    def test_header_matches_sample(self):
        if not os.path.isfile(SAMPLE_CSV):
            self.skipTest("auctions_sample.csv が無い")
        self.assertEqual(_read_csv(SAMPLE_CSV)[0], core.AUCTION_CSV_HEADER)

    def test_description_concrete_example(self):
        """中野店・TOMMY HILFIGER 半袖シャツ での説明列を具体値で検証。"""

        it = Item(shop="中野", brand="TOMMY HILFIGER", brand_kana="トミーヒルフィガー",
                  name="半袖シャツ ボタンシャツ コットン100", color="イエロー",
                  price="1580", gender="メンズ", genre="トップス", situation="中古品",
                  rank="C", rank2="目立った傷や汚れなし", notated_size="XL",
                  m1="70", m2="44.5", m3="57", m4="22.5")
        cfg = kanme_config()
        it.condition_text = cfg.condition_text("中古品", "", "", "トップス")
        html = core.build_web_description(it, cfg)
        self.assertEqual(html, orig_web_description(it, cfg.shop("中野").images))
        self.assertNotIn("\n", html)   # 競りナビ対策で1物理行
        self.assertIn("TOMMY HILFIGER 半袖シャツ ボタンシャツ コットン100です。<BR> ", html)
        self.assertIn("中古品。通常の着用に伴う状態。<BR> ", html)
        self.assertIn("着丈:70cm<BR> 肩幅:44.5cm<BR> 身幅:57cm<BR> 袖丈:22.5cm<BR>", html)
        self.assertIn(">中野</TD>", html)
        self.assertIn("rank.jpg", html)
        self.assertNotIn("ranku.jpg", html)


# ---------------------------------------------------------------------------
# インストーラ
# ---------------------------------------------------------------------------

class InstallerTests(unittest.TestCase):

    def setUp(self):
        installer_dir = os.path.join(os.path.dirname(TESTS_DIR), "installer")
        if installer_dir not in sys.path:
            sys.path.insert(0, installer_dir)
        import installer as inst
        self.inst = inst
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        # 同梱物のダミー
        self.bundle = os.path.join(self.tmp, "bundle")
        os.makedirs(self.bundle)
        for n in (inst.APP_EXE_NAME, inst.TEMPLATE_NAME):
            with open(os.path.join(self.bundle, n), "wb") as fp:
                fp.write(b"dummy-" + n.encode())
        inst.bundled = lambda name: os.path.join(self.bundle, name)
        inst.make_desktop_shortcut = lambda *a, **k: None   # デスクトップを汚さない

    def test_install_creates_per_shop_layout(self):
        root = os.path.join(self.tmp, "installed")
        for shop in self.inst.SHOPS:
            exe = self.inst.install(shop, root)
            d = os.path.dirname(exe)
            self.assertEqual(os.path.basename(exe), f"EC_Bridge_{shop}.exe")
            self.assertEqual(d, os.path.join(root, shop))
            self.assertTrue(os.path.isfile(exe))
            self.assertTrue(os.path.isfile(os.path.join(d, self.inst.TEMPLATE_NAME)))
            with open(os.path.join(d, "install.json"), encoding="utf-8") as fp:
                self.assertEqual(json.load(fp), {"shop": shop})

    def test_installed_config_selects_right_variant(self):
        for shop, fn in (("上池袋", core.medamaya_condition_text),
                         ("要町", core.kanme_condition_text),
                         ("中野", core.kanme_condition_text)):
            cfg = core.make_config({"shop": shop}.get("shop"))
            self.assertEqual(cfg.condition_text, fn)


FOLDER_LISTING_FIXTURE = os.path.join(
    TESTS_DIR, "fixtures", "folder_listing_sample.html")


class SerinaviParseTests(unittest.TestCase):
    """競りナビ フォルダ一覧HTML → {管理番号: item_id} の抽出。"""

    def setUp(self):
        import serinavi
        self.serinavi = serinavi
        with open(FOLDER_LISTING_FIXTURE, encoding="utf-8") as fp:
            self.html = fp.read()

    def test_parse_pairs_all_items(self):
        got = self.serinavi.parse_folder_listing(self.html)
        self.assertEqual(got, {
            "22260828001": "900000001",
            "22260828002": "900000002",
            "22260828003": "900000003",
            "22260828004": "900000004",
        })

    def test_parse_empty_html(self):
        self.assertEqual(self.serinavi.parse_folder_listing(""), {})

    def test_parse_ignores_block_without_management_number(self):
        got = self.serinavi.parse_folder_listing(self.html)
        self.assertNotIn("999999999", got.values())   # ページャの checkbox は拾わない

    def test_parse_falls_back_to_checkbox_value(self):
        block = ('<input name="itemCheckbox" value="555">'
                 '<p>管理番号 22260828009</p>')       # edit リンク無し
        self.assertEqual(
            self.serinavi.parse_folder_listing(block), {"22260828009": "555"})

    def test_edit_url_format(self):
        url = self.serinavi.EDIT_URL.format(fid="1308997", iid="900000001")
        self.assertIn("folder_id=1308997", url)
        self.assertIn("item_id=900000001", url)
        self.assertIn("action=edit", url)

    def test_folder_list_url_has_newest_first_sort(self):
        self.assertIn("sort=-update_date",
                      self.serinavi.FOLDER_LIST_URL.format(fid="1308997"))


class DescriptionMultilineTests(unittest.TestCase):
    """build_web_description の multiline 切り替え。"""

    def _item(self):
        return Item(shop="上池袋", brand="NIKE", brand_kana="ナイキ", name="Tシャツ",
                    color="白", price="1000", gender="", genre="トップス",
                    situation="中古品", rank="C", rank2="やや傷や汚れあり",
                    tag_condition="", condition_text="使用感あり", postage="700",
                    notated_size="M", motion="", m1="60", m2="45", m3="50", m4="58")

    def test_default_is_single_physical_line(self):
        text = core.build_web_description(self._item(), medamaya_config())
        self.assertNotIn("\n", text)

    def test_multiline_keeps_newlines(self):
        text = core.build_web_description(
            self._item(), medamaya_config(), multiline=True)
        self.assertIn("\n", text)

    def test_both_have_same_content_ignoring_newlines(self):
        cfg = medamaya_config()
        one = core.build_web_description(self._item(), cfg)
        multi = core.build_web_description(self._item(), cfg, multiline=True)
        self.assertEqual(one, multi.replace("\n", " "))


class GuiPublishTests(_GuiBase):
    """「出品」ボタン: CSV出力 → serinavi.publish 呼び出し。"""

    def _fill_valid(self, **kw):
        base = dict(brand="A", price="1000", genre="トップス")
        base.update(kw)
        for k, v in base.items():
            getattr(self.app, f"v_{k}").set(v)
        self.root.update()

    def _saved_item(self):
        self._fill_valid()
        self.app.on_next()

    def test_needs_firefox_profile(self):
        from unittest import mock
        import serinavi
        self._saved_item()
        self.app.v_firefox_profile.set("")
        with mock.patch.object(serinavi, "publish") as pub, \
             mock.patch.object(core.messagebox, "showerror") as err:
            self.app.on_publish()
        pub.assert_not_called()
        err.assert_called_once()

    def test_exports_csv_and_calls_publish(self):
        from unittest import mock
        import serinavi
        self._saved_item()
        self.app.v_firefox_profile.set(self.tmp_dir)
        with mock.patch.object(core, "export_auction_csv",
                               return_value="out.csv") as exp, \
             mock.patch.object(core.messagebox, "askokcancel", return_value=True), \
             mock.patch.object(serinavi, "publish", return_value=[]) as pub, \
             mock.patch.object(core.messagebox, "showinfo") as info:
            self.app.on_publish()
        exp.assert_called_once()
        pub.assert_called_once()
        args, kwargs = pub.call_args
        self.assertEqual([i.brand for i in args[0]], ["A"])
        self.assertEqual(args[2], "out.csv")
        self.assertEqual(kwargs["profile_dir"], self.tmp_dir)
        self.assertTrue(kwargs["geckodriver_path"].endswith("geckodriver.exe"))
        info.assert_called_once()

    def test_cancel_at_confirm_skips_publish(self):
        from unittest import mock
        import serinavi
        self._saved_item()
        self.app.v_firefox_profile.set(self.tmp_dir)
        with mock.patch.object(core, "export_auction_csv", return_value="out.csv"), \
             mock.patch.object(core.messagebox, "askokcancel", return_value=False), \
             mock.patch.object(serinavi, "publish") as pub:
            self.app.on_publish()
        pub.assert_not_called()

    def test_failures_show_warning(self):
        from unittest import mock
        import serinavi
        self._saved_item()
        self.app.v_firefox_profile.set(self.tmp_dir)
        with mock.patch.object(core, "export_auction_csv", return_value="out.csv"), \
             mock.patch.object(core.messagebox, "askokcancel", return_value=True), \
             mock.patch.object(serinavi, "publish",
                               return_value=["22260828001 A … 一覧に見つからず"]), \
             mock.patch.object(core.messagebox, "showwarning") as warn:
            self.app.on_publish()
        warn.assert_called_once()

    def test_blank_new_slot_uses_saved_items(self):
        from unittest import mock
        import serinavi
        for brand in ("A", "B"):
            self._fill_valid(brand=brand)
            self.app.on_next()
        self.app.v_firefox_profile.set(self.tmp_dir)
        with mock.patch.object(core, "export_auction_csv", return_value="out.csv"), \
             mock.patch.object(core.messagebox, "askokcancel", return_value=True), \
             mock.patch.object(serinavi, "publish", return_value=[]) as pub, \
             mock.patch.object(core.messagebox, "showinfo"):
            self.app.on_publish()
        self.assertEqual([i.brand for i in pub.call_args[0][0]], ["A", "B"])
        self.assertEqual(self.app.v_error.get(), "")

    def test_no_items_shows_error(self):
        from unittest import mock
        import serinavi
        self.app.v_firefox_profile.set(self.tmp_dir)
        with mock.patch.object(serinavi, "publish") as pub:
            self.app.on_publish()
        pub.assert_not_called()
        self.assertEqual(self.app.v_error.get(), "出力する商品がありません")


if __name__ == "__main__":
    unittest.main(verbosity=2)
