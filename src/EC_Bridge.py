# -*- coding: utf-8 -*-
"""EC_Bridge（標準版 = 上池袋）を開発環境から起動する。

配布 exe は src/app.py（install.json で店舗を切り替え）。
店舗ごとの差分は ec_bridge_core.make_config にまとまっている。
"""

from ec_bridge_core import make_config, run

CONFIG = make_config("上池袋")

if __name__ == "__main__":
    run(CONFIG)
