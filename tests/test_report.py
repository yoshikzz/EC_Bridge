# -*- coding: utf-8 -*-
"""単体テストを実行し、結果を Excel(.xlsx) のチェックリストとして出力する。

使い方::

    python test_report.py                # テスト実行 + テスト結果.xlsx を生成
    python test_report.py --open         # 生成後に Excel/Calc で開く

出力シート:
  - テスト項目一覧 : 1テスト = 1行。合格すると「クリア」列に ✓（緑）が自動で付く。
  - サマリ         : 全体集計と分類別の集計。
  - カバレッジ     : 機能領域ごとに「テストが存在し、かつ全て合格しているか」を表示。
                     テストが無い領域は ✗ で警告する（＝網羅漏れの検出）。

依存ライブラリ不要（mini_xlsx を同梱）。
"""

from __future__ import annotations

import argparse
import io
import os
import platform
import sys
import time
import unittest
from datetime import datetime

from mini_xlsx import Workbook

TEST_MODULE = "test_ec_bridge_core"
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# ---------------------------------------------------------------------------
# 機能領域（この一覧すべてにテストが存在することを網羅性の基準とする）
# ---------------------------------------------------------------------------

REQUIRED_AREAS = [
    "管理番号生成",
    "タイトル生成（GUI / Web）",
    "状態説明文生成",
    "実寸サイズ表示",
    "値札情報欄",
    "商品説明HTML",
    "値札セル配置",
    "値札ファイル出力",
    "ヤフオクCSV出力",
    "店舗マスタ / 定数",
    "設定ファイル入出力",
    "GUI: 画面遷移",
    "GUI: 入力バリデーション",
    "GUI: 実寸パネル",
    "GUI: タイトル / 文字数表示",
    "GUI: 設定連携",
    "GUI: 出力先フォルダ",
    "GUI: 選択肢の状態反映",
    "GUI: ボタン操作（外部連携）",
    "GUI: マルチ店舗フロー",
    "GUI: 複製",
    "出品 / 競りナビ連携",
    "配布 / インストーラ",
    "ヘルパー関数",
    "意図的仕様変更の固定",
]

# テストクラス -> 既定の機能領域（TEST_META に無いテストのフォールバック）
AREA_BY_CLASS = {
    "IntentionalChangeTests": "意図的仕様変更の固定",
    "PriceTagTests": "値札ファイル出力",
    "SettingsTests": "設定ファイル入出力",
    "MasterDataTests": "店舗マスタ / 定数",
    "RegressionTests": "意図的仕様変更の固定",
    "HelperTests": "ヘルパー関数",
    "DescriptionEdgeTests": "商品説明HTML",
    "GuiSmokeTests": "GUI: 画面遷移",
    "GuiExtraTests": "GUI: 画面遷移",
    "GuiMeasurementPanelTests": "GUI: 実寸パネル",
    "GuiChoiceReflectionTests": "GUI: 選択肢の状態反映",
    "GuiChoiceReflectionKanmeTests": "GUI: 選択肢の状態反映",
    "GuiActionTests": "GUI: ボタン操作（外部連携）",
    "GuiMultiShopTests": "GUI: マルチ店舗フロー",
    "GuiDuplicateTests": "GUI: 複製",
    "GuiOutputDirTests": "GUI: 出力先フォルダ",
    "AuctionCsvTests": "ヤフオクCSV出力",
    "InstallerTests": "配布 / インストーラ",
    "SerinaviParseTests": "出品 / 競りナビ連携",
    "GuiPublishTests": "出品 / 競りナビ連携",
    "DescriptionMultilineTests": "商品説明HTML",
}

# テストID -> (機能領域, 日本語のテスト内容)
TEST_META: dict[str, tuple[str, str]] = {
    "DescriptionEdgeTests.test_condition_and_brand_line_present":
        ("商品説明HTML", "説明HTMLに「ブランド 品名です。」＋状態文が入る"),
    "DescriptionEdgeTests.test_description_has_no_newlines":
        ("商品説明HTML", "説明列は改行を含まない1物理行（競りナビが改行を弾くため）"),
    "DescriptionEdgeTests.test_dash_fallback_for_empty_notated_and_color":
        ("商品説明HTML", "表記サイズ・カラーが空なら説明HTMLで「-」表示"),
    "DescriptionEdgeTests.test_tag_info_leading_slash_when_size_empty":
        ("値札情報欄", "表記サイズ空欄時の値札情報欄の先頭スラッシュ（旧仕様維持）"),
    "GuiExtraTests.test_char_count_value":
        ("GUI: タイトル / 文字数表示", "文字数カウント表示が「文字数: 4.0/65」形式"),
    "GuiExtraTests.test_clear_fields_resets_defaults":
        ("GUI: 画面遷移", "入力クリアで各項目が既定値へ戻る"),
    "GuiExtraTests.test_condition_recomputes_on_situation_change":
        ("GUI: タイトル / 文字数表示", "商品状態・値札メモ変更で状態説明文が再生成される"),
    "GuiExtraTests.test_delete_middle_keeps_others_in_order":
        ("GUI: 画面遷移", "中間の商品を削除しても他の順序が保たれる"),
    "GuiExtraTests.test_other_genre_shows_motion_combobox_not_measurements":
        ("GUI: 実寸パネル", "ジャンル「その他」で実寸欄でなく動作確認コンボを表示"),
    "GuiExtraTests.test_prev_at_first_shows_error":
        ("GUI: 入力バリデーション", "先頭で「前へ」→「前のデータは存在しません」"),
    "GuiExtraTests.test_web_title_via_collect":
        ("タイトル生成（GUI / Web）", "GUI入力から生成したWeb出品タイトル"),
    "GuiSmokeTests.test_delete_removes_current":
        ("GUI: 画面遷移", "「削除」で現在の商品が一覧から除かれる"),
    "GuiSmokeTests.test_delete_with_no_items_shows_error":
        ("GUI: 入力バリデーション", "商品ゼロ件で「削除」→「削除するデータが存在しません」"),
    "GuiSmokeTests.test_edit_existing_item_persists":
        ("GUI: 画面遷移", "既存商品の編集内容が保持される"),
    "GuiSmokeTests.test_measurement_panel_rebuilds_on_genre_change":
        ("GUI: 実寸パネル", "ジャンル変更で実寸入力欄が再構築される"),
    "GuiSmokeTests.test_next_saves_and_advances":
        ("GUI: 画面遷移", "「次へ」で現在の商品を保存し次の番号へ進む"),
    "GuiSmokeTests.test_prev_from_blank_new_slot_creates_no_phantom":
        ("GUI: 画面遷移", "空の新規スロットから「前へ」で幽霊アイテムを作らない"),
    "GuiSmokeTests.test_roundtrip_preserves_measurements":
        ("GUI: 実寸パネル", "前へ／次へ往復で実寸・表記サイズが失われない"),
    "GuiSmokeTests.test_settings_roundtrip":
        ("GUI: 設定連携", "店舗・プロファイルの変更が設定ファイルへ即保存される"),
    "GuiSmokeTests.test_title_and_counter_update":
        ("GUI: タイトル / 文字数表示", "入力に応じてタイトルと文字数表示が更新される"),
    "GuiSmokeTests.test_validation_blocks_next":
        ("GUI: 入力バリデーション", "値段が数字でない／ジャンル未選択で「次へ」を止める"),
    "GuiSmokeTests.test_price_field_rejects_non_digits":
        ("GUI: 入力バリデーション", "値段欄は半角数字以外を入力させない（読込時の設定は通す）"),
    "HelperTests.test_is_digits_or_empty":
        ("GUI: 入力バリデーション", "値段バリデータ：半角数字と空欄のみ許可（全角・記号・小数は不可）"),
    "HelperTests.test_item_defaults":
        ("ヘルパー関数", "Item の既定値（ジャンル未選択・中古品・ランクC 等）"),
    "HelperTests.test_join_tag_note_collapses_runs_and_trims":
        ("ヘルパー関数", "値札メモの空白連続を読点1つにまとめ前後空白を除去"),
    "HelperTests.test_management_number_is_str":
        ("管理番号生成", "管理番号が文字列型で返る"),
    "HelperTests.test_measurement_html_unknown_and_other_is_dash":
        ("実寸サイズ表示", "その他・未選択ジャンルの実寸HTMLは「-」"),
    "HelperTests.test_paths_point_at_src_and_output":
        ("ヘルパー関数", "テンプレートは src/、生成物は output/ を指す"),
    "HelperTests.test_title_length_counts_fullwidth_1_halfwidth_half":
        ("ヘルパー関数", "文字数カウント：全角1・半角0.5"),
    "HelperTests.test_title_length_matches_old_ord_rule_for_common_text":
        ("ヘルパー関数", "一般的な文字列で旧カウント規則（ord>255）と一致"),
    "IntentionalChangeTests.test_management_number_zero_pads_old_years":
        ("意図的仕様変更の固定", "西暦下2桁をゼロ埋め（旧版は桁崩れの可能性）"),
    "IntentionalChangeTests.test_price_tags_written_to_fixed_name_and_overwrites":
        ("意図的仕様変更の固定", "値札は output/ネット用値札.ods を毎回上書き（テンプレは不変）"),
    "IntentionalChangeTests.test_titles_no_stray_space_when_gender_blank":
        ("意図的仕様変更の固定", "性別「記入無し」でタイトルに余分な空白を出さない"),
    "IntentionalChangeTests.test_watch_measurement_label_fixed":
        ("意図的仕様変更の固定", "腕時計の実寸ラベル「ケース縦」二重表記を修正"),
    "IntentionalChangeTests.test_web_title_other_includes_motion":
        ("意図的仕様変更の固定", "その他＋動作確認をWebタイトルにも出力"),
    "MasterDataTests.test_delivery_group_mapping":
        ("店舗マスタ / 定数", "送料700→配送グループ1、2000→2"),
    "MasterDataTests.test_genre_measurements_keys":
        ("店舗マスタ / 定数", "ジャンル別実寸項目の定義（キー・項目数）"),
    "MasterDataTests.test_option_lists_match_original":
        ("店舗マスタ / 定数", "ランク・状態・動作確認の選択肢が旧版と一致"),
    "MasterDataTests.test_condition_csv_map_covers_all_rank2":
        ("店舗マスタ / 定数", "商品ランク6種すべてにCSV「商品の状態」表記が対応（未使用品→未使用等）"),
    "MasterDataTests.test_shop_master_matches_original":
        ("店舗マスタ / 定数", "3店舗のID・検索語・市区・都道府県・保存先フォルダパスが正しい"),
    "MasterDataTests.test_csv_header_is_53_columns":
        ("ヤフオクCSV出力", "CSVヘッダーが53列で先頭・末尾・フォルダ列が正しい"),
    "PriceTagTests.test_both_variants_start_from_first_tab":
        ("値札ファイル出力", "標準版・要町中野版とも1タブ目から書き始める"),
    "PriceTagTests.test_multi_sheet_split":
        ("値札ファイル出力", "21件目以降が次タブの先頭へ折り返す（両版）"),
    "PriceTagTests.test_capacity_is_tabs_times_20":
        ("値札ファイル出力", "ちょうどタブ数×20件まで出力できる"),
    "PriceTagTests.test_positions_span_four_columns":
        ("値札ファイル出力", "1タブ内で5件ごとに列ブロックが右へ移動"),
    "PriceTagTests.test_sheet_shortage_raises_with_helpful_message":
        ("値札ファイル出力", "タブ不足時に「タブを○つ追加」と案内する ValueError"),
    "PriceTagTests.test_single_item_cells":
        ("値札ファイル出力", "1件出力時の各セル（ブランド／管理番号／価格／ランク／品名／情報欄）"),
    "RegressionTests.test_condition_text_kanme_matches_original":
        ("状態説明文生成", "要町・中野版の状態説明文が旧実装と一致"),
    "RegressionTests.test_condition_text_medamaya_matches_original":
        ("状態説明文生成", "標準版の状態説明文が旧実装と一致"),
    "RegressionTests.test_gui_title_matches_original_for_selected_genre":
        ("タイトル生成（GUI / Web）", "ジャンル選択時のGUIタイトルが旧実装と一致"),
    "RegressionTests.test_gui_title_other_with_motion_matches_original":
        ("タイトル生成（GUI / Web）", "その他＋動作確認のGUIタイトルが旧実装と一致"),
    "RegressionTests.test_join_tag_note_no_surrounding_space":
        ("ヘルパー関数", "前後空白なしの値札メモ整形が旧実装と一致"),
    "RegressionTests.test_management_number_current_dates":
        ("管理番号生成", "現行日付・全店舗・複数連番で旧実装と一致"),
    "RegressionTests.test_measurement_html_matches_original_except_watch":
        ("実寸サイズ表示", "実寸HTML（腕時計以外）が旧実装と一致"),
    "RegressionTests.test_price_tag_cell_placement_matches_original":
        ("値札セル配置", "20位置すべてのセル座標が旧calcと一致"),
    "RegressionTests.test_shop_ids_consistent":
        ("店舗マスタ / 定数", "店舗ID 22/11/44 で一貫（旧版の33/44不整合を解消）"),
    "RegressionTests.test_tag_info_matches_original":
        ("値札情報欄", "値札情報欄の文字列が旧calcと一致"),
    "RegressionTests.test_web_description_kanme_nakano_image_override":
        ("商品説明HTML", "中野店の画像差し替え（rank.jpg）を含む説明HTML一致"),
    "RegressionTests.test_web_description_matches_original":
        ("商品説明HTML", "商品説明HTML全文が旧yahoo_auction生成と一致"),
    "RegressionTests.test_web_title_matches_original_for_non_apparel":
        ("タイトル生成（GUI / Web）", "シューズ/バッグ/腕時計のWebタイトルが旧実装と一致"),
    "RegressionTests.test_web_title_matches_original_when_gender_set":
        ("タイトル生成（GUI / Web）", "性別指定時のWebタイトル（性別→ジャンル順）が旧実装と一致"),
    "SettingsTests.test_corrupt_json_returns_empty_dict":
        ("設定ファイル入出力", "壊れたJSON設定は空dictとして読む"),
    "SettingsTests.test_missing_file_returns_empty_dict":
        ("設定ファイル入出力", "設定ファイルが無ければ空dict"),
    "SettingsTests.test_non_object_json_returns_empty_dict":
        ("設定ファイル入出力", "JSON配列など非オブジェクトは空dict"),
    "SettingsTests.test_roundtrip":
        ("設定ファイル入出力", "保存→読込で内容が一致"),
    "SettingsTests.test_settings_filename_uses_config_name":
        ("設定ファイル入出力", "設定ファイル名が config.name 由来（省略時は output/）"),
    "SettingsTests.test_make_config_variant_by_shop":
        ("配布 / インストーラ", "店舗名→設定：上池袋=標準版、要町/中野=要町中野版、不正名は上池袋"),
    "InstallerTests.test_install_creates_per_shop_layout":
        ("配布 / インストーラ", "店舗選択→EC_Bridge_<店>.exe・install.json・テンプレ・output/ を作成"),
    "InstallerTests.test_installed_config_selects_right_variant":
        ("配布 / インストーラ", "install.json の店舗で正しい文言バリアントが選ばれる"),
    # --- GuiMeasurementPanelTests ---
    "GuiMeasurementPanelTests.test_every_genre_builds_expected_panel":
        ("GUI: 実寸パネル", "6ジャンル＋未選択それぞれで実寸入力欄の数とラベルが正しい"),
    "GuiMeasurementPanelTests.test_notated_size_field_always_present":
        ("GUI: 実寸パネル", "どのジャンルでも「表記サイズ」欄が出る"),
    "GuiMeasurementPanelTests.test_measurement_values_retained_across_genre_switch":
        ("GUI: 実寸パネル", "ジャンルを切り替えて戻しても実寸値が保持される"),
    "GuiMeasurementPanelTests.test_hidden_measurement_still_collected":
        ("GUI: 実寸パネル", "欄が消えたジャンルでも入力済みの実寸値は保存される"),
    # --- GuiChoiceReflectionTests（Kanme サブクラスも同キーで再利用） ---
    "GuiChoiceReflectionTests.test_all_shops_selectable_and_saved":
        ("GUI: 選択肢の状態反映", "3店舗すべて選択でき、設定ファイルへ保存される"),
    "GuiChoiceReflectionTests.test_all_genders_reflected_in_title":
        ("GUI: 選択肢の状態反映", "性別3値がタイトル末尾に反映される（記入無しは付かない）"),
    "GuiChoiceReflectionTests.test_all_postage_values_collected":
        ("GUI: 選択肢の状態反映", "送料2値が商品データに反映される"),
    "GuiChoiceReflectionTests.test_all_ranks_collected":
        ("GUI: 選択肢の状態反映", "ランク9値すべてが商品データに反映される"),
    "GuiChoiceReflectionTests.test_all_rank2_values_collected":
        ("GUI: 選択肢の状態反映", "商品ランク6値すべてが商品データに反映される"),
    "GuiChoiceReflectionTests.test_all_situations_reflected_in_title_and_condition":
        ("GUI: 選択肢の状態反映", "商品状態11値がタイトルと状態説明文に反映される"),
    "GuiChoiceReflectionTests.test_all_motion_values_in_other_genre":
        ("GUI: 選択肢の状態反映", "その他ジャンルで動作確認7値がタイトル・説明文に反映される"),
    "GuiChoiceReflectionTests.test_kana_color_notated_feed_title":
        ("GUI: 選択肢の状態反映", "カタカナ・カラー・表記サイズがタイトルに反映される"),
    "GuiChoiceReflectionTests.test_tag_condition_spaces_become_ten":
        ("GUI: 選択肢の状態反映", "値札用状態メモの空白が読点に変換されて説明文へ入る"),
    "GuiChoiceReflectionTests.test_manual_condition_edit_survives_navigation":
        ("GUI: 選択肢の状態反映", "手動で書き換えた状態説明文が前へ／次へ往復後も残る"),
    # --- GuiActionTests ---
    "GuiActionTests.test_on_price_tags_validates_before_writing":
        ("GUI: ボタン操作（外部連携）", "値札出力ボタン：不正入力なら出力せずエラー表示"),
    "GuiActionTests.test_on_price_tags_writes_current_and_opens":
        ("GUI: ボタン操作（外部連携）", "値札出力ボタン：現在の入力を保存し出力・ファイルを開く"),
    "GuiActionTests.test_on_price_tags_shows_error_dialog_on_shortage":
        ("GUI: ボタン操作（外部連携）", "値札出力ボタン：シート不足時にエラーダイアログ"),
    "GuiActionTests.test_on_export_csv_validates_before_writing":
        ("GUI: ボタン操作（外部連携）", "CSV出力ボタン：不正入力なら出力せずエラー表示"),
    "GuiActionTests.test_on_export_csv_writes_current_and_opens":
        ("GUI: ボタン操作（外部連携）", "CSV出力ボタン：現在の入力を保存しCSV出力・ファイルを開く"),
    "GuiActionTests.test_on_export_csv_shows_error_dialog":
        ("GUI: ボタン操作（外部連携）", "CSV出力ボタン：出力失敗時にエラーダイアログ"),
    "GuiActionTests.test_output_from_blank_new_slot_uses_saved_items":
        ("GUI: ボタン操作（外部連携）", "最後に「次へ」を押した後でも保存済み商品をそのまま出力できる"),
    "GuiActionTests.test_output_with_no_items_shows_error":
        ("GUI: ボタン操作（外部連携）", "商品0件で値札/CSV出力→「出力する商品がありません」"),
    "GuiActionTests.test_output_still_blocks_on_partial_current_entry":
        ("GUI: 入力バリデーション", "新規スロットに入力途中なら出力を止めてエラー表示"),
    "GuiActionTests.test_close_confirmed_saves_settings":
        ("GUI: ボタン操作（外部連携）", "ウィンドウを閉じる：確認OKで設定保存しウィンドウ破棄"),
    "GuiActionTests.test_close_cancelled_keeps_window":
        ("GUI: ボタン操作（外部連携）", "ウィンドウを閉じる：確認キャンセルでウィンドウ維持"),
    # --- GuiMultiShopTests ---
    "GuiMultiShopTests.test_each_item_keeps_own_shop_through_price_tags":
        ("GUI: マルチ店舗フロー", "店舗の異なる商品を連続入力しても各商品が自店舗の管理番号になる（値札）"),
    "GuiMultiShopTests.test_shop_change_does_not_rewrite_saved_items":
        ("GUI: マルチ店舗フロー", "入力中に店舗を変えても保存済み商品の店舗は変わらない"),
    "GuiMultiShopTests.test_export_csv_uses_each_items_shop":
        ("GUI: マルチ店舗フロー", "CSV出力でも各商品が自店舗の管理番号・保存先フォルダになる"),
    # --- GuiOutputDirTests ---
    "GuiOutputDirTests.test_first_run_output_dir_is_empty":
        ("GUI: 出力先フォルダ", "初回起動（設定なし）は出力先が空欄＝参照で選ばせる"),
    "GuiOutputDirTests.test_output_dir_uses_passed_default_when_no_saved_value":
        ("GUI: 出力先フォルダ", "既定値が渡されていれば初期値に使う"),
    "GuiOutputDirTests.test_browse_updates_output_dir":
        ("GUI: 出力先フォルダ", "「参照」でフォルダを選ぶと出力先が更新される"),
    "GuiOutputDirTests.test_browse_cancel_keeps_output_dir":
        ("GUI: 出力先フォルダ", "「参照」をキャンセルすると出力先は変わらない"),
    "GuiOutputDirTests.test_price_tags_and_csv_land_in_chosen_dir":
        ("GUI: 出力先フォルダ", "選んだフォルダに ネット用値札.ods と auctions_*.csv が作られる"),
    "GuiOutputDirTests.test_nonexistent_output_dir_is_created":
        ("GUI: 出力先フォルダ", "存在しない出力先は自動で作成される"),
    "GuiOutputDirTests.test_empty_output_dir_shows_error":
        ("GUI: 出力先フォルダ", "出力先が空なら出力せずエラー表示"),
    "GuiOutputDirTests.test_output_dir_persisted_and_restored":
        ("GUI: 出力先フォルダ", "選んだ出力先が設定に保存され次回起動時に復元される"),
    # --- GuiDuplicateTests ---
    "GuiDuplicateTests.test_duplicate_middle_item_inserts_copy_after":
        ("GUI: 複製", "複製ボタン：現在のデータを次の位置に挿入し複製先を表示"),
    "GuiDuplicateTests.test_duplicate_shifts_following_items":
        ("GUI: 複製", "複製で以降の商品が1つずつ後ろへずれる"),
    "GuiDuplicateTests.test_duplicate_reflects_unsaved_edits":
        ("GUI: 複製", "「次へ」未押下の画面の編集内容も複製に反映される"),
    "GuiDuplicateTests.test_duplicate_is_independent_copy":
        ("GUI: 複製", "複製したデータを編集しても元データは変わらない"),
    "GuiDuplicateTests.test_duplicate_from_new_slot_with_content":
        ("GUI: 複製", "新規入力中に複製→その商品を確定してから複製を挿入"),
    "GuiDuplicateTests.test_duplicate_last_item_appends":
        ("GUI: 複製", "最後の商品を複製すると末尾に追加される"),
    "GuiDuplicateTests.test_duplicate_on_blank_slot_shows_error":
        ("GUI: 複製", "空の新規スロットで複製→「複製するデータがありません」"),
    # --- AuctionCsvTests ---
    "AuctionCsvTests.test_row_has_53_columns":
        ("ヤフオクCSV出力", "1商品=53列のCSV行になる"),
    "AuctionCsvTests.test_core_fields":
        ("ヤフオクCSV出力", "管理番号・カテゴリ・価格・キーワード・発送元・状態・フォルダ・配送グループ"),
    "AuctionCsvTests.test_constant_fields":
        ("ヤフオクCSV出力", "即決0・個数1・期間7・終了22・自動延長はい 等の固定値"),
    "AuctionCsvTests.test_image_and_spec_fields_blank":
        ("ヤフオクCSV出力", "画像・スペックサイズ・ブランドID・JAN等は空欄"),
    "AuctionCsvTests.test_condition_maps_unused_to_yahoo_label":
        ("ヤフオクCSV出力", "商品ランク→CSV「商品の状態」（未使用品→未使用 等）"),
    "AuctionCsvTests.test_title_and_description_reuse_web_builders":
        ("ヤフオクCSV出力", "タイトル・説明は既存のWeb用生成ロジックをそのまま使う"),
    "AuctionCsvTests.test_kanme_config_folder_and_prefixes":
        ("ヤフオクCSV出力", "要町・中野設定でも区切り「サイズ: 」とフォルダパスが反映される"),
    "AuctionCsvTests.test_export_writes_shift_jis_crlf_file":
        ("ヤフオクCSV出力", "auctions_YYYYMMDD.csv を Shift-JIS・CRLF・BOM無しで出力"),
    "AuctionCsvTests.test_export_sequential_management_numbers":
        ("ヤフオクCSV出力", "複数商品の管理番号が連番になる"),
    "AuctionCsvTests.test_export_same_day_overwrites_next_day_new_file":
        ("ヤフオクCSV出力", "同日は同ファイルを上書き更新、日付が変わると別ファイル"),
    "AuctionCsvTests.test_export_empty_raises":
        ("ヤフオクCSV出力", "商品0件の出力は ValueError"),
    "AuctionCsvTests.test_header_matches_sample":
        ("ヤフオクCSV出力", "auctions_sample.csv とヘッダーが完全一致"),
    "AuctionCsvTests.test_description_concrete_example":
        ("ヤフオクCSV出力", "中野店 TOMMY HILFIGER の説明列を具体値で検証（1行化・画像・保管店舗）"),

    "SerinaviParseTests.test_parse_pairs_all_items":
        ("出品 / 競りナビ連携", "フォルダ一覧HTMLから{管理番号: 競りナビ内部ID}を全件抽出"),
    "SerinaviParseTests.test_parse_empty_html":
        ("出品 / 競りナビ連携", "空HTMLは空dictを返す"),
    "SerinaviParseTests.test_parse_ignores_block_without_management_number":
        ("出品 / 競りナビ連携", "管理番号の無いブロック（ページャ等）は拾わない"),
    "SerinaviParseTests.test_parse_falls_back_to_checkbox_value":
        ("出品 / 競りナビ連携", "editリンクが無ければ checkbox の value を内部IDに使う"),
    "SerinaviParseTests.test_edit_url_format":
        ("出品 / 競りナビ連携", "編集ページURLに folder_id / item_id / action=edit が入る"),
    "SerinaviParseTests.test_folder_list_url_has_newest_first_sort":
        ("出品 / 競りナビ連携", "一覧URLは新着順（sort=-update_date）"),

    "DescriptionMultilineTests.test_default_is_single_physical_line":
        ("商品説明HTML", "既定の説明HTMLは改行なし1物理行（CSVアップロード用）"),
    "DescriptionMultilineTests.test_multiline_keeps_newlines":
        ("商品説明HTML", "multiline=True で改行を保持（出品ページ説明欄に直接入れる用）"),
    "DescriptionMultilineTests.test_both_have_same_content_ignoring_newlines":
        ("商品説明HTML", "1行版と改行版は改行以外の内容が一致する"),

    "GuiPublishTests.test_needs_firefox_profile":
        ("出品 / 競りナビ連携", "出品ボタン：Firefoxプロファイル未指定ならエラー、出品しない"),
    "GuiPublishTests.test_exports_csv_and_calls_publish":
        ("出品 / 競りナビ連携", "出品ボタン：CSV出力後 serinavi.publish を正しい引数で呼ぶ"),
    "GuiPublishTests.test_cancel_at_confirm_skips_publish":
        ("出品 / 競りナビ連携", "出品ボタン：確認ダイアログでキャンセルすると出品しない"),
    "GuiPublishTests.test_failures_show_warning":
        ("出品 / 競りナビ連携", "出品ボタン：説明更新に失敗した商品があれば警告表示"),
    "GuiPublishTests.test_blank_new_slot_uses_saved_items":
        ("出品 / 競りナビ連携", "出品ボタン：空スロットからでも保存済み全商品を出品"),
    "GuiPublishTests.test_no_items_shows_error":
        ("出品 / 競りナビ連携", "出品ボタン：商品0件なら「出力する商品がありません」"),
}

# サブクラスのテストは親クラスの TEST_META を流用する
_SUBCLASS_PARENT = {"GuiChoiceReflectionKanmeTests": "GuiChoiceReflectionTests"}

STATUS_LABEL = {"pass": "成功", "fail": "失敗", "error": "エラー", "skip": "スキップ"}
STATUS_MARK = {"pass": "✓", "fail": "✗", "error": "✗", "skip": "－"}


# ---------------------------------------------------------------------------
# テスト実行
# ---------------------------------------------------------------------------

class _Collector(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records: dict[str, dict] = {}
        self._start = 0.0

    @staticmethod
    def _tid(test) -> str:
        return test.id().split(".", 1)[1]      # "Class.method"

    def _rec(self, test) -> dict:
        return self.records.setdefault(self._tid(test), {
            "cls": test.__class__.__name__,
            "method": test._testMethodName,
            "doc": (test.shortDescription() or "").strip(),
            "status": "pass",
            "seconds": 0.0,
            "note": "",
        })

    def startTest(self, test):
        super().startTest(test)
        self._start = time.perf_counter()
        self._rec(test)

    def stopTest(self, test):
        super().stopTest(test)
        self._rec(test)["seconds"] = time.perf_counter() - self._start

    def addFailure(self, test, err):
        super().addFailure(test, err)
        rec = self._rec(test)
        rec["status"] = "fail"
        rec["note"] = _first_line(self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        rec = self._rec(test)
        rec["status"] = "error"
        rec["note"] = _first_line(self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        rec = self._rec(test)
        rec["status"] = "skip"
        rec["note"] = reason


def _first_line(text: str) -> str:
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line and not line.startswith("File "):
            return line[:300]
    return text.strip()[:300]


def _pretty(method: str) -> str:
    return method[5:].replace("_", " ") if method.startswith("test_") else method


def run_suite() -> tuple[list[dict], float]:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(TEST_MODULE)
    runner = unittest.TextTestRunner(resultclass=_Collector, stream=io.StringIO(),
                                     verbosity=0)
    t0 = time.perf_counter()
    result = runner.run(suite)
    elapsed = time.perf_counter() - t0

    rows: list[dict] = []
    unmeta: list[str] = []
    for tid, rec in sorted(result.records.items()):
        meta = TEST_META.get(tid)
        if not meta:
            cls, _, method = tid.partition(".")
            parent = _SUBCLASS_PARENT.get(cls)
            if parent and f"{parent}.{method}" in TEST_META:
                p_area, p_desc = TEST_META[f"{parent}.{method}"]
                meta = (p_area, p_desc + "（要町・中野設定）")
        if meta:
            area, content = meta
        else:
            unmeta.append(tid)
            area = AREA_BY_CLASS.get(rec["cls"], "未分類")
            content = rec["doc"] or _pretty(rec["method"])
        rows.append({
            "tid": tid,
            "area": area,
            "cls": rec["cls"],
            "content": content,
            "status": rec["status"],
            "seconds": rec["seconds"],
            "note": rec["note"],
        })
    if unmeta:
        print("⚠ TEST_META 未登録のテスト（説明が仮）:")
        for tid in unmeta:
            print(f"    {tid}")
    return rows, elapsed


# ---------------------------------------------------------------------------
# レポート生成
# ---------------------------------------------------------------------------

def build_workbook(rows: list[dict], elapsed: float) -> Workbook:
    wb = Workbook()
    title = wb.add_style(bold=True, color="FFFFFF", bg="1F3864", align="center",
                         valign="center")
    head = wb.add_style(bold=True, color="FFFFFF", bg="2F5597", border=True,
                        align="center", valign="center", wrap=True)
    cell = wb.add_style(border=True, valign="top", wrap=True)
    center = wb.add_style(border=True, align="center", valign="center")
    num = wb.add_style(border=True, align="right", valign="center", num_fmt="0.0")
    pct = wb.add_style(border=True, align="right", valign="center", num_fmt='0.0"%"')
    ok = wb.add_style(border=True, align="center", valign="center", bg="C6EFCE",
                      color="006100", bold=True)
    ng = wb.add_style(border=True, align="center", valign="center", bg="FFC7CE",
                      color="9C0006", bold=True)
    skip = wb.add_style(border=True, align="center", valign="center", bg="FFEB9C",
                        color="9C6500")
    key = wb.add_style(border=True, bold=True, bg="DDEBF7", valign="center")

    _sheet_items(wb, rows, dict(title=title, head=head, cell=cell, center=center,
                                num=num, ok=ok, ng=ng, skip=skip))
    _sheet_summary(wb, rows, elapsed, dict(title=title, head=head, cell=cell,
                                           center=center, num=num, pct=pct, key=key,
                                           ok=ok, ng=ng, skip=skip))
    _sheet_coverage(wb, rows, dict(title=title, head=head, cell=cell, center=center,
                                   num=num, pct=pct, ok=ok, ng=ng, skip=skip))
    return wb


def _mark_style(status: str, s: dict) -> int:
    return {"pass": s["ok"], "skip": s["skip"]}.get(status, s["ng"])


def _sheet_items(wb: Workbook, rows: list[dict], s: dict) -> None:
    sh = wb.add_sheet("テスト項目一覧")
    headers = ["No", "分類", "テストID", "テスト内容", "実行結果", "クリア",
               "所要(ms)", "備考（失敗内容 / スキップ理由）"]
    widths = [5, 22, 46, 60, 10, 8, 10, 70]
    for i, w in enumerate(widths, start=1):
        sh.set_col_width(i, w)
    sh.write_row(1, 1, headers, s["head"])
    for n, row in enumerate(rows, start=1):
        r = n + 1
        sh.write(r, 1, n, s["center"])
        sh.write(r, 2, row["area"], s["cell"])
        sh.write(r, 3, row["tid"], s["cell"])
        sh.write(r, 4, row["content"], s["cell"])
        sh.write(r, 5, STATUS_LABEL[row["status"]], s["center"])
        sh.write(r, 6, STATUS_MARK[row["status"]], _mark_style(row["status"], s))
        sh.write(r, 7, round(row["seconds"] * 1000, 1), s["num"])
        sh.write(r, 8, row["note"], s["cell"])
    sh.freeze(row=1)
    sh.set_autofilter(1, 1, len(rows) + 1, len(headers))


def _sheet_summary(wb: Workbook, rows: list[dict], elapsed: float, s: dict) -> None:
    sh = wb.add_sheet("サマリ")
    for i, w in enumerate([28, 16, 12, 12, 12, 14], start=1):
        sh.set_col_width(i, w)
    total = len(rows)
    passed = sum(r["status"] == "pass" for r in rows)
    failed = sum(r["status"] == "fail" for r in rows)
    errored = sum(r["status"] == "error" for r in rows)
    skipped = sum(r["status"] == "skip" for r in rows)
    executed = total - skipped
    rate = (passed / executed * 100) if executed else 0.0

    sh.merge(1, 1, 1, 6)
    sh.write(1, 1, "EC_Bridge 単体テスト結果サマリ", s["title"])
    info = [
        ("実行日時", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Python", platform.python_version()),
        ("OS", f"{platform.system()} {platform.release()}"),
        ("総実行時間(秒)", round(elapsed, 2)),
    ]
    r = 3
    for k, v in info:
        sh.write(r, 1, k, s["key"])
        sh.write(r, 2, v, s["cell"])
        r += 1

    r += 1
    sh.write_row(r, 1, ["区分", "件数"], s["head"])
    for label, value, style in [
        ("テスト総数", total, s["cell"]),
        ("成功", passed, s["ok"]),
        ("失敗", failed, s["ng"] if failed else s["cell"]),
        ("エラー", errored, s["ng"] if errored else s["cell"]),
        ("スキップ", skipped, s["skip"] if skipped else s["cell"]),
    ]:
        r += 1
        sh.write(r, 1, label, s["key"])
        sh.write(r, 2, value, style)
    r += 1
    sh.write(r, 1, "成功率（スキップ除く）", s["key"])
    sh.write(r, 2, round(rate, 1), s["pct"])
    r += 1
    sh.write(r, 1, "総合判定", s["key"])
    verdict_ok = failed == 0 and errored == 0
    sh.write(r, 2, "合格" if verdict_ok else "要修正",
             s["ok"] if verdict_ok else s["ng"])

    # 分類別
    r += 3
    sh.write_row(r, 1, ["分類", "件数", "成功", "失敗/エラー", "スキップ", "判定"],
                 s["head"])
    areas = sorted({row["area"] for row in rows},
                   key=lambda a: (a not in REQUIRED_AREAS, a))
    for area in areas:
        group = [row for row in rows if row["area"] == area]
        g_pass = sum(x["status"] == "pass" for x in group)
        g_bad = sum(x["status"] in ("fail", "error") for x in group)
        g_skip = sum(x["status"] == "skip" for x in group)
        r += 1
        sh.write(r, 1, area, s["cell"])
        sh.write(r, 2, len(group), s["center"])
        sh.write(r, 3, g_pass, s["center"])
        sh.write(r, 4, g_bad, s["ng"] if g_bad else s["center"])
        sh.write(r, 5, g_skip, s["skip"] if g_skip else s["center"])
        sh.write(r, 6, "OK" if g_bad == 0 else "NG",
                 s["ok"] if g_bad == 0 else s["ng"])


def _sheet_coverage(wb: Workbook, rows: list[dict], s: dict) -> None:
    sh = wb.add_sheet("カバレッジ")
    for i, w in enumerate([28, 12, 12, 12, 18, 40], start=1):
        sh.set_col_width(i, w)
    sh.merge(1, 1, 1, 6)
    sh.write(1, 1, "機能領域カバレッジ（テストが存在し、全て合格しているか）", s["title"])
    sh.write_row(3, 1, ["機能領域", "テスト件数", "成功", "失敗/エラー", "状態", "備考"],
                 s["head"])

    r = 3
    for area in REQUIRED_AREAS:
        group = [row for row in rows if row["area"] == area]
        g_pass = sum(x["status"] == "pass" for x in group)
        g_bad = sum(x["status"] in ("fail", "error") for x in group)
        r += 1
        if not group:
            state, style, note = "✗ テスト無し", s["ng"], "この領域のテストを追加してください"
        elif g_bad:
            state, style, note = "▲ 一部失敗", s["ng"], "失敗テストを修正してください"
        else:
            state, style, note = "✓ 網羅", s["ok"], ""
        sh.write(r, 1, area, s["cell"])
        sh.write(r, 2, len(group), s["center"])
        sh.write(r, 3, g_pass, s["center"])
        sh.write(r, 4, g_bad, s["ng"] if g_bad else s["center"])
        sh.write(r, 5, state, style)
        sh.write(r, 6, note, s["cell"])

    unclassified = sorted({row["tid"] for row in rows if row["area"] == "未分類"})
    r += 2
    sh.write(r, 1, "未分類のテスト（AREA_BY_TEST に追記推奨）", s["head"])
    if unclassified:
        for tid in unclassified:
            r += 1
            sh.write(r, 1, tid, s["ng"])
    else:
        r += 1
        sh.write(r, 1, "なし（全テストが機能領域に割り当て済み）", s["ok"])


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    parser = argparse.ArgumentParser(description="単体テストを実行して Excel 報告を生成")
    parser.add_argument("--open", action="store_true", help="生成後にファイルを開く")
    parser.add_argument("--out", default=os.path.join(OUTPUT_DIR, "テスト結果.xlsx"))
    args = parser.parse_args(argv)

    os.chdir(TESTS_DIR)
    for p in (TESTS_DIR, os.path.join(PROJECT_DIR, "src")):
        if p not in sys.path:
            sys.path.insert(0, p)

    rows, elapsed = run_suite()
    wb = build_workbook(rows, elapsed)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dated = os.path.join(OUTPUT_DIR, f"テスト結果_{stamp}.xlsx")
    wb.save(dated)
    try:
        wb.save(args.out)
    except PermissionError:
        print(f"⚠ {os.path.basename(args.out)} が開かれているため更新できません。"
              f"閉じてから再実行してください（履歴ファイルは出力済み）。")
        args.out = dated

    passed = sum(r["status"] == "pass" for r in rows)
    failed = sum(r["status"] in ("fail", "error") for r in rows)
    skipped = sum(r["status"] == "skip" for r in rows)
    missing = [a for a in REQUIRED_AREAS
               if not any(r["area"] == a for r in rows)]

    print(f"テスト: {len(rows)}件  成功 {passed} / 失敗・エラー {failed} / スキップ {skipped}")
    if missing:
        print("⚠ テスト未整備の機能領域: " + ", ".join(missing))
    print(f"出力: {args.out}")
    print(f"      {dated}")

    if args.open:
        try:
            os.startfile(args.out)  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            pass

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
