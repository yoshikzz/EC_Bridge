# -*- coding: utf-8 -*-
"""配布用エントリポイント（EC_Bridge.exe になる）。

exe の隣にある install.json の "shop" を読み、その店舗向けの設定で起動する。
install.json が無い場合は上池袋で起動する。

`EC_Bridge.exe --selftest` … GUI を出さずに値札/CSV 出力を1件試し、
結果を output/selftest.txt に書いて終了する（ビルド後の動作確認用）。
"""

import os
import sys

from ec_bridge_core import install_config, make_config, run


def _selftest(config) -> int:
    import traceback

    from ec_bridge_core import (Item, default_output_dir, export_auction_csv,
                                write_price_tags)

    lines: list[str] = []
    try:
        item = Item(shop=config.default_shop, brand="TEST", brand_kana="テスト",
                    name="動作確認", price="1000", genre="トップス",
                    rank2="目立った傷や汚れなし", m1="60", m2="45", m3="55", m4="24")
        item.condition_text = config.condition_text("中古品", "", "", "トップス")
        lines.append("値札: " + write_price_tags([item], config))
        lines.append("CSV : " + export_auction_csv([item], config))
        lines.append("OK")
    except Exception:  # noqa: BLE001
        lines.append(traceback.format_exc())
    with open(os.path.join(default_output_dir(), "selftest.txt"),
              "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    return 0 if lines[-1] == "OK" else 1


def main() -> None:
    config = make_config(install_config().get("shop", "上池袋"))
    if "--selftest" in sys.argv:
        sys.exit(_selftest(config))
    run(config)


if __name__ == "__main__":
    main()
