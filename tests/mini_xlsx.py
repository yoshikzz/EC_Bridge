# -*- coding: utf-8 -*-
"""依存ライブラリ無しの最小 XLSX ライター。

必要な機能だけ:
  - 複数シート
  - 文字列 / 数値 / 真偽値セル
  - セル書式（太字・背景色・文字色・罫線・配置・折り返し・表示形式）
  - 列幅・ウィンドウ枠固定・オートフィルター・セル結合

Excel / LibreOffice Calc の両方で開けることを確認済み。
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
_NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"


def col_letter(index: int) -> str:
    """1 始まりの列番号 -> 'A', 'B', ... 'AA'。"""

    result = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def cell_ref(row: int, col: int) -> str:
    return f"{col_letter(col)}{row}"


@dataclass(frozen=True)
class Style:
    bold: bool = False
    bg: str | None = None            # "RRGGBB"
    color: str | None = None         # "RRGGBB"
    border: bool = False
    align: str | None = None         # left/center/right
    valign: str | None = None        # top/center/bottom
    wrap: bool = False
    num_fmt: str | None = None       # 例 "0", "0.0", "@"


@dataclass
class _Sheet:
    name: str
    _cells: dict[tuple[int, int], tuple[object, int]] = field(default_factory=dict)
    col_widths: dict[int, float] = field(default_factory=dict)
    freeze_row: int = 0
    freeze_col: int = 0
    autofilter: tuple[int, int, int, int] | None = None
    merges: list[tuple[int, int, int, int]] = field(default_factory=list)
    _max_row: int = 0
    _max_col: int = 0

    def write(self, row: int, col: int, value: object, style: int = 0) -> None:
        self._cells[(row, col)] = (value, style)
        self._max_row = max(self._max_row, row)
        self._max_col = max(self._max_col, col)

    def write_row(self, row: int, start_col: int, values, styles=None) -> None:
        for offset, value in enumerate(values):
            style = 0
            if styles is not None:
                style = styles[offset] if isinstance(styles, (list, tuple)) else styles
            self.write(row, start_col + offset, value, style)

    def set_col_width(self, col: int, width: float) -> None:
        self.col_widths[col] = width

    def freeze(self, row: int = 0, col: int = 0) -> None:
        self.freeze_row, self.freeze_col = row, col

    def set_autofilter(self, r1: int, c1: int, r2: int, c2: int) -> None:
        self.autofilter = (r1, c1, r2, c2)

    def merge(self, r1: int, c1: int, r2: int, c2: int) -> None:
        self.merges.append((r1, c1, r2, c2))


class Workbook:
    def __init__(self) -> None:
        self._sheets: list[_Sheet] = []
        self._styles: list[Style] = [Style()]
        self._shared: list[str] = []
        self._shared_index: dict[str, int] = {}

    # -- 構築 -----------------------------------------------------------

    def add_sheet(self, name: str) -> _Sheet:
        sheet = _Sheet(name=name[:31])
        self._sheets.append(sheet)
        return sheet

    def add_style(self, **kwargs) -> int:
        style = Style(**kwargs)
        if style in self._styles:
            return self._styles.index(style)
        self._styles.append(style)
        return len(self._styles) - 1

    def _string_id(self, text: str) -> int:
        if text not in self._shared_index:
            self._shared_index[text] = len(self._shared)
            self._shared.append(text)
        return self._shared_index[text]

    # -- 出力 -----------------------------------------------------------

    def save(self, path: str) -> None:
        # 先にシート XML を生成して共有文字列を確定させてから書き出す。
        sheet_xml = [self._sheet_xml(sheet) for sheet in self._sheets]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", self._content_types())
            zf.writestr("_rels/.rels", self._root_rels())
            zf.writestr("xl/workbook.xml", self._workbook_xml())
            zf.writestr("xl/_rels/workbook.xml.rels", self._workbook_rels())
            zf.writestr("xl/styles.xml", self._styles_xml())
            zf.writestr("xl/sharedStrings.xml", self._shared_strings_xml())
            for i, xml in enumerate(sheet_xml, start=1):
                zf.writestr(f"xl/worksheets/sheet{i}.xml", xml)

    def _content_types(self) -> str:
        sheets = "".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.'
            f'spreadsheetml.worksheet+xml"/>'
            for i in range(1, len(self._sheets) + 1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Types xmlns="{_NS_CT}">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
            'package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            f'{sheets}</Types>'
        )

    def _root_rels(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{_NS_PR}">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

    def _workbook_xml(self) -> str:
        sheets = "".join(
            f'<sheet name="{escape(s.name)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, s in enumerate(self._sheets, start=1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{_NS_MAIN}" xmlns:r="{_NS_REL}">'
            f'<sheets>{sheets}</sheets></workbook>'
        )

    def _workbook_rels(self) -> str:
        rels = "".join(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(self._sheets) + 1)
        )
        n = len(self._sheets)
        rels += (
            f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            f'<Relationship Id="rId{n + 2}" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{_NS_PR}">{rels}</Relationships>'
        )

    def _styles_xml(self) -> str:
        # カスタム表示形式
        fmt_ids: dict[str, int] = {}
        num_fmts_xml = ""
        next_fmt = 164
        for style in self._styles:
            if style.num_fmt and style.num_fmt not in fmt_ids:
                fmt_ids[style.num_fmt] = next_fmt
                num_fmts_xml += (
                    f'<numFmt numFmtId="{next_fmt}" '
                    f'formatCode="{escape(style.num_fmt)}"/>'
                )
                next_fmt += 1

        # フォント
        font_keys: list[tuple[bool, str | None]] = [(False, None)]
        for style in self._styles:
            key = (style.bold, style.color)
            if key not in font_keys:
                font_keys.append(key)
        fonts_xml = ""
        for bold, color in font_keys:
            parts = '<sz val="11"/><name val="Yu Gothic"/>'
            if bold:
                parts = "<b/>" + parts
            if color:
                parts += f'<color rgb="FF{color}"/>'
            fonts_xml += f"<font>{parts}</font>"

        # 塗りつぶし（index 0,1 は予約）
        fill_keys: list[str | None] = [None, None]
        for style in self._styles:
            if style.bg and style.bg not in fill_keys:
                fill_keys.append(style.bg)
        fills_xml = (
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
        )
        for bg in fill_keys[2:]:
            fills_xml += (
                f'<fill><patternFill patternType="solid">'
                f'<fgColor rgb="FF{bg}"/><bgColor indexed="64"/></patternFill></fill>'
            )

        # 罫線
        borders_xml = (
            "<border><left/><right/><top/><bottom/><diagonal/></border>"
            '<border><left style="thin"><color indexed="64"/></left>'
            '<right style="thin"><color indexed="64"/></right>'
            '<top style="thin"><color indexed="64"/></top>'
            '<bottom style="thin"><color indexed="64"/></bottom><diagonal/></border>'
        )

        # cellXfs
        xfs = ""
        for style in self._styles:
            font_id = font_keys.index((style.bold, style.color))
            fill_id = fill_keys.index(style.bg) if style.bg in fill_keys else 0
            border_id = 1 if style.border else 0
            num_id = fmt_ids.get(style.num_fmt, 0)
            attrs = (
                f'numFmtId="{num_id}" fontId="{font_id}" fillId="{fill_id}" '
                f'borderId="{border_id}" xfId="0"'
            )
            flags = []
            if num_id:
                flags.append('applyNumberFormat="1"')
            if font_id:
                flags.append('applyFont="1"')
            if fill_id:
                flags.append('applyFill="1"')
            if border_id:
                flags.append('applyBorder="1"')
            align = ""
            if style.align or style.valign or style.wrap:
                a = []
                if style.align:
                    a.append(f'horizontal="{style.align}"')
                if style.valign:
                    a.append(f'vertical="{style.valign}"')
                if style.wrap:
                    a.append('wrapText="1"')
                align = f'<alignment {" ".join(a)}/>'
                flags.append('applyAlignment="1"')
            xfs += f'<xf {attrs} {" ".join(flags)}>{align}</xf>'

        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<styleSheet xmlns="{_NS_MAIN}">'
            f'<numFmts count="{len(fmt_ids)}">{num_fmts_xml}</numFmts>'
            f'<fonts count="{len(font_keys)}">{fonts_xml}</fonts>'
            f'<fills count="{len(fill_keys)}">{fills_xml}</fills>'
            f'<borders count="2">{borders_xml}</borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" '
            'borderId="0"/></cellStyleXfs>'
            f'<cellXfs count="{len(self._styles)}">{xfs}</cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
            '</cellStyles></styleSheet>'
        )

    def _shared_strings_xml(self) -> str:
        items = "".join(
            f"<si><t xml:space=\"preserve\">{escape(s)}</t></si>" for s in self._shared
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="{_NS_MAIN}" count="{len(self._shared)}" '
            f'uniqueCount="{len(self._shared)}">{items}</sst>'
        )

    def _sheet_xml(self, sheet: _Sheet) -> str:
        max_row = max(sheet._max_row, 1)
        max_col = max(sheet._max_col, 1)
        dim = f"A1:{cell_ref(max_row, max_col)}"

        cols_xml = ""
        if sheet.col_widths:
            entries = "".join(
                f'<col min="{c}" max="{c}" width="{w:.2f}" customWidth="1"/>'
                for c, w in sorted(sheet.col_widths.items())
            )
            cols_xml = f"<cols>{entries}</cols>"

        pane_xml = ""
        if sheet.freeze_row or sheet.freeze_col:
            x, y = sheet.freeze_col, sheet.freeze_row
            top_left = cell_ref(y + 1, x + 1)
            state = "frozen"
            active = "bottomRight"
            if x and not y:
                active = "topRight"
            elif y and not x:
                active = "bottomLeft"
            pane_xml = (
                f'<pane xSplit="{x}" ySplit="{y}" topLeftCell="{top_left}" '
                f'activePane="{active}" state="{state}"/>'
            )

        rows_xml = ""
        for r in range(1, max_row + 1):
            row_cells = {c: v for (rr, c), v in sheet._cells.items() if rr == r}
            if not row_cells:
                continue
            cells_xml = ""
            for c in sorted(row_cells):
                value, style_id = row_cells[c]
                ref = cell_ref(r, c)
                s_attr = f' s="{style_id}"' if style_id else ""
                if isinstance(value, bool):
                    cells_xml += f'<c r="{ref}"{s_attr} t="b"><v>{1 if value else 0}</v></c>'
                elif isinstance(value, (int, float)):
                    cells_xml += f'<c r="{ref}"{s_attr}><v>{value}</v></c>'
                else:
                    sid = self._string_id("" if value is None else str(value))
                    cells_xml += f'<c r="{ref}"{s_attr} t="s"><v>{sid}</v></c>'
            rows_xml += f'<row r="{r}">{cells_xml}</row>'

        merges_xml = ""
        if sheet.merges:
            entries = "".join(
                f'<mergeCell ref="{cell_ref(r1, c1)}:{cell_ref(r2, c2)}"/>'
                for r1, c1, r2, c2 in sheet.merges
            )
            merges_xml = f'<mergeCells count="{len(sheet.merges)}">{entries}</mergeCells>'

        autofilter_xml = ""
        if sheet.autofilter:
            r1, c1, r2, c2 = sheet.autofilter
            autofilter_xml = (
                f'<autoFilter ref="{cell_ref(r1, c1)}:{cell_ref(r2, c2)}"/>'
            )

        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<worksheet xmlns="{_NS_MAIN}" xmlns:r="{_NS_REL}">'
            f'<dimension ref="{dim}"/>'
            f'<sheetViews><sheetView workbookViewId="0">{pane_xml}</sheetView></sheetViews>'
            '<sheetFormatPr defaultRowHeight="15"/>'
            f'{cols_xml}<sheetData>{rows_xml}</sheetData>'
            f'{autofilter_xml}{merges_xml}</worksheet>'
        )
