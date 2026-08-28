# EC_Bridge

---

# 📗 利用ガイド

## 1. インストール

### 1-1. ファイルを入手する

1. ブラウザで **https://github.com/yoshikzz/EC_Bridge** を開く。
2. 緑色の **「Code」** ボタン → **「Download ZIP」** をクリック。
3. ダウンロードした **`EC_Bridge-main.zip`** を右クリック →
   **「すべて展開」** で好きな場所（デスクトップなど）に展開する。
4. 展開してできた `EC_Bridge-main` フォルダの中の **`dist`** フォルダを開く。

### 1-2. インストーラを実行する

5. `dist` フォルダの中の **`install.exe`** をダブルクリック。
   （「WindowsによってPCが保護されました」と出たら **「詳細情報」→「実行」**）
6. **店舗を選択**（上池袋 / 要町 / 中野）。
7. **インストール先** を選ぶ（既定の `ドキュメント\EC_Bridge` などでOK）。
8. **「インストール」** を押す。
9. デスクトップに **「EC_Bridge（店舗名）」** のショートカットができます。
   **次回からはこのショートカットを起動**（ZIPファイルと展開済みのフォルダは消してかまいません）。

> インストール先のフォルダには `EC_Bridge_<店舗>.exe` と
> `ネット用値札.ods`（値札テンプレート）が入ります(移動したり変更しないでください)。

## 2. はじめての起動

- 上部の **「出力先」** 欄が空なので、**「参照」** を押して
  **値札やCSVを保存したいフォルダ** を選んでください（デスクトップや共有フォルダなど）。
  一度選べば記憶され、次回からは自動で入ります。
 
  ※ `ネット用値札.ods`（テンプレート）が置いてあるフォルダは選ばないでください。

- **「出品」ボタンを使う場合**は、**「Firefoxプロファイル」** 欄に
  **ふだん競りナビにログインしている Firefox のプロファイルフォルダ** を設定します
  （設定は初回だけ。次回からは記憶されます）。**Firefox 本体**
  （`C:\Program Files\Mozilla Firefox`）も入っている必要があります。
  → 場所と確認方法は次の「2-1」を参照。

### 2-1. Firefoxプロファイルフォルダの調べ方

「プロファイル」＝ Firefox がブックマークやログイン状態を保存している場所です。
人によってフォルダ名（`xxxxxxxx.default-release` の `xxxxxxxx` 部分）が違うので、
**Firefox で調べます**。

1. **Firefox** を開き、アドレスバーに `about:profiles` と入力して Enter。
2. 「プロファイル」が並びます。**「既定のプロファイル: はい」** と書かれている
   もの（＝ふだん使っているもの）を見ます。
3. その **「ルートディレクトリ」** の行にある **「フォルダーを開く」** ボタンを押す。
   → エクスプローラーが開きます。
4. エクスプローラーの**アドレスバーをクリック**するとフルパスが選択されるので、
   `Ctrl+C` でコピー。
   （例: `C:\Users\tanaka\AppData\Roaming\Mozilla\Firefox\Profiles\ab12cd34.default-release`）
5. EC_Bridge の **「Firefoxプロファイル」** 欄の **「参照」** を押し、
   4 のフォルダを選ぶ（またはパスを貼り付ける）。

> - `AppData` フォルダは通常隠れています。上記の `about:profiles` →
>   「フォルダーを開く」を使えば隠れていても開けます。
> - 複数プロファイルがある場合は、**競りナビにログインできているほうの Firefox** で
>   `about:profiles` を開いてください（「使用中」と表示されているものが今開いている
>   プロファイルです）。
> - プロファイルを移動・改名すると設定し直しになります。

## 3. 画面の入力欄

| 欄 | 説明 |
|---|---|
| **取扱店舗** | 上池袋 / 要町 / 中野。管理番号・発送元・保管店舗表示などが切り替わります |
| **出力先** | 値札とCSVの保存先フォルダ |
| **Firefoxプロファイル** | 「出品」ボタンで使う、競りナビにログイン済みの Firefox プロファイル |
| **商品ブランド(メーカー)** | 例: `NIKE` |
| **カタカナ** | 例: `ナイキ` |
| **商品名(値札1行目)** | 値札とタイトルに使う品名 |
| **カラー** | 例: `ブラック` |
| **ネット出品タイトル** | 上の入力から自動生成（編集不可）。右に文字数（全角1・半角0.5／65 まで） |
| **値段** | 半角数字のみ |
| **性別** | 記入無し / メンズ / レディース（トップス・ボトムスのときタイトルに付きます） |
| **商品ジャンル** | トップス / ボトムス / シューズ / バッグ / 腕時計 / その他。選ぶと下の実寸欄が変わります |
| **表記サイズ** | タグ表記のサイズ（例 `M`, `27.0`）。空なら値札は「-」 |
| **実寸サイズ** | ジャンルごとの採寸欄（トップス=着丈/肩幅/身幅/袖丈 など）。「その他」は代わりに **動作確認** を選択 |
| **商品状態** | 未使用品 / 美中古品 / 中古品 / 現状品 / ジャンク品 / 箱付き …（全11種） |
| **ランク** | 値札用ランク A〜E（AB, BC などの中間あり） |
| **商品ランク** | ヤフオクの「商品の状態」: 未使用品 / 目立った傷や汚れなし / やや傷や汚れあり など |
| **値札用状態メモ** | 値札と説明文に入る補足（例 `使用感 スレ`）。スペースは自動で「、」に |
| **状態説明文** | 自動生成されますが、手で書き換えても構いません |
| **送料** | 700 / 2000（CSVの配送グループ 1 / 2 になります） |

## 4. ボタン

| ボタン | 動作 |
|---|---|
| **前へ / 次へ** | 商品を1件ずつ移動。「次へ」で今の入力を保存して次の番号へ |
| **複製** | 今のデータを次の位置にコピー（以降の商品は1つずつ後ろへずれる） |
| **削除** | 表示中の商品を削除 |
| **値札出力** | 出力先に `ネット用値札.ods` を作成／上書き（既存を毎回上書き＝常に最新） |
| **出品** | 出力先に `auctions_YYYYMMDD.csv` を作成（同じ日は上書き、翌日は別ファイル）し、続けて **Firefox で競りナビへ自動アップロード**。さらに各商品の編集ページを開いて **説明を改行入りの見やすい形に整える** |

## 5. 基本の流れ

1. 店舗を選ぶ／出力先を確認（「出品」を使うなら Firefoxプロファイルも設定）。
2. 1件目を入力 → **「次へ」** → 2件目を入力 → …（同じ商品が続くときは **「複製」** が便利）。
3. 全部入れたら（最後の商品を表示したまま） **「値札出力」** を押して値札を作る。
4. **「出品」** を押す → 確認ダイアログで **OK** → Firefox が開く。
5. Firefox が競りナビにログイン済みならそのまま自動で進みます。
   ログイン画面が出たら **「Yahoo! JAPAN IDでログイン」→ ID/パスワード** でログインし、
   アプリの確認ダイアログで **OK**。
   → CSV が自動アップロードされ、続けて各商品の説明が整えられます。
6. 完了/一部失敗のメッセージが出ます。値札 `ネット用値札.ods` は印刷して使います。

## 6. 「出品」ボタンがやっていること

1. 出力先に `auctions_YYYYMMDD.csv`（競りナビの一括アップロード形式）を作る。
2. Firefox（指定プロファイル）で 競りナビ →「アップロード」→「一括アップロード」を開き、
   その CSV を選んで「決定」まで自動で行う。
   → CSV の「商品保存先フォルダパス」列（店舗ごとに `新NEW○○在庫`）のフォルダに登録される。
3. 店舗フォルダの一覧から **管理番号** で各商品を探し、編集ページを開いて
   **説明を改行入りの HTML** に差し替えて保存する
   （CSV 内では改行が使えないため、アップロード用は1行・登録後に整える）。

> - 途中で見つからなかった商品は最後にまとめて表示されます（CSV 分は登録済み）。
> - **カテゴリ** は全行 `2084207680` で登録されます。商品ごとに違う場合は
>   競りナビ側で直してください（`ブランドID`・`サイズ規格` も同様）。
> - 競りナビは処理が成功しても「通信エラー」を表示することがあります。アプリは
>   一覧に商品が入ったかを確認してから進むので、**同じ「出品」操作を焦って
>   何度も押さないでください**（管理番号が重複登録されます）。
> - 同じ日に「出品」をやり直すと、前回アップロードした商品はそのまま残り、
>   もう一度アップロードされて**重複します**。追加ではなくやり直したいときは、
>   競りナビ側で前回分を消してから実行してください（翌日は別ファイル）。

### 手動でアップロードしたいとき（フォールバック）

Firefox が使えない等の場合は、`auctions_YYYYMMDD.csv` を自分で取り込めます。
競りナビ → **「アップロード」→「一括アップロード」** →
**「ファイルを選択」** で `auctions_YYYYMMDD.csv` → **「決定」**。
保存は **CSV（Shift-JIS）形式のまま**（Excel で開いたら UTF-8 にしないこと）。

## 7. こんなときは

- **値札が21件以上**： `ネット用値札.ods`（テンプレート）を LibreOffice で開き、**シート（タブ）を追加**してください。1タブ20枚、40件なら2タブ、という具合です。不足しているとエラーで枚数を教えてくれます。
- **アップロードでエラーになる**： CSV を保存し直すとき Excel が **UTF-8 の CSV** にしてしまうことがあります。「CSV（コンマ区切り）」＝ Shift-JIS で保存してください（元のまま触らなければ Shift-JIS です）。
- **「ネット用値札.ods が開かれています」／「auctions_… が開かれています」**： 出力先のそのファイルを閉じてからもう一度。
- **出力先を変えたい**： 「参照」で選び直すだけ。記憶されます。
- **店舗を一時的に変えたい**： 画面上の「取扱店舗」で切り替えられます。
- **「出品」で Firefox が開かない / すぐ閉じる**： 「Firefoxプロファイル」欄が
  競りナビにログイン済みのプロファイルフォルダを指しているか（調べ方は「2-1」）、
  Firefox 本体が `C:\Program Files\Mozilla Firefox` にあるかを確認してください。
- **「出品」でログイン画面が出る**： 指定したプロファイルが競りナビに未ログインです。
  開いた Firefox で「Yahoo! JAPAN IDでログイン」からログインし、アプリの
  ダイアログで OK を押せばそのまま続行します。毎回聞かれるなら、`about:profiles`
  で **ふだん競りナビにログインしているプロファイル**（「既定のプロファイル: はい」）
  を選び直してください。
- **「出品」で一部の商品が「一覧に見つからず」になる**： アップロード直後は一覧への
  反映が遅れることがあります。少し待ってから、その商品だけアプリで入れ直して
  もう一度「出品」するか、競りナビで直接説明を貼り付けてください。

---

# 🛠 開発者向け

## フォルダ構成

```
ec_bridge/
├── src/
│   ├── ec_bridge_core.py            すべてのロジック（GUI・値札・CSV・定数）
│   ├── app.py                       配布 exe のエントリ（install.json で店舗決定）
│   ├── serinavi.py                  競りナビへの出品（Selenium・遅延import）
│   ├── EC_Bridge.py                 開発用ランチャー（上池袋）
│   ├── EC_Bridge_for_kanme_nakano.py 開発用ランチャー（中野）
│   ├── geckodriver.exe              Firefox 用 WebDriver（exe に同梱される）
│   └── ネット用値札.ods             値札テンプレート（4列×5行の値札レイアウト入り）
├── installer/installer.py           install.exe の中身（店舗選択GUI）
├── build.py                         PyInstaller ビルドスクリプト
├── dist/install.exe                 配布物（コミットする。約30MB）
├── tests/
│   ├── test_ec_bridge_core.py       単体テスト（150 項目）
│   ├── test_report.py               テスト実行＋Excelチェックリスト生成
│   ├── mini_xlsx.py                 依存なしの .xlsx ライター
│   ├── auctions_sample.csv          出品CSVの形式サンプル
│   ├── fixtures/                    テスト用の合成データ（競りナビ一覧HTML等）
│   └── TESTING.md
└── output/                          テストレポート・selftest の出力先（git 管理外）
```

## アーキテクチャ

- **`ec_bridge_core.py` が本体**。GUI（`EcBridgeApp`）・値札出力（`write_price_tags`）・
  CSV出力（`export_auction_csv`）・文字列生成（`build_title` / `build_web_description` /
  `build_tag_info` / `measurement_html`）・マスタ定数（`SHOPS` / `AUCTION_CSV_HEADER` …）・
  データ構造（`ShopSpec` / `AppConfig` / `Item` dataclass）。
- **`serinavi.py`** は「出品」ボタンの Selenium 処理。`EcBridgeApp.on_publish` から
  **遅延 import** される（起動時は読み込まない）。`parse_folder_listing(html)` と
  `publish(items, config, csv_path, *, geckodriver_path, profile_dir, confirm, progress)`。
  - **ログイン関門**: `driver.get(UPLOAD_URL)` して `/serinavi/` に居ればセッション
    有効とみなし続行。未ログインなら `confirm()` で手動ログインを促す（`/serinavi/hub`
    へはあえて遷移しない。ログイン直後は `pro.store.yahoo.co.jp/pro.*` に飛ぶ）。
  - **「決定する」はネイティブクリック**（`element.click()`）。`execute_script` の
    JS click だと XHR が中途半端になり「通信エラー」が多発する（20件で再現）。
  - **重複対策**: 競りナビは処理成功でも「通信エラー」を出すことがあり、単純に
    リトライすると管理番号が重複登録される。`publish` は
    「アップロード → 一覧の先頭ページで反映確認（`_probe`）→ 出ていなければ短く
    待って再確認 → それでも 0 件なら再アップロード」を最大 `UPLOAD_ATTEMPTS` 回。
    **再アップロード前に必ず一覧を確認する**ので、成功済みなら重複しない。
  - 一覧待ちは短め（`_folder_map` の `WebDriverWait` は 12 秒）。失敗時は CSV パス
    付きの明確なメッセージを返し、無限に探し続けない。
  - `_make_driver` は `Options.profile = <利用者プロファイル>`（FirefoxProfile が
    コピーしてセッションを引き継ぐ。ログイン状態はプロファイル任せ）。
- **`app.py`** は配布用の薄いエントリ。`install.json` の `shop` を読み、
  `make_config(shop)` で `AppConfig` を作って `run()`。`--selftest` で GUI 無しの動作確認。
- **`EC_Bridge.py` / `EC_Bridge_for_kanme_nakano.py`** は開発時に店舗固定で起動するための同等物。
- **パス解決**（`_FROZEN` 判定）:
  - 開発時: テンプレートは `src/`、設定は `PROJECT_DIR`（= リポジトリ直下）。
  - exe 時: `PROJECT_DIR` = exe と同じフォルダ。テンプレート `ネット用値札.ods`・
    `install.json`・`EC_Bridge_settings.json` はそこに置く。
  - **出力先**（ODS/CSV）は GUI の「出力先」欄。初回は空、選ぶと `output_dir` として設定保存。

## データフロー

```
GUI 入力 → Item(dataclass)
  ├─ build_title(item, config, web=False)  → 画面の「ネット出品タイトル」
  ├─ config.condition_text(...)            → 「状態説明文」
  └─ 一覧 list[Item]
        ├─ write_price_tags(items, config, out_dir)
        │     テンプレ .ods を複製 → セルに書込 → <out_dir>/ネット用値札.ods を上書き
        ├─ export_auction_csv(items, config, out_dir)
        │     build_auction_row × N → <out_dir>/auctions_YYYYMMDD.csv (Shift-JIS/CRLF)
        │        各行: build_title(web=True) / build_web_description / build_tag_info 相当
        └─ serinavi.publish(items, config, csv_path, ...)   ← 「出品」ボタン
              1. 一括アップロード画面で上記 CSV を取り込む
              2. 店舗フォルダ一覧HTML → parse_folder_listing → {管理番号: item_id}
              3. 各編集ページで build_web_description(multiline=True) を流し込んで保存
```

管理番号 = `{店舗ID}{YY}{MM}{DD}{連番3桁}`（`management_number`）。店舗IDは 上池袋22 / 要町11 / 中野44。
競りナビのフォルダID（`ShopSpec.folder_id`）は 上池袋 1308997 / 要町 1308972 / 中野 1309032。

## 店舗バリアント

`make_config(shop)` が店舗名から `AppConfig` を組み立てる:

| | 標準版（上池袋） | 要町中野版（`KANME_SHOPS = {要町, 中野}`） |
|---|---|---|
| 状態説明文 | `medamaya_condition_text` | `kanme_condition_text` |
| タイトル区切り | ` サイズ` / ` ` | ` サイズ: ` / ` カラー: ` |
| 中野店の説明画像 | `ranku.jpg` | `rank.jpg`（`shop_image_overrides`） |

## 値札 `.ods` のレイアウト

1タブ = **20枚**（`ITEMS_PER_SHEET`）。タブ内は **4列 × 5行**、値札1枚あたり縦7セル。

- 列ブロック: 位置1–5→列0、6–10→列3、11–15→列6、16–20→列9（`PRICE_TAG_BLOCKS`）
- 行オフセット: ブロック内 0,7,14,21,28
- 書き込むセル（データ列 `c`、ラベル列 `c+1`）:
  `[r,c]`ブランド / `[r+1,c]`管理番号 / `[r+2,c]`価格 / `[r+2,c+1]`ランク /
  `[r+4,c]`品名（空白→`/`） / `[r+5,c]`情報欄（`build_tag_info`）
- 21件目以降は次タブへ折り返し。タブ不足時は `ValueError`（必要タブ数を案内）。
- テンプレートは**上書きしない**。`<out_dir>/ネット用値札.ods` に `.bak` を作らず保存。

## ヤフオク出品CSV（`AUCTION_CSV_HEADER` = 53列）

**競りナビの「一括アップロード」形式の CSV**を `export_auction_csv` が書き出し、
「出品」ボタンが `serinavi.publish` でアップロード＋説明整形まで自動化する
（`serinavi.py` 参照。手動アップロードも可能）。

- **Shift-JIS(cp932) / CRLF / BOM無し / QUOTE_MINIMAL**。
  `説明` 列は **1物理行**（`build_web_description` が既定でテンプレートの改行 `\n` を
  半角スペースに畳む）。競りナビの一括アップロードはフィールド内の改行を受け付けないため。
  アップロード後、`serinavi.publish` が編集ページで `build_web_description(multiline=True)`
  の**改行入り版**に差し替える（見た目は `<BR>` タグで決まるので変わらない）。
- GUI から埋まる列: 管理番号 / タイトル / 説明 / 開始価格 / ストアキーワード / 発送元 / 商品の状態 /
  商品保存先フォルダパス / 配送グループ。
- 固定値: 即決0・個数1・期間7・終了22・自動延長はい・自動再出品3・消費税10・発送1日 ほか。
- **空欄のまま（アップロード前に手補完）**: カテゴリ（全行 `2084207680`）・ブランドID・
  商品スペックサイズ種別/ID・商品分類ID・画像列。
- 「商品の状態」は `YAHOO_CONDITION_CSV` で変換（`未使用品`→`未使用` など）。
- ファイル名 `auctions_YYYYMMDD.csv`。同日は上書き、日付が変わると別ファイル。
- 形式サンプル: `tests/auctions_sample.csv`（ヘッダー一致をテストで固定）。

## 開発環境で動かす

```
python src/EC_Bridge.py                    # 上池袋
python src/EC_Bridge_for_kanme_nakano.py   # 中野
```

必要パッケージ: `ezodf`（値札出力）、`selenium`（「出品」ボタン）。
GUI と CSV は標準ライブラリのみ。`geckodriver.exe` は `src/` に置く（exe には同梱）。

## テスト

```
cd tests
python -m unittest test_ec_bridge_core     # 150 項目
python test_report.py                      # ↑を実行し output/テスト結果.xlsx を生成
```

`serinavi.publish` は実ブラウザが要るためテストしない。`parse_folder_listing` は
`tests/fixtures/folder_listing_sample.html`（合成データ）で、`on_publish` は
`serinavi.publish` を mock して検証する。

- 旧実装（コミット `3fe6c7c`）のロジックを関数として再現し、書き直し後も出力が
  変わらないことを `RegressionTests` で照合。
- `test_report.py` は機能領域ごとのカバレッジも出力。詳細は `tests/TESTING.md`。

## ビルドと配布

```
pip install pyinstaller selenium
python build.py        # → dist/install.exe（EC_Bridge.exe・値札テンプレート・geckodriver を同梱）
```

`build.py` は `EC_Bridge.exe` に `src/geckodriver.exe` と `selenium` を同梱する
（`--add-binary` / `--collect-all selenium`）。利用者側に Python は不要だが、
「出品」を使うには **Firefox 本体** と競りナビにログイン済みのプロファイルが要る。

ビルドしたら **`dist/install.exe` をコミットして push**（`.gitignore` で
`install.exe` だけ追跡対象にしてある）。店側は GitHub の **Code → Download ZIP**
で取得し、`dist/install.exe` を実行 →「インストール」で
`<場所>/<店舗>/EC_Bridge_<店舗>.exe` + `install.json` + `ネット用値札.ods` が展開される。
動作確認は `EC_Bridge_<店舗>.exe --selftest`（`<exe>/output/selftest.txt` に結果）。
