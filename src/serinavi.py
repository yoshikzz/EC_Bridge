# -*- coding: utf-8 -*-
"""競りナビ（ヤフオク店舗ツール）への出品を Selenium で行う。

流れ:
  1. 一括アップロード画面で auctions_YYYYMMDD.csv を取り込む（商品を「保存」で登録）
  2. 店舗フォルダ一覧を開き、HTML から {管理番号: 競りナビ内部ID} を作る
  3. 各商品の編集ページを開き、商品説明を「改行入りHTML版」に差し替えて保存

CSV 側で 9 割（タイトル・価格・フォルダ・状態・発送…）を入れ、
Selenium は「人力では整形が困難な説明欄」だけを触る。

競りナビの HTML はサイト更新で変わり得る。壊れたら以下の定数を直す。
"""

from __future__ import annotations

import os
import re
import time
from typing import Callable

from ec_bridge_core import (AppConfig, Item, build_web_description,
                            management_number, today_ymd)

BASE = "https://auctions.store.yahoo.co.jp/serinavi"
UPLOAD_URL = BASE + "/upload"
FOLDER_LIST_URL = BASE + "/items?folder_id={fid}&sort=-update_date"
EDIT_URL = (BASE + "/items/create"
            "?folder_id={fid}&item_folder_id={fid}&item_id={iid}&action=edit")

FIREFOX_BINARY = r"C:\Program Files\Mozilla Firefox\firefox.exe"
PER_ITEM_PAUSE = 1.5             # bot 検知よけ
UPLOAD_CLICK_ATTEMPTS = 8        # 「決定する」を押し直す上限
UPLOAD_WATCH_SECONDS = 35        # 1回の押下後、画面のアップロード結果を待つ秒数
UPLOAD_OK_TEXT = "受け付け"       # 「商品データN件…を受け付けました」
UPLOAD_ERROR_TEXT = "通信エラー"   # 競りナビが処理成功でも出すことがある

# React の controlled textarea に値を入れて変更を通知する定番ハック
_SET_TEXTAREA_JS = """
const el = arguments[0], val = arguments[1];
const proto = window.HTMLTextAreaElement.prototype;
const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
setter.call(el, val);
el.dispatchEvent(new Event('input',  {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
const dt = document.getElementsByName('description_type')[0];
if (dt) dt.value = '0';
try { if (typeof submitDescription === 'function') submitDescription(); } catch (e) {}
"""


def _current_url(driver) -> str:
    """ログイン遷移中は browsing context が捨てられることがあるので握りつぶす。"""
    try:
        return driver.current_url or ""
    except Exception:
        return ""


def parse_folder_listing(html: str) -> dict[str, str]:
    """フォルダ一覧HTML -> {管理番号(11桁): 競りナビ内部 item_id}。"""

    result: dict[str, str] = {}
    # 各商品は itemCheckbox から始まるブロック。そこで区切って中を見る。
    blocks = re.split(r'(?=name="itemCheckbox")', html)
    for block in blocks:
        cb = re.search(r'name="itemCheckbox"[^>]*value="(\d+)"', block)
        mg = re.search(r'管理番号\s*(\d{11})', block)
        ed = re.search(r'item_id=(\d+)(?:&amp;|&)action=edit', block)
        if not mg:
            continue
        item_id = (ed.group(1) if ed else cb.group(1) if cb else None)
        if item_id:
            result[mg.group(1)] = item_id
    return result


def _make_driver(geckodriver_path: str, profile_dir: str):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    if not profile_dir or not os.path.isdir(profile_dir):
        raise ValueError(
            "有効な Firefox プロファイルフォルダを指定してください。\n"
            "（競りナビにログイン済みのプロファイルを選ぶ）")
    options = Options()
    # 変更前スクレイピング版と同じ: 利用者のログイン済みプロファイルをそのまま使う
    options.profile = profile_dir
    if os.path.isfile(FIREFOX_BINARY):
        options.binary_location = FIREFOX_BINARY
    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
    driver.maximize_window()
    return driver


_KETTEI_XPATH = "//a[normalize-space()='決定する']"


def _kettei_enabled(driver):
    """「決定する」が押せる状態か（ファイル選択後に disabled が外れる）。"""
    from selenium.webdriver.common.by import By
    els = driver.find_elements(By.XPATH, _KETTEI_XPATH)
    return bool(els) and (els[0].get_attribute("disabled") or "false").lower() \
        in ("false", "none", "")


def _click_confirm_modal(driver):
    """「決定する」後に確認ダイアログが出るタイプなら、その実行ボタンも押す。"""
    from selenium.webdriver.common.by import By
    for label in ("アップロードする", "アップロード", "実行する", "はい", "OK"):
        for b in driver.find_elements(
                By.XPATH, "//*[@role='dialog' or contains(@class,'modal') or "
                          "contains(@class,'Modal') or contains(@class,'dialog')]"
                          f"//*[self::button or self::a][normalize-space()='{label}']"):
            try:
                driver.execute_script("arguments[0].click();", b)
            except Exception:
                pass


def _upload_csv(driver, wait, csv_path: str, *, verify=None) -> str:
    """CSV を一括アップロード。

    画面のアップロード結果ログ（「…を受け付けました」）が出て、かつ「通信エラー」が
    消えるまで「決定する」を押し直す。毎回アップロード画面を開き直すので、前の押下の
    エラー表示が残ったまま判定することはない。

    競りナビは処理が通っても「通信エラー」を出すことがあり、そのまま押し直すと
    管理番号が重複登録される（競りナビは重複排除しない）。そのため押し直す前に
    ``verify`` で一覧を確認し、既に登録されていれば止める。

    戻り値: ``"ok"`` / ``"error"``（最後まで通信エラー）/ ``"unknown"``。
    """

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    csv_abs = os.path.abspath(csv_path)
    basename = os.path.basename(csv_abs)
    last = "unknown"

    for attempt in range(1, UPLOAD_CLICK_ATTEMPTS + 1):
        # 毎回まっさらな状態から：画面を開き直してファイルを選び直す
        driver.get(UPLOAD_URL)
        try:
            fi = wait.until(
                EC.presence_of_element_located((By.ID, "uploadFile")))
        except Exception:
            last = "unknown"
            continue
        fi.send_keys(csv_abs)
        try:
            WebDriverWait(driver, 20).until(lambda d: basename in d.page_source)
            WebDriverWait(driver, 30).until(_kettei_enabled)
        except Exception:
            last = "unknown"
            continue

        # 「決定する」をネイティブクリック（JS click だと XHR が中途半端になり
        # 「通信エラー」が出やすい）。駄目なら JS click にフォールバック。
        btn = driver.find_element(By.XPATH, _KETTEI_XPATH)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.5)
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        _click_confirm_modal(driver)

        # この押下の結果ログを見る（画面は開き直しているので前回のエラーは無い）
        deadline = time.time() + UPLOAD_WATCH_SECONDS
        ok_seen = err_seen = False
        while time.time() < deadline:
            src = driver.page_source
            ok_seen = UPLOAD_OK_TEXT in src
            err_seen = UPLOAD_ERROR_TEXT in src
            if ok_seen and not err_seen:
                return "ok"                 # ログ確認・エラーなし → 次へ進む
            if err_seen:
                break                        # 通信エラー → 押し直す
            time.sleep(2)
        last = "error" if err_seen else "unknown"

        # 押し直す前に、実はサーバー側で通っていないか一覧で確認（重複防止）
        if verify is not None:
            try:
                if verify():
                    return "ok"
            except Exception:
                pass
        time.sleep(4)

    return last


def _folder_map(driver, fid: str, wanted: set[str], *, max_pages: int) -> dict[str, str]:
    """フォルダ一覧を新着順で max_pages ページ見て {管理番号: item_id} を作る。"""

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    found: dict[str, str] = {}
    for page in range(1, max_pages + 1):
        url = FOLDER_LIST_URL.format(fid=fid)
        if page > 1:
            url += f"&page={page}"
        driver.get(url)
        try:
            # 一覧が出ないならログイン切れ等。長く待たず次へ回さない。
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.NAME, "itemCheckbox")))
        except Exception:
            break
        time.sleep(1)
        before = len(found)
        found.update(parse_folder_listing(driver.page_source))
        if wanted <= set(found) or len(found) == before:
            break
    return found


def _scan_until_found(driver, fid: str, wanted: set[str],
                      *, tries: int, gap: float, max_pages: int) -> dict[str, str]:
    """アップロード反映待ち。wanted が全部見つかるまで最大 tries 回スキャン。"""
    id_map = _folder_map(driver, fid, wanted, max_pages=max_pages)
    for _ in range(tries - 1):
        if wanted <= set(id_map):
            break
        time.sleep(gap)
        id_map.update(_folder_map(driver, fid, wanted, max_pages=max_pages))
    return id_map


def _set_description(driver, wait, edit_url: str, html_desc: str) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(edit_url)
    ta = wait.until(EC.presence_of_element_located((By.NAME, "Description_plain")))
    # HTMLタグ入力モードへ
    driver.execute_script(
        "try { if (typeof tabModeChange === 'function') tabModeChange(false); }"
        " catch (e) {}")
    driver.execute_script(_SET_TEXTAREA_JS, ta, html_desc)
    save = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='フォルダに保存する']")))
    save.click()
    # 保存後は一覧に戻る想定。戻らなくてもエラー表示が無ければ良しとする。
    try:
        wait.until(lambda d: "action=edit" not in d.current_url)
    except Exception:
        time.sleep(2)


def publish(items: list[Item], config: AppConfig, csv_path: str, *,
            geckodriver_path: str, profile_dir: str,
            confirm: Callable[[str], bool],
            progress: Callable[[int, int, str], None] | None = None) -> list[str]:
    """出品処理。失敗した商品の説明リストを返す（空なら全成功）。"""

    from selenium.webdriver.support.ui import WebDriverWait

    if not items:
        raise ValueError("出品する商品がありません。")
    if not os.path.isfile(geckodriver_path):
        raise ValueError(f"geckodriver.exe が見つかりません: {geckodriver_path}")

    driver = _make_driver(geckodriver_path, profile_dir)
    wait = WebDriverWait(driver, 40)
    failures: list[str] = []
    ymd = today_ymd()
    total = len(items)
    done = 0
    try:
        # 一括アップロード画面を「ログインの関門」にする。
        # セッションが残っていれば /serinavi/upload に直行できる（ダイアログ無しで続行）。
        # 未ログインならログイン画面へリダイレクトされる。
        driver.get(UPLOAD_URL)
        if "/serinavi/" not in _current_url(driver):
            if not confirm(
                    "Firefoxで競りナビにログインしてください。\n"
                    "（ログイン画面では「Yahoo! JAPAN IDでログイン」を押す）\n\n"
                    "ログインが終わったら OK を押してください。"):
                return ["キャンセルされました"]
            driver.get(UPLOAD_URL)
            if "/serinavi/" not in _current_url(driver):
                return ["競りナビにログインできていません。ログイン後にもう一度お試しください。"]

        # 店舗ごとに管理番号・対象フォルダを先に確定
        by_shop: dict[str, list[tuple[int, Item]]] = {}
        for seq, item in enumerate(items, start=1):
            by_shop.setdefault(item.shop, []).append((seq, item))
        plan = []   # [(shop, spec, {seq: mgmt}, wanted_set)]
        for shop, entries in by_shop.items():
            spec = config.shop(shop)
            mgmt_of = {seq: management_number(spec.shop_id, *ymd, seq)
                       for seq, _ in entries}
            plan.append((shop, spec, mgmt_of, set(mgmt_of.values())))

        # 一覧は 1 ページ 50 件。1 店舗に大量アップロードするときはページ数を増やす。
        def _pages_for(wanted: set[str], base: int) -> int:
            return base + (len(wanted) - 1) // 50

        # --- アップロード ＋ 一覧で結果検証 ---
        # 新着順の先頭ページを見るだけの「速い確認」。アップロードが通っていれば
        # 対象商品はここに出る。何も出なければ失敗と即断する（延々と探さない）。
        def _probe() -> dict[str, dict[str, str]]:
            return {shop: _folder_map(driver, spec.folder_id, wanted,
                                      max_pages=_pages_for(wanted, 1))
                    for shop, spec, _, wanted in plan}

        def _any_found(maps) -> bool:
            return any(set(maps[shop]) & wanted for shop, _, _, wanted in plan)

        # アップロード：画面の結果ログを確認できるまで「決定する」を押し直す。
        # verify で一覧を見てから押し直すので、通信エラー表示でも実は通っていた
        # 場合に重複登録しない。
        status = _upload_csv(driver, wait, csv_path,
                             verify=lambda: _any_found(_probe()))

        time.sleep(4)
        id_maps = _probe()
        if not _any_found(id_maps):
            # 反映が遅れているだけかもしれないので少しだけ待って再確認
            for _ in range(4):
                time.sleep(15)
                id_maps = _probe()
                if _any_found(id_maps):
                    break

        if not _any_found(id_maps):
            hint = "（競りナビが『通信エラー』を返し続けています）" if status == "error" else ""
            return [f"一括アップロードに失敗しました{hint}。CSV は "
                    f"{os.path.basename(csv_path)} に出力済みです。"
                    "競りナビにログインし直すか、時間をおいて再実行してください。"]

        # ここまで来たらアップロードは通っている。全件そろうまで一覧を追う。
        id_maps = {shop: _scan_until_found(driver, spec.folder_id, wanted,
                                           tries=5, gap=12,
                                           max_pages=_pages_for(wanted, 3))
                   for shop, spec, _, wanted in plan}

        # --- 各商品の説明を改行入り版に更新 ---
        for shop, spec, mgmt_of, wanted in plan:
            id_map = id_maps[shop]
            entries = by_shop[shop]
            for seq, item in entries:
                mgmt = mgmt_of[seq]
                label = f"{mgmt} {item.brand} {item.name}".strip()
                item_id = id_map.get(mgmt)
                done += 1
                if not item_id:
                    failures.append(f"{label} … 一覧に見つからず（CSV分は登録済みの可能性）")
                    continue
                try:
                    _set_description(
                        driver, wait,
                        EDIT_URL.format(fid=spec.folder_id, iid=item_id),
                        build_web_description(item, config, multiline=True))
                except Exception as exc:  # noqa: BLE001
                    failures.append(f"{label} … {exc}")
                if progress:
                    progress(done, total, label)
                time.sleep(PER_ITEM_PAUSE)
    finally:
        # ブラウザは開いたままにして利用者が結果を確認できるようにする
        pass
    return failures
