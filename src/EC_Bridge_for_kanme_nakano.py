# -*- coding: utf-8 -*-
"""EC_Bridge（要町・中野版 = 既定は中野）を開発環境から起動する。

配布 exe は src/app.py（install.json で店舗を切り替え）。
"""

from ec_bridge_core import make_config, run

CONFIG = make_config("中野")

if __name__ == "__main__":
    run(CONFIG)
