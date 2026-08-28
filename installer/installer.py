# -*- coding: utf-8 -*-
"""EC_Bridge インストーラ（install.exe になる）。

店舗を選んで「インストール」を押すと、インストール先フォルダに
  <選択店舗>フォルダ/
  ├── EC_Bridge_<店舗>.exe   … 同梱の EC_Bridge.exe をコピーしてリネーム
  ├── ネット用値札.ods        … 値札テンプレート
  └── install.json            … {"shop": "<店舗>"}（起動時に読まれる）
を作成し、デスクトップにショートカットを置く。
値札 ODS・出品 CSV の出力先はアプリ初回起動時に利用者が選ぶ。

PyInstaller で --add-data により EC_Bridge.exe と ネット用値札.ods を同梱する。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SHOPS = ["上池袋", "要町", "中野"]
TEMPLATE_NAME = "ネット用値札.ods"
APP_EXE_NAME = "EC_Bridge.exe"


def bundled(name: str) -> str:
    """PyInstaller 同梱ファイル（開発時はこのファイルの隣）。"""

    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def default_install_root() -> str:
    return os.path.join(os.path.expanduser("~"), "EC_Bridge")


def make_desktop_shortcut(target: str, name: str) -> None:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        return
    lnk = os.path.join(desktop, f"{name}.lnk")
    workdir = os.path.dirname(target)
    ps = (
        "$w = New-Object -ComObject WScript.Shell; "
        f"$s = $w.CreateShortcut('{lnk}'); "
        f"$s.TargetPath = '{target}'; "
        f"$s.WorkingDirectory = '{workdir}'; "
        "$s.Save()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, timeout=20)
    except Exception:
        pass  # ショートカット作成失敗は致命的ではない


def install(shop: str, root_dir: str) -> str:
    dest = os.path.join(root_dir, shop)
    os.makedirs(dest, exist_ok=True)

    exe_path = os.path.join(dest, f"EC_Bridge_{shop}.exe")
    shutil.copyfile(bundled(APP_EXE_NAME), exe_path)
    shutil.copyfile(bundled(TEMPLATE_NAME), os.path.join(dest, TEMPLATE_NAME))
    with open(os.path.join(dest, "install.json"), "w", encoding="utf-8") as fp:
        json.dump({"shop": shop}, fp, ensure_ascii=False, indent=2)

    make_desktop_shortcut(exe_path, f"EC_Bridge（{shop}）")
    return exe_path


class InstallerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("EC_Bridge インストーラ")
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="店舗を選択してください", font=("", 11, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.v_shop = tk.StringVar(value=SHOPS[0])
        for i, shop in enumerate(SHOPS):
            ttk.Radiobutton(frame, text=shop, value=shop, variable=self.v_shop,
                            padding=4).grid(row=1, column=i, sticky="w")

        ttk.Label(frame, text="インストール先").grid(row=2, column=0, sticky="w",
                                                     pady=(12, 2))
        self.v_dir = tk.StringVar(value=default_install_root())
        ttk.Entry(frame, textvariable=self.v_dir, width=44).grid(
            row=3, column=0, columnspan=2, sticky="we")
        ttk.Button(frame, text="参照", command=self._browse).grid(row=3, column=2,
                                                                  padx=4)

        ttk.Button(frame, text="インストール", command=self._install).grid(
            row=4, column=0, columnspan=3, pady=(16, 0), sticky="we")

        self.v_msg = tk.StringVar()
        ttk.Label(frame, textvariable=self.v_msg, foreground="#0a0").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _browse(self) -> None:
        chosen = filedialog.askdirectory(title="インストール先フォルダ",
                                         initialdir=self.v_dir.get())
        if chosen:
            self.v_dir.set(chosen)

    def _install(self) -> None:
        shop = self.v_shop.get()
        root_dir = self.v_dir.get().strip()
        if not root_dir:
            messagebox.showerror("エラー", "インストール先を指定してください。")
            return
        try:
            exe_path = install(shop, root_dir)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("エラー", f"インストールに失敗しました。\n\n{exc}")
            return
        self.v_msg.set(f"完了: {exe_path}")
        if messagebox.askyesno("完了",
                               f"{shop} 版をインストールしました。\n今すぐ起動しますか？"):
            try:
                os.startfile(exe_path)  # type: ignore[attr-defined]
            except OSError:
                pass


def main() -> None:
    root = tk.Tk()
    InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
