# -*- coding: utf-8 -*-
"""EC_Bridge 共通ロジック。

GUI (:class:`EcBridgeApp`)、値札出力 (:func:`write_price_tags`)、
ヤフオク一括出品CSVの出力 (:func:`export_auction_csv`) を提供する。

店舗ごとの派生版 (EC_Bridge.py / EC_Bridge_for_kanme_nakano.py) は
:class:`AppConfig` を組み立てて :func:`run` を呼ぶだけの薄いランチャーにする。
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import re
import sys
import traceback
import unicodedata
from dataclasses import dataclass, field, replace
from typing import Callable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------------------
# ディレクトリ構成
#   開発時 : <project>/src(コード・テンプレート) / <project>/output(生成物)
#   exe    : EC_Bridge.exe と同じフォルダに ネット用値札.ods・install.json を置き、
#            そこへ output/ を作る（テンプレートは店が編集できるよう同梱しない）
# ---------------------------------------------------------------------------

_FROZEN = getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")
SRC_DIR = (getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
           if _FROZEN else os.path.dirname(os.path.abspath(__file__)))
# 生成物・設定・テンプレートを置く場所（exe の隣 / 開発時はリポジトリ直下）
PROJECT_DIR = os.path.dirname(sys.executable) if _FROZEN else os.path.dirname(SRC_DIR)


def default_output_dir() -> str:
    """出力先の初期値（GUI で変更できる）。exe/リポジトリ直下の output/。"""

    path = os.path.join(PROJECT_DIR, "output")
    os.makedirs(path, exist_ok=True)
    return path


# 後方互換
output_dir = default_output_dir


def default_template_path(config: "AppConfig") -> str:
    base = PROJECT_DIR if _FROZEN else SRC_DIR
    return os.path.join(base, config.price_tag_filename)


def default_geckodriver_path() -> str:
    """geckodriver.exe の場所。開発時は src/、exe では同梱先（_MEIPASS）。"""

    return os.path.join(SRC_DIR, "geckodriver.exe")


def install_config() -> dict:
    """exe の隣にある install.json（インストーラが書き出す）。"""

    try:
        with open(os.path.join(PROJECT_DIR, "install.json"), encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

GENDERS = ["記入無し", "メンズ", "レディース"]          # 記入無しは内部値 ""
POSTAGES = ["700", "2000"]
RANKS = ["A", "AB", "B", "BC", "C", "CD", "D", "DE", "E"]
RANK2S = ["未使用品", "未使用品に近い", "目立った傷や汚れなし",
          "やや傷や汚れあり", "傷や汚れあり", "全体的に状態が悪い"]
SITUATIONS = ["未使用品", "未使用保管品", "未使用タグ付き品", "未使用箱付き品",
              "美中古品", "中古品", "現状品", "稼働品", "ジャンク品",
              "箱付き", "ケース付き"]
MOTIONS = ["", "通電未確認", "動作未確認", "簡易通電確認済み",
           "通電確認済み", "簡易動作確認済み", "動作確認済み"]
GENRES = ["トップス", "ボトムス", "シューズ", "バッグ", "腕時計", "その他"]
GENRE_PLACEHOLDER = "選択してください"

DEFAULT_SITUATION = "中古品"
DEFAULT_RANK = "C"
DEFAULT_RANK2 = "目立った傷や汚れなし"
DEFAULT_POSTAGE = "700"

TITLE_CHAR_LIMIT = 65

# ジャンル -> 実寸フィールドの (HTML表記ラベル, GUI表記ラベル)。
# GUIラベルを省いた場合は HTML ラベルを流用する。m1..m4 に順に対応。
GENRE_MEASUREMENTS: dict[str, list[tuple[str, str]]] = {
    "トップス": [("着丈", "着丈"), ("肩幅", "肩幅"), ("身幅", "身幅"), ("袖丈", "袖丈")],
    "ボトムス": [("ウエスト", "ウエスト"), ("股上", "股上"), ("股下", "股下"), ("裾幅", "裾幅")],
    "シューズ": [("アウトソール", "アウトソール全長"), ("幅", "幅")],
    "バッグ": [("横", "横"), ("縦", "縦"), ("マチ", "マチ")],
    "腕時計": [("ケース縦", "ケース縦"), ("ケース横", "ケース横"), ("ベルト幅", "ベルト幅")],
    "その他": [],
}

# ヤフオク一括出品CSV（セラーツール形式。Shift-JIS / CRLF）関連の定数。
AUCTION_CATEGORY_ID = "2084207680"   # 旧Selenium版と同じく常にこの値
AUCTION_DURATION = "7"               # 期間（日）
AUCTION_END_TIME = "22"              # 終了時間
AUCTION_RESUBMIT = "3"               # 商品の自動再出品
AUCTION_LEAD_TIME = "1"              # 発送までの日数
AUCTION_DELIVERY_GROUP = {"700": "1", "2000": "2"}   # 送料 -> 配送グループ
AUCTION_CSV_ENCODING = "cp932"

# 商品ランク(rank2) -> CSV「商品の状態」列の表記。
YAHOO_CONDITION_CSV = {
    "未使用品": "未使用",
    "未使用品に近い": "未使用に近い",
    "目立った傷や汚れなし": "目立った傷や汚れなし",
    "やや傷や汚れあり": "やや傷や汚れあり",
    "傷や汚れあり": "傷や汚れあり",
    "全体的に状態が悪い": "全体的に状態が悪い",
}

# ヤフオク一括出品CSVのヘッダー（53列。順序厳守）。
AUCTION_CSV_HEADER = [
    "管理番号", "カテゴリ", "タイトル", "説明", "ストア内商品検索用キーワード",
    "開始価格", "即決価格", "個数", "期間", "終了時間",
    "商品発送元の都道府県", "商品発送元の市区町村", "送料負担", "代金先払い、後払い",
    "商品の状態",
    "画像1", "画像1コメント", "画像2", "画像2コメント", "画像3", "画像3コメント",
    "画像4", "画像4コメント", "画像5", "画像5コメント", "画像6", "画像6コメント",
    "画像7", "画像7コメント", "画像8", "画像8コメント", "画像9", "画像9コメント",
    "画像10", "画像10コメント",
    "最低評価", "悪評割合制限", "入札者認証制限", "自動延長", "商品の自動再出品",
    "自動値下げ", "注目のオークション", "重量設定", "消費税設定", "税込みフラグ",
    "JANコード・ISBNコード", "ブランドID", "商品スペックサイズ種別",
    "商品スペックサイズID", "商品分類ID", "商品保存先フォルダパス", "配送グループ",
    "発送までの日数",
]

DESCRIPTION_TEMPLATE = (
    "<TABLE BORDER=1 WIDTH=700px CELLSPACING=4 CELLPADDING=10 BORDER=1> </TD> </TR> "
    "<TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>ランク付け</TD> <TD WIDTH=75%>\n"
    "{rank}"
    "\n</TD></TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>状態</TD> <TD WIDTH=75%>\n"
    "{brand} {name}です。<BR>\n"
    "{condition}<BR>\n"
    "<TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>表記サイズ</TD> <TD WIDTH=75%>\n"
    "{notated}"
    "\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>実寸サイズ</TD> <TD WIDTH=75%>\n"
    "{measurements}"
    "\n</TD> </TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>カラー</TD> <TD WIDTH=75%>\n"
    "{color}"
    "\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>保管店舗</TD> <TD WIDTH=75%>{shop}</TD> </TR>  </TABLE>"
    "{images}"
)

ITEMS_PER_SHEET = 20
# 値札シート内の (この位置以上なら, データ列)。ラベルはデータ列 +1。
PRICE_TAG_BLOCKS = [(16, 9), (11, 6), (6, 3), (1, 0)]

_IMG_UEIKEBUKURO = (
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/rannku.jpg>"
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
)
_IMG_KANAMECHO = _IMG_UEIKEBUKURO
_IMG_NAKANO = (
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/ranku.jpg><BR>"
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/nakanochizu3.jpg>"
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
)
# 要町・中野版で使う 中野店の画像（rank.jpg 版）
_IMG_NAKANO_KANME = (
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/rank.jpg><BR>"
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/nakanochizu3.jpg>"
    "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShopSpec:
    """店舗ごとの固定値。"""

    name: str
    shop_id: int
    store_keyword: str          # ストア内検索キーワード
    city: str                   # 発送元の市区町村
    prefecture_name: str        # 発送元 都道府県名
    folder_path: str            # CSV「商品保存先フォルダパス」
    folder_id: str              # 競りナビのフォルダID（出品時の一覧・編集URL用）
    images: str                 # 商品説明末尾の画像タグ


SHOPS: dict[str, ShopSpec] = {
    "上池袋": ShopSpec("上池袋", 22, "上池袋店 XXX", "豊島区", "東京都",
                       "新NEW上池袋在庫", "1308997", _IMG_UEIKEBUKURO),
    "要町": ShopSpec("要町", 11, "要町店 XXX", "豊島区", "東京都",
                     "新NEW要町在庫", "1308972", _IMG_KANAMECHO),
    "中野": ShopSpec("中野", 44, "中野店 XXX", "中野区", "東京都",
                     "新NEW中野店在庫", "1309032", _IMG_NAKANO),
}
SHOP_NAMES = list(SHOPS)


@dataclass
class AppConfig:
    """派生版ごとの差分。"""

    name: str                                   # 設定ファイル名の接頭辞 / ウィンドウタイトル
    default_shop: str
    condition_text: Callable[[str, str, str, str], str]
    base_sheet_index: int = 0                    # 値札テンプレートの書き込み開始タブ
    gui_size_prefix: str = " サイズ"
    gui_color_prefix: str = " "
    web_size_prefix: str = " サイズ "
    web_color_prefix: str = " "
    shop_image_overrides: dict[str, str] = field(default_factory=dict)
    price_tag_filename: str = "ネット用値札.ods"
    window_title: str = "EC_Bridge"

    def shop(self, name: str) -> ShopSpec:
        spec = SHOPS[name]
        image = self.shop_image_overrides.get(name)
        if image is not None:
            spec = replace(spec, images=image)
        return spec


@dataclass
class Item:
    """商品1件分の入力データ。"""

    shop: str = ""
    brand: str = ""
    brand_kana: str = ""
    name: str = ""
    color: str = ""
    price: str = ""
    gender: str = ""                            # "", "メンズ", "レディース"
    genre: str = GENRE_PLACEHOLDER
    situation: str = DEFAULT_SITUATION
    rank: str = DEFAULT_RANK
    rank2: str = DEFAULT_RANK2
    tag_condition: str = ""                     # 値札用の状態メモ
    condition_text: str = ""                   # 生成された状態説明文
    postage: str = DEFAULT_POSTAGE
    notated_size: str = ""
    motion: str = ""
    m1: str = ""
    m2: str = ""
    m3: str = ""
    m4: str = ""

    def measurement_values(self) -> list[str]:
        return [self.m1, self.m2, self.m3, self.m4]


# ---------------------------------------------------------------------------
# 状態説明文テンプレート（派生版ごと）
# ---------------------------------------------------------------------------

def medamaya_condition_text(situation: str, tag_note: str, motion: str, genre: str) -> str:
    note = ("と" + tag_note) if tag_note else ""
    body = f"少々使用感{note}はありますが、大きなダメージはなく中古並の状態です。"
    if genre == "その他" and motion:
        return f"{motion}です。{body}"
    return body


def kanme_condition_text(situation: str, tag_note: str, motion: str, genre: str) -> str:
    note = (tag_note + "あり。") if tag_note else ""
    verb = "着用" if genre in ("トップス", "ボトムス") else "使用"
    body = f"{situation}。通常の{verb}に伴う状態。{note}"
    if motion:
        return f"{motion}。{body}"
    return body


# 要町・中野は文言・区切り・中野店画像が異なる「要町中野版」を使う
KANME_SHOPS = frozenset({"要町", "中野"})
_MEDAMAYA_KW: dict = dict(condition_text=medamaya_condition_text)
_KANME_KW: dict = dict(
    condition_text=kanme_condition_text,
    gui_size_prefix=" サイズ: ", gui_color_prefix=" カラー: ",
    web_size_prefix=" サイズ: ", web_color_prefix=" カラー: ",
    shop_image_overrides={"中野": _IMG_NAKANO_KANME},
)


def make_config(shop: str) -> "AppConfig":
    """店舗名から AppConfig を組み立てる（要町・中野は要町中野版）。"""

    kw = _KANME_KW if shop in KANME_SHOPS else _MEDAMAYA_KW
    default_shop = shop if shop in SHOP_NAMES else "上池袋"
    return AppConfig(name="EC_Bridge", default_shop=default_shop,
                     window_title=f"EC_Bridge（{default_shop}）", **kw)


# ---------------------------------------------------------------------------
# 純粋なヘルパー
# ---------------------------------------------------------------------------

def today_ymd() -> tuple[int, int, int]:
    d = datetime.date.today()
    return d.year, d.month, d.day


def format_display_date(year: int, month: int, day: int) -> str:
    return f"{year}年{month}月{day}日"


def management_number(shop_id: int, year: int, month: int, day: int, seq: int) -> str:
    """管理番号。先頭ゼロを保持するため文字列で返す。"""

    return f"{shop_id}{year % 100:02d}{month:02d}{day:02d}{seq:03d}"


def join_tag_note(raw: str) -> str:
    """値札メモの空白区切りを読点区切りにまとめる。"""

    return re.sub(r"[ \u3000]+", "、", raw.strip())


def _is_digits_or_empty(proposed: str) -> bool:
    """値段入力欄のバリデーション: 半角数字のみ許可（空欄は可）。"""

    return proposed == "" or (proposed.isascii() and proposed.isdigit())


def measurement_html(item: Item) -> str:
    labels = GENRE_MEASUREMENTS.get(item.genre, [])
    if not labels:
        return "-"
    values = item.measurement_values()
    return "\n".join(f"{html_label}:{value}cm<BR>"
                     for (html_label, _gui), value in zip(labels, values))


def build_title(item: Item, config: AppConfig, *, web: bool) -> str:
    """ネット出品タイトルを生成する。"""

    size_prefix = config.web_size_prefix if web else config.gui_size_prefix
    color_prefix = config.web_color_prefix if web else config.gui_color_prefix
    base = f"{item.brand} {item.brand_kana} {item.name}"
    parts: list[str] = []
    if item.notated_size:
        parts.append(size_prefix + item.notated_size)
    if item.color:
        parts.append(color_prefix + item.color)
    if item.situation and item.situation != "中古品":
        parts.append(" " + item.situation)

    if item.genre == "その他":
        genre_label, motion_label = "", (item.motion or "")
    elif item.genre and item.genre != GENRE_PLACEHOLDER:
        genre_label, motion_label = item.genre, ""
    else:
        genre_label, motion_label = "", ""
    gender_label = item.gender if item.genre in ("トップス", "ボトムス") and item.gender else ""

    tail = genre_label or motion_label
    if web:
        # 原版のWeb出品タイトル順: 性別 -> ジャンル（その他は動作確認）
        ordered = [gender_label, tail]
    else:
        # 原版のGUI表示順: ジャンル（その他は動作確認）-> 性別
        ordered = [tail, gender_label]
    parts.extend(" " + token for token in ordered if token)
    return base + "".join(parts)


def title_length(text: str) -> float:
    """全角1・半角0.5でカウントする。"""

    total = 0.0
    for ch in text:
        total += 1.0 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 0.5
    return total


def build_web_description(item: Item, config: AppConfig, *,
                          multiline: bool = False) -> str:
    """商品説明HTML。

    ``multiline=False``（CSV用）… 一括アップロードはフィールド内の改行を受け付けない
      ため、テンプレートの改行（\\n）は半角スペースに畳んで1物理行にする。
    ``multiline=True``（出品ページの説明欄に直接入れる用）… 改行を残す。
    出品ページ上の改行は HTML の <BR> タグが担うので見た目はどちらも同じ。
    """

    shop = config.shop(item.shop)
    html = DESCRIPTION_TEMPLATE.format(
        rank=item.rank,
        brand=item.brand,
        name=item.name,
        condition=item.condition_text,
        notated=item.notated_size or "-",
        measurements=measurement_html(item),
        color=item.color or "-",
        shop=item.shop,
        images=shop.images,
    )
    return html if multiline else html.replace("\n", " ")


def build_tag_info(item: Item) -> str:
    """値札の商品情報欄（スラッシュ区切り）。"""

    text = ""
    if item.notated_size:
        text += "サイズ" + item.notated_size
    if item.tag_condition:
        text += "/" + re.sub(r"[ 　、]+", "/", item.tag_condition)
    if item.motion:
        text += "/" + item.motion
    if item.gender == "レディース":
        text += "/レディース"
    text += "/" + item.situation + "/オーク"
    return text


# ---------------------------------------------------------------------------
# 値札出力
# ---------------------------------------------------------------------------

def _set_cell(cell, value) -> None:
    """セルに値を書く。ezodf の :meth:`set_value` はセルの子要素を全消しするため、
    セルにアンカーされた画像（``draw:frame`` = 「ネット販売中」等）まで消えてしまう。
    書き込み前に図形を退避し、あとで元の並び順（テキストより前）に戻す。
    """

    node = cell.xmlnode
    shapes = [child for child in node
              if isinstance(child.tag, str) and child.tag.split("}")[-1] == "frame"]
    cell.set_value(value)
    for index, shape in enumerate(shapes):
        node.insert(index, shape)


def _price_tag_block(position: int) -> tuple[int, int]:
    """シート内の1始まり位置 -> (行オフセット, データ列)。"""

    for min_pos, col in PRICE_TAG_BLOCKS:
        if position >= min_pos:
            return (position - min_pos) * 7, col
    raise ValueError(f"不正な値札位置: {position}")


def write_price_tags(items: list[Item], config: AppConfig,
                     out_dir: str | None = None, *,
                     template_path: str | None = None) -> str:
    """値札テンプレートを複製し、商品データを書き込んで保存パスを返す。

    template_path 省略時は src/ のテンプレート、out_dir 省略時は output/ を使う。
    """

    import ezodf

    template = template_path or default_template_path(config)
    if not os.path.isfile(template):
        raise FileNotFoundError(f"値札テンプレートが見つかりません: {template}")
    out_dir = out_dir or output_dir()

    doc = ezodf.opendoc(template)
    total = len(items)
    required = (total - 1) // ITEMS_PER_SHEET + 1 if total else 1
    available = len(doc.sheets) - config.base_sheet_index
    if required > available:
        raise ValueError(
            f"{total}件の値札出力には{required}タブ必要ですが、"
            f"{config.price_tag_filename} には{available}タブしかありません。"
            f"タブを{required - available}つ追加してください"
            f"（1タブあたり最大{ITEMS_PER_SHEET}件）。"
        )

    year, month, day = today_ymd()
    for seq, item in enumerate(items, start=1):
        # 21件目以降は次のタブへ折り返す
        sheet = doc.sheets[config.base_sheet_index + (seq - 1) // ITEMS_PER_SHEET]
        position = (seq - 1) % ITEMS_PER_SHEET + 1
        row, data_col = _price_tag_block(position)
        label_col = data_col + 1

        shop = config.shop(item.shop)
        c_num = int(management_number(shop.shop_id, year, month, day, seq))
        c_price = int(item.price)
        c_name = re.sub(r"[ 　、]+", "/", item.name)
        c_info = build_tag_info(item)

        _set_cell(sheet[row + 0, data_col], item.brand)
        _set_cell(sheet[row + 1, data_col], c_num)
        _set_cell(sheet[row + 2, data_col], c_price)
        _set_cell(sheet[row + 2, label_col], item.rank)
        _set_cell(sheet[row + 4, data_col], c_name)
        _set_cell(sheet[row + 5, data_col], c_info)

    # 出力先は常に固定名。実行のたび同じファイルを上書き更新する（.bak は作らない）。
    out_path = os.path.join(out_dir, config.price_tag_filename)
    doc.backup = False
    try:
        doc.saveas(out_path)
    except PermissionError:
        raise ValueError(
            f"{config.price_tag_filename} が開かれています。閉じてから再実行してください。"
        )
    return out_path


# ---------------------------------------------------------------------------
# ヤフオク一括出品CSV
# ---------------------------------------------------------------------------

def build_auction_row(item: Item, config: AppConfig, seq: int,
                      ymd: tuple[int, int, int]) -> list[str]:
    """商品1件を CSV の1行（53要素）にする。"""

    shop = config.shop(item.shop)
    year, month, day = ymd
    row = [
        management_number(shop.shop_id, year, month, day, seq),  # 管理番号
        AUCTION_CATEGORY_ID,                                     # カテゴリ
        build_title(item, config, web=True),                     # タイトル
        build_web_description(item, config),                     # 説明
        shop.store_keyword,                                      # ストア内商品検索用キーワード
        item.price,                                              # 開始価格
        "0",                                                    # 即決価格
        "1",                                                    # 個数
        AUCTION_DURATION,                                        # 期間
        AUCTION_END_TIME,                                        # 終了時間
        shop.prefecture_name,                                    # 商品発送元の都道府県
        shop.city,                                               # 商品発送元の市区町村
        "落札者",                                                # 送料負担
        "代金先払い",                                            # 代金先払い、後払い
        YAHOO_CONDITION_CSV.get(item.rank2, item.rank2),         # 商品の状態
    ]
    row += [""] * 20                                             # 画像1..10 + コメント
    row += [
        "-5",       # 最低評価
        "いいえ",    # 悪評割合制限
        "いいえ",    # 入札者認証制限
        "はい",      # 自動延長
        AUCTION_RESUBMIT,  # 商品の自動再出品
        "",         # 自動値下げ
        "0",        # 注目のオークション
        "",         # 重量設定
        "10",       # 消費税設定
        "いいえ",    # 税込みフラグ
        "",         # JANコード・ISBNコード
        "",         # ブランドID
        "",         # 商品スペックサイズ種別
        "",         # 商品スペックサイズID
        "",         # 商品分類ID
        shop.folder_path,                                # 商品保存先フォルダパス
        AUCTION_DELIVERY_GROUP.get(item.postage, ""),    # 配送グループ
        AUCTION_LEAD_TIME,                               # 発送までの日数
    ]
    assert len(row) == len(AUCTION_CSV_HEADER), len(row)
    return row


def export_auction_csv(items: list[Item], config: AppConfig,
                       out_dir: str | None = None) -> str:
    """商品一覧をヤフオク一括出品CSV（Shift-JIS / CRLF）に書き出し、パスを返す。

    ファイル名は ``auctions_YYYYMMDD.csv``。同じ日に出力し直すと同じファイルを
    上書き更新し、日付が変わると新しいファイルになる。
    """

    if not items:
        raise ValueError("出力する商品がありません。")

    out_dir = out_dir or output_dir()
    ymd = today_ymd()
    rows = [build_auction_row(item, config, seq, ymd)
            for seq, item in enumerate(items, start=1)]

    out_path = os.path.join(out_dir, f"auctions_{'%04d%02d%02d' % ymd}.csv")
    try:
        with open(out_path, "w", encoding=AUCTION_CSV_ENCODING,
                  errors="replace", newline="") as fp:
            writer = csv.writer(fp, lineterminator="\r\n")
            writer.writerow(AUCTION_CSV_HEADER)
            writer.writerows(rows)
    except PermissionError:
        raise ValueError(
            f"{os.path.basename(out_path)} が開かれています。閉じてから再実行してください。"
        )
    return out_path


# ---------------------------------------------------------------------------
# 設定ファイル
# ---------------------------------------------------------------------------

def settings_file_path(config: AppConfig, base_dir: str | None = None) -> str:
    # 設定は exe の隣に固定（出力先は GUI で変わるのでそこには置かない）
    return os.path.join(base_dir or PROJECT_DIR, f"{config.name}_settings.json")


def load_settings(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class EcBridgeApp:
    """商品入力 GUI。"""

    def __init__(self, root: tk.Tk, config: AppConfig, *,
                 out_dir: str | None = None,
                 settings_dir: str | None = None) -> None:
        self.root = root
        self.config = config
        # 出力先の初期値。None なら初回起動時は空欄（利用者が「参照」で選ぶ）。
        self._default_out_dir = out_dir
        self.settings_path = settings_file_path(config, settings_dir)
        self.settings = load_settings(self.settings_path)

        self.items: list[Item] = []
        self.index = 0                       # 0..len(items)。len は新規未保存
        self._loading = False
        self._measure_widgets: list[tk.Widget] = []

        root.title(config.window_title)
        self._build_vars()
        self._build_widgets()
        self._wire_traces()

        self._update_measurement_panel()
        self._refresh_title()
        self._refresh_condition()
        self._refresh_counter()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- 変数 ---------------------------------------------------------------

    def _build_vars(self) -> None:
        s = self.settings
        self.v_shop = tk.StringVar(value=s.get("last_shop", self.config.default_shop))
        if self.v_shop.get() not in SHOP_NAMES:
            self.v_shop.set(self.config.default_shop)

        saved_out = s.get("output_dir")
        self.v_output_dir = tk.StringVar(
            value=saved_out if saved_out and os.path.isdir(saved_out)
            else (self._default_out_dir or ""))
        # 出品（Selenium）で使う Firefox プロファイル。競りナビにログイン済みのもの。
        self.v_firefox_profile = tk.StringVar(value=s.get("firefox_profile", ""))

        self.v_brand = tk.StringVar()
        self.v_brand_kana = tk.StringVar()
        self.v_name = tk.StringVar()
        self.v_color = tk.StringVar()
        self.v_price = tk.StringVar()
        self.v_gender = tk.StringVar(value="")
        self.v_genre = tk.StringVar(value=GENRE_PLACEHOLDER)
        self.v_situation = tk.StringVar(value=DEFAULT_SITUATION)
        self.v_rank = tk.StringVar(value=DEFAULT_RANK)
        self.v_rank2 = tk.StringVar(value=DEFAULT_RANK2)
        self.v_tag_condition = tk.StringVar()
        self.v_condition = tk.StringVar()
        self.v_postage = tk.StringVar(value=DEFAULT_POSTAGE)
        self.v_notated = tk.StringVar()
        self.v_motion = tk.StringVar(value="")
        self.v_m1 = tk.StringVar()
        self.v_m2 = tk.StringVar()
        self.v_m3 = tk.StringVar()
        self.v_m4 = tk.StringVar()

        self.v_title = tk.StringVar()
        self.v_charcount = tk.StringVar(value=f"文字数: 0.0/{TITLE_CHAR_LIMIT}")
        self.v_counter = tk.StringVar(value="1/1")
        self.v_error = tk.StringVar(value="")

    # -- ウィジェット -----------------------------------------------------

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)
        self.frame = frame
        r = 0

        ttk.Label(frame, text=format_display_date(*today_ymd()),
                  font=("Helvetica", 16)).grid(row=r, column=1, sticky="w", pady=(0, 6))
        r += 1

        ttk.Label(frame, text="商品番号", padding=6).grid(row=r, column=0, sticky="e")
        ttk.Label(frame, textvariable=self.v_counter).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frame, text="取扱店舗", padding=6).grid(row=r, column=0, sticky="e")
        shop_cb = ttk.Combobox(frame, state="readonly", textvariable=self.v_shop,
                               values=SHOP_NAMES, width=12)
        shop_cb.grid(row=r, column=1, sticky="w")
        self._bind_combo(shop_cb)
        r += 1

        ttk.Label(frame, text="出力先", padding=6).grid(row=r, column=0, sticky="e")
        out_box = ttk.Frame(frame)
        out_box.grid(row=r, column=1, sticky="w")
        ttk.Entry(out_box, textvariable=self.v_output_dir, width=58).pack(side="left")
        ttk.Button(out_box, text="参照", command=self._browse_output_dir).pack(
            side="left", padx=4)
        r += 1

        ttk.Label(frame, text="Firefoxプロファイル", padding=6).grid(
            row=r, column=0, sticky="e")
        ff_box = ttk.Frame(frame)
        ff_box.grid(row=r, column=1, sticky="w")
        ttk.Entry(ff_box, textvariable=self.v_firefox_profile, width=58).pack(side="left")
        ttk.Button(ff_box, text="参照", command=self._browse_firefox_profile).pack(
            side="left", padx=4)
        ttk.Label(ff_box, text="←出品(競りナビ)で使用").pack(side="left", padx=4)
        r += 1

        for label, var, width in (
            ("商品ブランド(メーカー)", self.v_brand, 40),
            ("カタカナ", self.v_brand_kana, 40),
            ("商品名(値札1行目)", self.v_name, 40),
            ("カラー", self.v_color, 20),
        ):
            ttk.Label(frame, text=label, padding=6).grid(row=r, column=0, sticky="e")
            ttk.Entry(frame, textvariable=var, width=width).grid(row=r, column=1, sticky="w")
            r += 1

        ttk.Label(frame, text="ネット出品タイトル", padding=6).grid(row=r, column=0, sticky="e")
        title_box = ttk.Frame(frame)
        title_box.grid(row=r, column=1, sticky="w")
        title_entry = ttk.Entry(title_box, textvariable=self.v_title, width=80,
                                state="readonly")
        title_entry.pack(side="left")
        ttk.Label(title_box, textvariable=self.v_charcount).pack(side="left", padx=8)
        r += 1

        ttk.Label(frame, text="値段", padding=6).grid(row=r, column=0, sticky="e")
        price_box = ttk.Frame(frame)
        price_box.grid(row=r, column=1, sticky="w")
        digits_only = (self.root.register(_is_digits_or_empty), "%P")
        self.price_entry = ttk.Entry(price_box, textvariable=self.v_price, width=10,
                                     validate="key", validatecommand=digits_only)
        self.price_entry.pack(side="left")
        ttk.Label(price_box, text="円").pack(side="left", padx=(4, 0))
        r += 1

        ttk.Label(frame, text="性別", padding=6).grid(row=r, column=0, sticky="e")
        self._radio_group(frame, r, self.v_gender,
                          [("記入無し", ""), ("メンズ", "メンズ"), ("レディース", "レディース")])
        r += 1

        ttk.Label(frame, text="商品ジャンル", padding=6).grid(row=r, column=0, sticky="e")
        genre_cb = ttk.Combobox(frame, state="readonly", textvariable=self.v_genre,
                                values=[GENRE_PLACEHOLDER] + GENRES, width=14)
        genre_cb.grid(row=r, column=1, sticky="w")
        self._bind_combo(genre_cb)
        r += 1

        self.measure_frame = ttk.Frame(frame)
        self.measure_frame.grid(row=r, column=1, sticky="w", pady=2)
        r += 1

        ttk.Label(frame, text="商品状態", padding=6).grid(row=r, column=0, sticky="e")
        state_box = ttk.Frame(frame)
        state_box.grid(row=r, column=1, sticky="w")
        sit_cb = ttk.Combobox(state_box, state="readonly", textvariable=self.v_situation,
                              values=SITUATIONS, width=15)
        rank_cb = ttk.Combobox(state_box, state="readonly", textvariable=self.v_rank,
                               values=RANKS, width=5)
        rank2_cb = ttk.Combobox(state_box, state="readonly", textvariable=self.v_rank2,
                                values=RANK2S, width=18)
        for cb in (sit_cb, rank_cb, rank2_cb):
            cb.pack(side="left", padx=(0, 6))
            self._bind_combo(cb)
        ttk.Entry(state_box, textvariable=self.v_tag_condition, width=12).pack(side="left")
        ttk.Label(state_box, text="←値札用状態 例:使用感、黄ばみ").pack(side="left", padx=4)
        r += 1

        ttk.Label(frame, text="状態説明文", padding=6).grid(row=r, column=0, sticky="e")
        ttk.Entry(frame, textvariable=self.v_condition, width=90).grid(
            row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frame, text="送料", padding=6).grid(row=r, column=0, sticky="e")
        self._radio_group(frame, r, self.v_postage,
                          [(p, p) for p in POSTAGES])
        r += 1

        btns = ttk.Frame(frame)
        btns.grid(row=r, column=1, sticky="w", pady=6)
        for text, cmd in (("前へ", self.on_prev), ("次へ", self.on_next),
                          ("複製", self.on_duplicate), ("削除", self.on_delete),
                          ("値札出力", self.on_price_tags),
                          ("出品", self.on_publish)):
            ttk.Button(btns, text=text, command=cmd).pack(side="left", padx=4)
        r += 1

        ttk.Label(frame, textvariable=self.v_error, foreground="#ff0000").grid(
            row=r, column=1, sticky="w")

    def _radio_group(self, parent, row, var, options) -> None:
        box = ttk.Frame(parent)
        box.grid(row=row, column=1, sticky="w")
        for text, value in options:
            rb = ttk.Radiobutton(box, text=text, value=value, variable=var, padding=6)
            rb.pack(side="left")
            rb.bind("<Return>", lambda e: (e.widget.invoke(), "break"))

    def _bind_combo(self, cb: ttk.Combobox) -> None:
        cb.bind("<Return>", lambda e: (cb.event_generate("<Button-1>"), "break")[-1])
        cb.bind("<Down>", lambda e: "break")

    # -- トレース ---------------------------------------------------------

    def _wire_traces(self) -> None:
        for var in (self.v_brand, self.v_brand_kana, self.v_name, self.v_color,
                    self.v_notated, self.v_gender, self.v_genre, self.v_motion,
                    self.v_situation):
            var.trace_add("write", self._refresh_title)
        for var in (self.v_situation, self.v_tag_condition, self.v_motion, self.v_genre):
            var.trace_add("write", self._refresh_condition)
        self.v_genre.trace_add("write", self._update_measurement_panel)
        self.v_title.trace_add("write", self._refresh_char_count)
        self.v_shop.trace_add("write", self._save_settings)
        self.v_output_dir.trace_add("write", self._save_settings)
        self.v_firefox_profile.trace_add("write", self._save_settings)

    # -- 動的な実寸パネル ------------------------------------------------

    def _update_measurement_panel(self, *_args) -> None:
        if self._loading:
            return
        for widget in self._measure_widgets:
            widget.destroy()
        self._measure_widgets = []
        frame = self.measure_frame
        genre = self.v_genre.get()

        lbl = ttk.Label(frame, text="表記サイズ", padding=6)
        ent = ttk.Entry(frame, textvariable=self.v_notated, width=12)
        lbl.grid(row=0, column=0, sticky="w")
        ent.grid(row=0, column=1, sticky="w")
        self._measure_widgets += [lbl, ent]

        if genre == "その他":
            mlbl = ttk.Label(frame, text="動作確認", padding=6)
            mcb = ttk.Combobox(frame, state="readonly", textvariable=self.v_motion,
                               values=MOTIONS, width=18)
            mlbl.grid(row=1, column=0, sticky="w")
            mcb.grid(row=1, column=1, sticky="w")
            self._bind_combo(mcb)
            self._measure_widgets += [mlbl, mcb]
            return

        labels = GENRE_MEASUREMENTS.get(genre, [])
        if not labels:
            return
        head = ttk.Label(frame, text="実寸サイズ", padding=6)
        head.grid(row=1, column=0, sticky="w")
        self._measure_widgets.append(head)
        mvars = [self.v_m1, self.v_m2, self.v_m3, self.v_m4]
        for i, ((_html, gui), var) in enumerate(zip(labels, mvars)):
            row = 1 + i // 2
            col = 1 + (i % 2) * 3
            name_lbl = ttk.Label(frame, text=f"{gui}:")
            value_entry = ttk.Entry(frame, textvariable=var, width=8)
            unit_lbl = ttk.Label(frame, text="cm")
            name_lbl.grid(row=row, column=col, sticky="e", padx=(10, 0))
            value_entry.grid(row=row, column=col + 1, sticky="w")
            unit_lbl.grid(row=row, column=col + 2, sticky="w")
            self._measure_widgets += [name_lbl, value_entry, unit_lbl]

    # -- 再計算 ----------------------------------------------------------

    def _refresh_title(self, *_args) -> None:
        if self._loading:
            return
        self.v_title.set(build_title(self._collect(), self.config, web=False))

    def _refresh_condition(self, *_args) -> None:
        if self._loading:
            return
        note = join_tag_note(self.v_tag_condition.get())
        self.v_condition.set(self.config.condition_text(
            self.v_situation.get(), note, self.v_motion.get(), self.v_genre.get()))

    def _refresh_char_count(self, *_args) -> None:
        length = title_length(self.v_title.get())
        self.v_charcount.set(f"文字数: {length:.1f}/{TITLE_CHAR_LIMIT}")

    def _refresh_counter(self) -> None:
        shown = self.index + 1
        self.v_counter.set(f"{shown}/{max(len(self.items), shown)}")

    def _show_error(self, message: str) -> None:
        self.v_error.set(message)

    def _clear_error(self) -> None:
        self.v_error.set("")

    # -- データ入出力 --------------------------------------------------

    def _collect(self) -> Item:
        return Item(
            shop=self.v_shop.get(),
            brand=self.v_brand.get(),
            brand_kana=self.v_brand_kana.get(),
            name=self.v_name.get(),
            color=self.v_color.get(),
            price=self.v_price.get(),
            gender=self.v_gender.get(),
            genre=self.v_genre.get(),
            situation=self.v_situation.get(),
            rank=self.v_rank.get(),
            rank2=self.v_rank2.get(),
            tag_condition=self.v_tag_condition.get(),
            condition_text=self.v_condition.get(),
            postage=self.v_postage.get(),
            notated_size=self.v_notated.get(),
            motion=self.v_motion.get(),
            m1=self.v_m1.get(), m2=self.v_m2.get(),
            m3=self.v_m3.get(), m4=self.v_m4.get(),
        )

    def _load(self, item: Item) -> None:
        self._loading = True
        try:
            self.v_shop.set(item.shop or self.config.default_shop)
            self.v_brand.set(item.brand)
            self.v_brand_kana.set(item.brand_kana)
            self.v_name.set(item.name)
            self.v_color.set(item.color)
            self.v_price.set(item.price)
            self.v_gender.set(item.gender)
            self.v_genre.set(item.genre)
            self.v_situation.set(item.situation)
            self.v_rank.set(item.rank)
            self.v_rank2.set(item.rank2)
            self.v_tag_condition.set(item.tag_condition)
            self.v_postage.set(item.postage)
            self.v_notated.set(item.notated_size)
            self.v_motion.set(item.motion)
            self.v_m1.set(item.m1)
            self.v_m2.set(item.m2)
            self.v_m3.set(item.m3)
            self.v_m4.set(item.m4)
        finally:
            self._loading = False
        self._update_measurement_panel()
        self._refresh_title()
        self._refresh_condition()
        if item.condition_text:
            self._loading = True
            self.v_condition.set(item.condition_text)
            self._loading = False
        self._refresh_counter()

    def _clear_fields(self) -> None:
        self._loading = True
        try:
            for var in (self.v_brand, self.v_brand_kana, self.v_name, self.v_color,
                        self.v_price, self.v_tag_condition, self.v_notated,
                        self.v_m1, self.v_m2, self.v_m3, self.v_m4):
                var.set("")
            self.v_gender.set("")
            self.v_genre.set(GENRE_PLACEHOLDER)
            self.v_situation.set(DEFAULT_SITUATION)
            self.v_rank.set(DEFAULT_RANK)
            self.v_rank2.set(DEFAULT_RANK2)
            self.v_postage.set(DEFAULT_POSTAGE)
            self.v_motion.set("")
        finally:
            self._loading = False
        self._update_measurement_panel()
        self._refresh_title()
        self._refresh_condition()
        self._refresh_counter()

    def _current_is_blank(self) -> bool:
        item = self._collect()
        filled = any((item.brand, item.brand_kana, item.name, item.color, item.price,
                      item.notated_size, item.m1, item.m2, item.m3, item.m4))
        return not filled and item.genre == GENRE_PLACEHOLDER

    def _save_current(self) -> None:
        if self.index < len(self.items):
            self.items[self.index] = self._collect()
        elif not self._current_is_blank():
            self.items.append(self._collect())

    def _validate(self) -> bool:
        self._clear_error()
        if not self.v_price.get().isdigit():
            self._show_error("値段を入力してください")
            return False
        if self.v_genre.get() == GENRE_PLACEHOLDER:
            self._show_error("ジャンルを選択してください")
            return False
        return True

    def _prepare_for_output(self) -> bool:
        """値札出力 / CSV出力の前処理。出力してよければ True。

        空の新規スロットを表示中なら、その画面は検証せず保存済み商品を出力する。
        """

        self._clear_error()
        if self.index >= len(self.items) and self._current_is_blank():
            if not self.items:
                self._show_error("出力する商品がありません")
                return False
            return True
        if not self._validate():
            return False
        self._save_current()
        return True

    # -- ボタン操作 ----------------------------------------------------

    def on_next(self) -> None:
        if not self._validate():
            return
        self._save_current()
        self.index += 1
        if self.index < len(self.items):
            self._load(self.items[self.index])
        else:
            self._clear_fields()
        self._refresh_counter()

    def on_prev(self) -> None:
        self._clear_error()
        if self.index == 0:
            self._show_error("前のデータは存在しません")
            return
        if not (self.index >= len(self.items) and self._current_is_blank()):
            # 甘めの補正（原版準拠）: 未入力の値段/ジャンルを既定値に寄せて保存
            if not self.v_price.get().isdigit():
                self.v_price.set("0")
            if self.v_genre.get() == GENRE_PLACEHOLDER:
                self.v_genre.set("その他")
            self._save_current()
        self.index -= 1
        self._load(self.items[self.index])
        self._refresh_counter()

    def on_duplicate(self) -> None:
        """現在のデータを次の位置に複製する。以降の商品は1つずつ後ろへずれる。"""

        self._clear_error()
        if self.index >= len(self.items):
            if self._current_is_blank():
                self._show_error("複製するデータがありません")
                return
            self.items.append(self._collect())          # 新規入力中ならまず確定
        else:
            self.items[self.index] = self._collect()     # 画面の編集を反映
        self.items.insert(self.index + 1, replace(self.items[self.index]))
        self.index += 1
        self._load(self.items[self.index])
        self._refresh_counter()

    def on_delete(self) -> None:
        self._clear_error()
        if not self.items or self.index >= len(self.items):
            self._show_error("削除するデータが存在しません")
            return
        del self.items[self.index]
        if self.items:
            self.index = min(self.index, len(self.items) - 1)
            self._load(self.items[self.index])
        else:
            self.index = 0
            self._clear_fields()
        self._refresh_counter()

    def _output_target(self) -> str | None:
        """出力先フォルダ。無ければ作成を試み、駄目ならエラー表示して None。"""

        path = self.v_output_dir.get().strip()
        if not path:
            self._show_error("出力先フォルダを指定してください")
            return None
        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except OSError:
                self._show_error(f"出力先フォルダが不正です: {path}")
                return None
        return path

    def on_price_tags(self) -> None:
        if not self._prepare_for_output():
            return
        out_dir = self._output_target()
        if out_dir is None:
            return
        try:
            out_path = write_price_tags(self.items, self.config, out_dir)
        except (ValueError, FileNotFoundError) as exc:
            messagebox.showerror("エラー", str(exc))
            return
        except Exception:
            messagebox.showerror("エラー", "値札出力に失敗しました。\n\n" + traceback.format_exc())
            return
        try:
            os.startfile(out_path)  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            messagebox.showinfo("完了", f"値札を出力しました:\n{out_path}")

    def on_export_csv(self) -> None:
        if not self._prepare_for_output():
            return
        out_dir = self._output_target()
        if out_dir is None:
            return
        try:
            out_path = export_auction_csv(self.items, self.config, out_dir)
        except ValueError as exc:
            messagebox.showerror("エラー", str(exc))
            return
        except Exception:
            messagebox.showerror(
                "エラー", "CSV出力に失敗しました。\n\n" + traceback.format_exc())
            return
        try:
            os.startfile(out_path)  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            messagebox.showinfo("完了", f"CSVを出力しました:\n{out_path}")

    def on_publish(self) -> None:
        """CSVを出力し、Selenium で競りナビへ一括アップロード＋説明整形する。"""

        if not self._prepare_for_output():
            return
        out_dir = self._output_target()
        if out_dir is None:
            return

        profile = self.v_firefox_profile.get().strip()
        if not profile or not os.path.isdir(profile):
            messagebox.showerror(
                "エラー",
                "Firefoxプロファイルフォルダを指定してください。\n"
                "競りナビにログイン済みのプロファイルを「参照」から選びます。")
            return

        try:
            csv_path = export_auction_csv(self.items, self.config, out_dir)
        except ValueError as exc:
            messagebox.showerror("エラー", str(exc))
            return
        except Exception:
            messagebox.showerror(
                "エラー", "CSV出力に失敗しました。\n\n" + traceback.format_exc())
            return

        if not messagebox.askokcancel(
                "確認",
                "Firefoxを起動して競りナビへ出品します。\n"
                f"対象: {len(self.items)}件\nCSV: {csv_path}\n\nよろしいですか？"):
            return

        try:
            import serinavi
        except ImportError:
            messagebox.showerror(
                "エラー", "Selenium が見つかりません。開発環境では pip install selenium。")
            return

        try:
            failures = serinavi.publish(
                self.items, self.config, csv_path,
                geckodriver_path=default_geckodriver_path(),
                profile_dir=profile,
                confirm=lambda m: messagebox.askokcancel("確認", m))
        except ValueError as exc:
            messagebox.showerror("エラー", str(exc))
            return
        except Exception:
            messagebox.showerror(
                "エラー", "出品処理に失敗しました。\n\n" + traceback.format_exc())
            return

        if failures:
            messagebox.showwarning(
                "一部失敗",
                "次の商品は説明の更新に失敗しました（CSV分は登録済みの可能性あり）:\n\n"
                + "\n".join(failures))
        else:
            messagebox.showinfo("完了", f"{len(self.items)}件を出品しました。")

    # -- その他 -------------------------------------------------------

    def _browse_output_dir(self) -> None:
        current = self.v_output_dir.get().strip()
        initial = current if os.path.isdir(current) else (self._default_out_dir
                                                          or PROJECT_DIR)
        chosen = filedialog.askdirectory(title="出力先フォルダを選択",
                                         initialdir=initial)
        if chosen:
            self.v_output_dir.set(os.path.normpath(chosen))

    def _browse_firefox_profile(self) -> None:
        current = self.v_firefox_profile.get().strip()
        initial = current if os.path.isdir(current) else PROJECT_DIR
        chosen = filedialog.askdirectory(
            title="Firefoxプロファイルフォルダを選択", initialdir=initial)
        if chosen:
            self.v_firefox_profile.set(os.path.normpath(chosen))

    def _save_settings(self, *_args) -> None:
        if self._loading:
            return
        save_settings(self.settings_path, {
            "last_shop": self.v_shop.get(),
            "output_dir": self.v_output_dir.get(),
            "firefox_profile": self.v_firefox_profile.get(),
        })

    def _on_close(self) -> None:
        if messagebox.askokcancel(
                "確認", "アプリケーションを閉じますか？入力されたデータは失われます。"):
            self._save_settings()
            self.root.destroy()


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def run(config: AppConfig) -> None:
    root = tk.Tk()
    EcBridgeApp(root, config)
    root.mainloop()


