# -*- coding: utf-8 -*-
"""配布物をビルドする（開発マシンでのみ実行。要 PyInstaller）。

    pip install pyinstaller
    python build.py

成果物: dist/install.exe
  - install.exe を店の PC に渡す
  - install.exe を実行 → 店舗を選ぶ → EC_Bridge_<店舗>.exe が作られる

install.exe には EC_Bridge.exe（全店舗共通・install.json で切替）と
値札テンプレート ネット用値札.ods が同梱される。
"""

from __future__ import annotations

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
TEMPLATE = os.path.join(SRC, "ネット用値札.ods")
GECKODRIVER = os.path.join(SRC, "geckodriver.exe")
WORK = os.path.join(ROOT, "_build")
DIST = os.path.join(ROOT, "dist")
ADD = ";" if os.name == "nt" else ":"


def _run(args: list[str]) -> None:
    import PyInstaller.__main__

    print(">>> pyinstaller " + " ".join(args))
    PyInstaller.__main__.run(args)


def build_app_exe() -> str:
    """全店舗共通の EC_Bridge.exe をビルドして絶対パスを返す。"""

    out = os.path.join(WORK, "app")
    _run([
        os.path.join(SRC, "app.py"),
        "--name", "EC_Bridge",
        "--onefile", "--windowed", "--noconfirm", "--clean",
        "--paths", SRC,
        "--collect-all", "ezodf",
        "--collect-all", "selenium",
        "--hidden-import", "lxml._elementpath",
        "--add-binary", f"{GECKODRIVER}{ADD}.",
        "--distpath", out,
        "--workpath", os.path.join(WORK, "app-work"),
        "--specpath", WORK,
    ])
    return os.path.join(out, "EC_Bridge.exe")


def build_installer_exe(app_exe: str) -> str:
    _run([
        os.path.join(ROOT, "installer", "installer.py"),
        "--name", "install",
        "--onefile", "--windowed", "--noconfirm", "--clean",
        "--add-data", f"{app_exe}{ADD}.",
        "--add-data", f"{TEMPLATE}{ADD}.",
        "--distpath", DIST,
        "--workpath", os.path.join(WORK, "inst-work"),
        "--specpath", WORK,
    ])
    return os.path.join(DIST, "install.exe")


def main() -> None:
    if not os.path.isfile(TEMPLATE):
        sys.exit(f"値札テンプレートが見つかりません: {TEMPLATE}")
    if not os.path.isfile(GECKODRIVER):
        sys.exit(f"geckodriver.exe が見つかりません: {GECKODRIVER}")
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)

    app_exe = build_app_exe()
    installer_exe = build_installer_exe(app_exe)

    if "--keep-app-exe" in sys.argv:      # 動作確認用に単体 exe も残す
        shutil.copyfile(app_exe, os.path.join(DIST, "EC_Bridge.exe"))
    shutil.rmtree(WORK, ignore_errors=True)
    print(f"\n完成: {installer_exe}")


if __name__ == "__main__":
    main()
