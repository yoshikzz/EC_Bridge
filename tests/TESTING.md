# 単体テストと結果レポート

`tests/` 内で実行する（テストが `../src` を自動で import パスに追加する）。

## 1. テストの実行

```
cd tests
python -m unittest test_ec_bridge_core -v
```

- `test_ec_bridge_core.py` … 単体テスト本体（150 項目）
  - `RegressionTests` … 旧 `EC_Bridge.py` / `EC_Bridge_for_kanme_nakano.py`
    （コミット `3fe6c7c`）のロジックを関数として再現し、**書き直し後も挙動が
    変わっていないこと**を照合する
  - `IntentionalChangeTests` … 意図的に変えた仕様を固定する
  - `PriceTagTests` … 実物／合成テンプレートに対する値札(.ods)出力
  - `AuctionCsvTests` … ヤフオク一括出品CSV（53列・Shift-JIS・CRLF）。
    `auctions_sample.csv` とヘッダーが一致することも確認
  - `SettingsTests` / `MasterDataTests` / `HelperTests` / `DescriptionEdgeTests`
  - GUI（Tk を生成。画面を出せない環境では自動 skip）
    - `GuiSmokeTests` / `GuiExtraTests` … 画面遷移・バリデーション・文字数表示
    - `GuiMeasurementPanelTests` … 6 ジャンル＋未選択の実寸パネル、値の保持
    - `GuiChoiceReflectionTests` … すべてのコンボ／ラジオ（店舗3・性別3・送料2・
      ランク9・商品ランク6・商品状態11・動作確認7）が状態と派生出力へ反映されるか。
      `GuiChoiceReflectionKanmeTests` で要町・中野設定でも同じ網羅を再実行
    - `GuiActionTests` … ボタン（値札出力／閉じる）の動作。
      ファイルを開く処理・メッセージボックスは mock で遮断
    - `GuiDuplicateTests` … 「複製」ボタン（次の位置へ挿入・以降ずれ・独立コピー）
    - `GuiMultiShopTests` … 店舗をまたぐ入力で、値札・CSV とも各商品が
      自店舗の管理番号・保存先フォルダになるか
    - `GuiPublishTests` … 「出品」ボタン。CSV 出力 → `serinavi.publish`（mock）を
      正しい引数で呼ぶか、Firefoxプロファイル未指定・キャンセル・失敗時の挙動
  - `SerinaviParseTests` … 競りナビ フォルダ一覧HTML → `{管理番号: item_id}` の抽出
    （`fixtures/folder_listing_sample.html` は合成データ）。URL 組み立ても確認
  - `DescriptionMultilineTests` … `build_web_description` の `multiline` 切り替え
    （既定=1物理行 / `True`=改行入り、改行以外は同一）

### GUI で自動化していない範囲

- キーボード操作（Return でコンボを開く等）… イベントループ依存で価値が低い
- ウィジェットの座標・見た目
- ネイティブの確認ダイアログそのもの（mock より先）
- `serinavi.publish` の実ブラウザ動作（Firefox＋競りナビのログインが要るため手動確認）

## 2. Excel チェックリストの生成

```
cd tests
python test_report.py            # テスト実行 → ../output/テスト結果.xlsx
python test_report.py --open     # 生成後に開く
```

`output/テスト結果.xlsx`（毎回上書き）と `output/テスト結果_YYYYMMDD_HHMMSS.xlsx`
（履歴）の 2 ファイルを出力する。依存ライブラリ不要（`mini_xlsx.py` を同梱）。

### シート構成

| シート | 内容 |
|---|---|
| テスト項目一覧 | 1 テスト = 1 行。合格すると「クリア」列に **✓（緑）** が自動で付く。失敗は ✗（赤）、スキップは －（黄）。オートフィルター付き |
| サマリ | 実行環境・全体集計（総合判定 合格/要修正）・分類別集計 |
| カバレッジ | 機能領域ごとに「テストがあり、かつ全て合格しているか」。テストが無い領域は **✗ テスト無し** で警告 |

「クリア」列のチェックは、`test_report.py` が実際にテストを走らせて合格した
ものだけに付く。再実行すれば最新状態に更新される。

## 3. 網羅性の担保（テストを増やすときの手順）

`test_report.py` の先頭に 2 つの表がある。

- `REQUIRED_AREAS` … カバーすべき機能領域の一覧。
  ここに載っていて対応テストが 1 件も無い領域は、カバレッジシートで
  **✗ テスト無し** と表示される。新機能を足したらこの一覧にも追加する。
- `TEST_META` … `テストID -> (機能領域, 日本語のテスト内容)`。
  新しいテストメソッドを `test_ec_bridge_core.py` に追加したら、ここに 1 行足す。
  未登録のまま実行すると `test_report.py` がコンソールに
  `⚠ TEST_META 未登録のテスト` と警告し、レポートには仮の説明で載る。

つまり「テストを足す → `TEST_META` に登録 → レポートで領域が ✓ になる」
というサイクルで、抜けが可視化される。

## 4. CI 等での利用

`test_report.py` はテスト失敗があると終了コード 1 を返す。
`python test_report.py` をそのままパイプラインに置ける。
