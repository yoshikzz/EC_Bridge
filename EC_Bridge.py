from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime
import time
import ezodf
import os
import re
import json
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import sys




if hasattr(sys, '_MEIPASS'):
    base_path = os.path.dirname(sys.executable)  # exeファイルのディレクトリ
else:
    base_path = os.path.dirname(__file__)  # スクリプトのディレクトリ

settings_filename = f"{os.path.splitext(os.path.basename(sys.executable if hasattr(sys, '_MEIPASS') else __file__))[0]}_settings.json"
settings_path = os.path.join(base_path, settings_filename)


def load_settings():
    if not os.path.exists(settings_path):
        return {}
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings():
    settings = {
        'last_shop': shop_val.get(),
        'firefox_profile_path': firefox_profile_path_var.get()
    }
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def browse_firefox_profile():
    selected_dir = filedialog.askdirectory(
        title='Firefoxプロファイルフォルダを選択',
        initialdir=firefox_profile_path_var.get() if os.path.isdir(firefox_profile_path_var.get()) else base_path
    )
    if selected_dir:
        firefox_profile_path_var.set(selected_dir)
# 時間取得関数
def Datetime():
    dt = datetime.datetime.now()
    year = dt.year

    if dt.month < 10:
        month = "0" + str(dt.month)
    else:
        month = dt.month
    if dt.day < 10:
        day = "0" + str(dt.day)
    else:
        day = dt.day
    return year, month, day

# ヤフオク入力用時間変数出力関数
def Date(year, month, day):
    date = int(str(year % 100) + str(month) + str(day))
    return date

# GUI表示用時間変数出力関数
def P_date(year, month, day):
    p_date = str(year) + "年" + str(month) + "月" + str(day) + "日"
    return p_date

# ショップID取得関数
def Get_shop(shop_val):
    shop = shop_val.get()
    if shop == '上池袋':
        shop_id = 22
    elif shop == '要町':
        shop_id = 11
    elif shop == '中野':
        shop_id = 33
    return shop_id

# ラジオボタン選択関数
def select_focused_radiobutton(event):
    widget = event.widget
    if isinstance(widget, ttk.Radiobutton):
        widget.invoke()

# コンボボックスオープン関数
def open_combobox(event):
    widget = event.widget
    if isinstance(widget, ttk.Combobox):
        widget.event_generate('<Button-1>')

def disable_dropdown(event):
    # 空の関数を設定することで、ドロップダウンメニューの自動開閉を無効化する
    return 'break'

def button1():
    for error_delete in error_log:
        error_delete.destroy()
    value = price_name.get()

    if not value.isdigit():
        error_label=ttk.Label(frame1, text="値段を入力してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    elif genre_val.get() == "選択してください":
        error_label=ttk.Label(frame1, text="ジャンルを選択してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    else:
        next_button_action()

def button2():
    for error_delete in error_log:
        error_delete.destroy()
    value = price_name.get()
    global current_idx
    if not value.isdigit():
        error_label=ttk.Label(frame1, text="値段を入力してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    elif genre_val.get() == "選択してください":
        error_label=ttk.Label(frame1, text="ジャンルを選択してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    else:
        if current_idx > 0:
            item_info = [
                shop_val.get(), brand_name.get(), brand_kana.get(), item_name.get(),
                color_name.get(), price_name.get(), grb_val.get(), genre_val.get(),
                situation_val.get(), rank_val.get(), rank2_val.get(), ss_text_val.get(), s_text_val.get(),postage_val.get()
            ]
            item_info.extend(input2)
            if current_idx <= len(item_data):
                item_data[current_idx - 1] = item_info
            else:
                item_data.append(item_info)
        calc(filepath, item_data)

def button3():
    for error_delete in error_log:
        error_delete.destroy()
    value = price_name.get()
    global current_idx
    if not value.isdigit():
        error_label=ttk.Label(frame1, text="数字を入力してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    elif genre_val.get() == "選択してください":
        error_label=ttk.Label(frame1, text="ジャンルを選択してください",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])
    else:
        if current_idx > 0:
            item_info = [
                shop_val.get(), brand_name.get(), brand_kana.get(), item_name.get(),
                color_name.get(), price_name.get(), grb_val.get(), genre_val.get(),
                situation_val.get(), rank_val.get(), rank2_val.get(), ss_text_val.get(), s_text_val.get(),postage_val.get()
            ]
            item_info.extend(input2)
            if current_idx <= len(item_data):
                item_data[current_idx - 1] = item_info
            else:
                item_data.append(item_info)
        yahoo_auction()


# コンボボックスナビゲーション関数
def navigate_combobox(event):
    widget = event.widget
    if isinstance(widget, ttk.Combobox):
        widget.event_generate('<Down>')

def measure(frame1, event=None, genre_val=None, input2=None, n_name=None, m1_name=None, m2_name=None, m3_name=None, m4_name=None, motion_val=None):
    genre = genre_val.get()
    motion_val =StringVar(value="")
    size = "-"
    motion_value = ""
    n_name_value = ""
    for widget in widgets:
        if isinstance(widget, ttk.Entry):
            widget.destroy()  # Entryウィジェットを破棄する
        if isinstance(widget, ttk.Label):
            widget.destroy()  # Labelウィジェットを破棄する
        elif isinstance(widget, StringVar):
            widget.set("")  # StringVarの値を空にする


    if genre == 'トップス':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        m_label = ttk.Label(frame1, text="実寸サイズ")
        m_label.grid(row=13, column=0)

        m1_label = ttk.Label(frame1, text="着丈:")
        m1_entry = ttk.Entry(frame1, textvariable=m1_name, width=8)
        mc1_label = ttk.Label(frame1, text="cm")

        m1_label.grid(row=13, column=1, sticky=W)
        m1_entry.grid(row=13, column=1, sticky=W, padx=35)
        mc1_label.grid(row=13, column=1, sticky=W, padx=90)

        m2_label = ttk.Label(frame1, text="肩幅:")
        m2_entry = ttk.Entry(frame1, textvariable=m2_name, width=8)
        mc2_label = ttk.Label(frame1, text="cm")

        m2_label.grid(row=13, column=1, sticky=W, padx=150)
        m2_entry.grid(row=13, column=1, sticky=W, padx=185)
        mc2_label.grid(row=13, column=1, sticky=W, padx=240)

        m3_label = ttk.Label(frame1, text="身幅:")
        m3_entry = ttk.Entry(frame1, textvariable=m3_name, width=8)
        mc3_label = ttk.Label(frame1, text="cm")

        m3_label.grid(row=14, column=1, sticky=W)
        m3_entry.grid(row=14, column=1, sticky=W, padx=35)
        mc3_label.grid(row=14, column=1, sticky=W, padx=90)

        m4_label = ttk.Label(frame1, text="袖丈:")
        m4_entry = ttk.Entry(frame1, textvariable=m4_name, width=8)
        mc4_label = ttk.Label(frame1, text="cm")

        m4_label.grid(row=14, column=1, sticky=W, padx=150)
        m4_entry.grid(row=14, column=1, sticky=W, padx=185)
        mc4_label.grid(row=14, column=1, sticky=W, padx=240)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value != "その他":
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        m1_name.trace_add('write', add_to_input2)
        m2_name.trace_add('write', add_to_input2)
        m3_name.trace_add('write', add_to_input2)
        m4_name.trace_add('write', add_to_input2)
        grb_val.trace_add('write', update_t_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, m_label, m1_label, m1_entry, mc1_label, m2_label, m2_entry, mc2_label, m3_label, m3_entry, mc3_label, m4_label, m4_entry, mc4_label])

    elif genre == 'ボトムス':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        m_label = ttk.Label(frame1, text="実寸サイズ")
        m_label.grid(row=13, column=0)

        m1_label = ttk.Label(frame1, text="ウエスト:")
        m1_entry = ttk.Entry(frame1, textvariable=m1_name, width=8)
        mc1_label = ttk.Label(frame1, text="cm")

        m1_label.grid(row=13, column=1, sticky=W)
        m1_entry.grid(row=13, column=1, sticky=W, padx=35)
        mc1_label.grid(row=13, column=1, sticky=W, padx=90)

        m2_label = ttk.Label(frame1, text="股上:")
        m2_entry = ttk.Entry(frame1, textvariable=m2_name, width=8)
        mc2_label = ttk.Label(frame1, text="cm")

        m2_label.grid(row=13, column=1, sticky=W, padx=150)
        m2_entry.grid(row=13, column=1, sticky=W, padx=185)
        mc2_label.grid(row=13, column=1, sticky=W, padx=240)

        m3_label = ttk.Label(frame1, text="股下:")
        m3_entry = ttk.Entry(frame1, textvariable=m3_name, width=8)
        mc3_label = ttk.Label(frame1, text="cm")

        m3_label.grid(row=14, column=1, sticky=W)
        m3_entry.grid(row=14, column=1, sticky=W, padx=35)
        mc3_label.grid(row=14, column=1, sticky=W, padx=90)

        m4_label = ttk.Label(frame1, text="裾幅:")
        m4_entry = ttk.Entry(frame1, textvariable=m4_name, width=8)
        mc4_label = ttk.Label(frame1, text="cm")

        m4_label.grid(row=14, column=1, sticky=W, padx=150)
        m4_entry.grid(row=14, column=1, sticky=W, padx=185)
        mc4_label.grid(row=14, column=1, sticky=W, padx=240)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value != "その他":
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        m1_name.trace_add('write', add_to_input2)
        m2_name.trace_add('write', add_to_input2)
        m3_name.trace_add('write', add_to_input2)
        m4_name.trace_add('write', add_to_input2)
        grb_val.trace_add('write', update_t_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, m_label, m1_label, m1_entry, mc1_label, m2_label, m2_entry, mc2_label, m3_label, m3_entry, mc3_label, m4_label, m4_entry, mc4_label])

    elif genre == 'シューズ':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        m_label = ttk.Label(frame1, text="実寸サイズ")
        m_label.grid(row=13, column=0)

        m1_label = ttk.Label(frame1, text="アウトソール全長:")
        m1_entry = ttk.Entry(frame1, textvariable=m1_name, width=8)
        mc1_label = ttk.Label(frame1, text="cm")

        m1_label.grid(row=13, column=1, sticky=W)
        m1_entry.grid(row=13, column=1, sticky=W, padx=85)
        mc1_label.grid(row=13, column=1, sticky=W, padx=140)

        m2_label = ttk.Label(frame1, text="幅:")
        m2_entry = ttk.Entry(frame1, textvariable=m2_name, width=8)
        mc2_label = ttk.Label(frame1, text="cm")

        m2_label.grid(row=13, column=1, sticky=W, padx=180)
        m2_entry.grid(row=13, column=1, sticky=W, padx=205)
        mc2_label.grid(row=13, column=1, sticky=W, padx=260)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value != "その他":
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        m1_name.trace_add('write', add_to_input2)
        m2_name.trace_add('write', add_to_input2)
        grb_val.trace_add('write', update_t_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, m_label, m1_label, m1_entry, mc1_label, m2_label, m2_entry, mc2_label])

    elif genre == 'バッグ':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        m_label = ttk.Label(frame1, text="実寸サイズ")
        m_label.grid(row=13, column=0)

        m1_label = ttk.Label(frame1, text="横:")
        m1_entry = ttk.Entry(frame1, textvariable=m1_name, width=8)
        mc1_label = ttk.Label(frame1, text="cm")

        m1_label.grid(row=13, column=1, sticky=W)
        m1_entry.grid(row=13, column=1, sticky=W, padx=35)
        mc1_label.grid(row=13, column=1, sticky=W, padx=90)

        m2_label = ttk.Label(frame1, text="縦:")
        m2_entry = ttk.Entry(frame1, textvariable=m2_name, width=8)
        mc2_label = ttk.Label(frame1, text="cm")

        m2_label.grid(row=13, column=1, sticky=W, padx=150)
        m2_entry.grid(row=13, column=1, sticky=W, padx=185)
        mc2_label.grid(row=13, column=1, sticky=W, padx=240)

        m3_label = ttk.Label(frame1, text="マチ:")
        m3_entry = ttk.Entry(frame1, textvariable=m3_name, width=8)
        mc3_label = ttk.Label(frame1, text="cm")

        m3_label.grid(row=14, column=1, sticky=W)
        m3_entry.grid(row=14, column=1, sticky=W, padx=35)
        mc3_label.grid(row=14, column=1, sticky=W, padx=90)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value != "その他":
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        m1_name.trace_add('write', add_to_input2)
        m2_name.trace_add('write', add_to_input2)
        m3_name.trace_add('write', add_to_input2)
        grb_val.trace_add('write', update_t_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, m_label, m1_label, m1_entry, mc1_label, m2_label, m2_entry, mc2_label, m3_label, m3_entry, mc3_label])

    elif genre == '腕時計':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        m_label = ttk.Label(frame1, text="実寸サイズ")
        m_label.grid(row=13, column=0)

        m1_label = ttk.Label(frame1, text="ケース縦:")
        m1_entry = ttk.Entry(frame1, textvariable=m1_name, width=8)
        mc1_label = ttk.Label(frame1, text="cm")

        m1_label.grid(row=13, column=1, sticky=W)
        m1_entry.grid(row=13, column=1, sticky=W, padx=50)
        mc1_label.grid(row=13, column=1, sticky=W, padx=120)

        m2_label = ttk.Label(frame1, text="ケース横:")
        m2_entry = ttk.Entry(frame1, textvariable=m2_name, width=8)
        mc2_label = ttk.Label(frame1, text="cm")

        m2_label.grid(row=13, column=1, sticky=W, padx=170)
        m2_entry.grid(row=13, column=1, sticky=W, padx=225)
        mc2_label.grid(row=13, column=1, sticky=W, padx=290)

        m3_label = ttk.Label(frame1, text="ベルト幅:")
        m3_entry = ttk.Entry(frame1, textvariable=m3_name, width=8)
        mc3_label = ttk.Label(frame1, text="cm")

        m3_label.grid(row=14, column=1, sticky=W)
        m3_entry.grid(row=14, column=1, sticky=W, padx=50)
        mc3_label.grid(row=14, column=1, sticky=W, padx=120)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value != "その他":
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        m1_name.trace_add('write', add_to_input2)
        m2_name.trace_add('write', add_to_input2)
        m3_name.trace_add('write', add_to_input2)
        grb_val.trace_add('write', update_t_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, m_label, m1_label, m1_entry, mc1_label, m2_label, m2_entry, mc2_label, m3_label, m3_entry, mc3_label])

    elif genre == 'その他':
        n_label = ttk.Label(frame1, text="表記サイズ", padding=(10))
        n_label.grid(row=12, column=0)

        n_entry = ttk.Entry(frame1, textvariable=n_name, width=10)
        n_entry.grid(row=12, column=1, sticky=W)

        motion_label = ttk.Label(frame1, text="動作確認", padding=(10))
        motion_label.grid(row=13, column=0)

        motion_val = StringVar()
        motion = ['','通電未確認','動作未確認', '簡易通電確認済み', '通電確認済み', '簡易動作確認済み', '動作確認済み']
        motion_val.set(motion[0])
        motion_cb = ttk.Combobox(frame1, state='readonly', textvariable=motion_val, values=motion, width=17)
        motion_cb.grid(row=13, column=1, sticky=W)

        def add_to_input2(*args):
            input2.clear()
            if n_name.get() == "":
                n_name.get() == "-"
            input2.append(n_name.get())
            if genre_val.get() == 'トップス':
                input2.append(f"着丈:{m1_name.get()}cm<BR>\n肩幅:{m2_name.get()}cm<BR>\n身幅:{m3_name.get()}cm<BR>\n袖丈:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'ボトムス':
                input2.append(f"ウエスト:{m1_name.get()}cm<BR>\n股上:{m2_name.get()}cm<BR>\n股下:{m3_name.get()}cm<BR>\n裾幅:{m4_name.get()}cm<BR>")
            elif genre_val.get() == 'シューズ':
                input2.append(f"アウトソール:{m1_name.get()}cm<BR>\n幅:{m2_name.get()}cm<BR>")
            elif genre_val.get() == 'バッグ':
                input2.append(f"横:{m1_name.get()}cm<BR>\n縦:{m2_name.get()}cm<BR>\nマチ:{m3_name.get()}cm<BR>")
            elif genre_val.get() == '腕時計':
                input2.append(f"ケース縦:{m1_name.get()}cm<BR>\nケース縦:{m2_name.get()}cm<BR>\nベルト幅:{m3_name.get()}cm<BR>")
            elif genre_val.get() == 'その他':
                input2.append("-")
            input2.append(m1_name.get())
            input2.append(m2_name.get())
            input2.append(m3_name.get())
            input2.append(m4_name.get())
            if genre_val.get() == 'その他':
                input2.append(motion_val.get())
            else:
                input2.append("")
        add_to_input2()

        def update_s_text(*args):
            selected_value = situation_val.get()
            ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
            motion_value = motion_val.get()
            if ss_text_value != "":
                ss_text_value = "と" + ss_text_value
            if motion_value == "":
                s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")
            else:
                s_text_val.set(motion_value + "です。少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")

        def update_t_text(*args):
            brand_name_value = brand_name.get()
            brand_kana_value = brand_kana.get()
            item_name_value = item_name.get()
            n_name_value = n_name.get()
            color_name_value = color_name.get()
            genre_value = genre_val.get()
            situation_value = situation_val.get()
            if genre_value == "選択してください":
                genre_value = ""
            inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
            c_inputtext = ""
            if n_name_value != "":
                c_inputtext += " サイズ" + n_name_value
            if color_name_value != "":
                c_inputtext += " " + color_name_value
            if situation_value != "中古品":
                c_inputtext += " " + situation_value
            if genre_value == "その他":
                motion_value = motion_val.get()
                if motion_value != "":
                    c_inputtext += " " + motion_value
            else:
                c_inputtext += " " + genre_value
            if genre_value == "トップス" or genre_value == "ボトムス":
                grb_value = grb_val.get()
                c_inputtext +=" " + grb_value
            t_text_val.set(inputtext + c_inputtext)
        update_s_text()
        update_t_text()
        n_name.trace_add('write', add_to_input2)
        situation_val.trace_add('write', update_s_text)
        situation_val.trace_add('write', update_t_text)
        motion_val.trace_add('write', add_to_input2)
        motion_val.trace_add('write', update_t_text)
        motion_val.trace_add('write', update_s_text)
        n_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        ss_text_val.trace_add('write', update_s_text)
        brand_name.trace_add('write', update_t_text)
        brand_kana.trace_add('write', update_t_text)
        item_name.trace_add('write', update_t_text)
        color_name.trace_add('write', update_t_text)
        grb_val.trace_add('write', update_t_text)
        genre_val.trace_add('write', update_t_text)
        widgets.extend([n_label, n_entry, motion_label, motion_cb])

def delete_current_item():
    global current_idx, idx_s
    if current_idx > 0:
        if current_idx <= len(item_data):
            del item_data[current_idx - 1]
        current_idx = max(1, current_idx - 1)
        if current_idx <= len(item_data):
            show_data(current_idx)
            idx_s -= 1
        else:
            clear_input_fields()

        update_current_label()
    else:
        error_label = ttk.Label(frame1, text="削除するデータが存在しません", foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
        error_log.extend([error_label])


def next_button_action():
    global current_idx, idx_s
    if current_idx > 0:
        item_info = [
            shop_val.get(), brand_name.get(), brand_kana.get(), item_name.get(),
            color_name.get(), price_name.get(), grb_val.get(), genre_val.get(),
            situation_val.get(), rank_val.get(), rank2_val.get(), ss_text_val.get(), s_text_val.get(),postage_val.get()
        ]
        item_info.extend(input2)
        if current_idx <= len(item_data):
            item_data[current_idx - 1] = item_info
        else:
            item_data.append(item_info)
    current_idx += 1
    if current_idx <= len(item_data):
        show_data(current_idx)
    else:
        idx_s += 1
        clear_input_fields()

    update_current_label()
    # GUIの外でデータを出力
    print("Item data:")
    for idx, data_list in enumerate(item_data, start=1):
        print(f"Item {idx}: {data_list}")

def show_data(idx):
    if idx < 1 or idx > len(item_data):
        return
    item_info = item_data[idx - 1]
    shop_val.set(item_info[0])
    brand_name.set(item_info[1])
    brand_kana.set(item_info[2])
    item_name.set(item_info[3])
    color_name.set(item_info[4])
    price_name.set(item_info[5])
    grb_val.set(item_info[6])
    genre_val.set(item_info[7])
    situation_val.set(item_info[8])
    rank_val.set(item_info[9])
    rank2_val.set(item_info[10])
    ss_text_val.set(item_info[11])
    postage_val.set(item_info[13])
    n_name.set(item_info[14])
    m1_name.set(item_info[16])
    m2_name.set(item_info[17])
    m3_name.set(item_info[18])
    m4_name.set(item_info[19])
    measure(frame1, None, genre_val, input2, n_name, m1_name, m2_name, m3_name, m4_name)
    s_text_val.set(item_info[12])

def update_current_label():
    global current_label, current_idx, all_idx
    all_idx = str(current_idx) + "/" + str(idx_s)
    if current_label:
        current_label.config(text=all_idx)

def yahoo_auction():
    geckodriver_path = os.path.join(base_path, 'geckodriver.exe')

    # Firefoxのオプションを設定
    firefox_options = Options()
    firefox_options.headless = False  # ヘッドレスモードをオフにして実行

    # Firefoxプロファイルのパス
    firefox_profile_path = firefox_profile_path_var.get().strip()
    if not firefox_profile_path or not os.path.isdir(firefox_profile_path):
        messagebox.showerror("エラー", "有効なFirefoxプロファイルフォルダを選択してください。")
        return

    # Firefoxのプロファイルを設定
    firefox_options.profile = firefox_profile_path

    # Firefoxのバイナリファイルのパスを指定する
    firefox_binary_path = r'C:\Program Files\Mozilla Firefox\firefox.exe'  # あなたの環境に合わせて変更してください

    # Firefoxのバイナリをオプションに追加
    firefox_options.binary = firefox_binary_path



    # WebDriverインスタンスを作成
    driver = webdriver.Firefox(options=firefox_options, service=Service(geckodriver_path))
    driver.maximize_window()
    driver.get("https://pro.store.yahoo.co.jp/pro.medamaya")
    time.sleep(50)
    #firefox_options.headless = True
    #driver = webdriver.Firefox(options=firefox_options, service=Service(geckodriver_path))
    for idx, item_info in enumerate(item_data, start=1):
        time.sleep(5)
        if item_data[idx-1][0] == "上池袋":
            a15 = "上池袋店 XXX"
            a0 = 22
            a145 = "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/rannku.jpg><IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
            a17 = "豊島区"
            driver.get("https://auctions.store.yahoo.co.jp/serinavi/items/create?action=create&folder_id=1308997")
        elif item_data[idx-1][0] == "要町":
            a0 = 11
            a15 = "要町店 XXX"
            a145 = "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/rannku.jpg><IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
            a17 = "豊島区"
            driver.get("https://auctions.store.yahoo.co.jp/serinavi/items/create?action=create&folder_id=1308972")
        elif item_data[idx-1][0] == "中野":
            a0 = 44
            a15 = "中野店 XXX"
            a145 = "<IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/ranku.jpg><BR><IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/nakanochizu3.jpg><IMG SRC=https://shopping.c.yimg.jp/lib/medamaya/cyuigakii2.jpg>"
            a17 = "中野区"
            driver.get("https://auctions.store.yahoo.co.jp/serinavi/items/create?action=create&folder_id=1309032")
        if item_data[idx-1][7] == "その他":
            item_data[idx-1][7] = ""
        a1 = int(str(a0) + str(year % 100) + str(month) + str(day) + str(idx).zfill(3))
        a2 = item_data[idx-1][1] + " " + item_data[idx-1][2] + " " + item_data[idx-1][3]
        if item_data[idx-1][14] != "":
            a2 += " サイズ " + item_data[idx-1][14]
        if item_data[idx-1][4] != "":
            a2 += " " + item_data[idx-1][4]
        else:
            item_data[idx-1][4] = "-"
        if item_data[idx-1][8] != "中古品":
            a2 += " " + item_data[idx-1][8]
        if item_data[idx-1][7] == "トップス" or item_data[idx-1][7] == "ボトムス":
            if item_data[idx-1][6] != "記入無し":
                a2 += " " + item_data[idx-1][6]
        a2 += " " + item_data[idx-1][7]

        a3 = "<TABLE BORDER=1 WIDTH=700px CELLSPACING=4 CELLPADDING=10 BORDER=1> </TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>ランク付け</TD> <TD WIDTH=75%>\n"
        a4 = item_data[idx-1][9]
        a5 = "\n</TD></TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>状態</TD> <TD WIDTH=75%>\n"
        a6 = item_data[idx-1][1] + " " + item_data[idx-1][3] + "です。<BR>\n"
        a7 = item_data[idx-1][12] + "<BR>\n"
        a8 = "<TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>表記サイズ</TD> <TD WIDTH=75%>\n"
        a9 = item_data[idx-1][14]
        if item_data[idx-1][14] == "":
            a9 = "-"
        a10 = "\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>実寸サイズ</TD> <TD WIDTH=75%>\n"
        a11 = item_data[idx-1][15]
        a12 = "\n</TD> </TR><TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>カラー</TD> <TD WIDTH=75%>\n"
        a13 = item_data[idx-1][4]
        a14 ="\n</TD> </TR> <TR> <TD BGCOLOR=#A9A9A9 WIDTH=25%>保管店舗</TD> <TD WIDTH=75%>" + item_data[idx-1][0] + "</TD> </TR>  </TABLE>"
        #a16だけ店ごとに変える
        #ストア内検索ワード
        #状態
        #消費税
        a16 = item_data[idx-1][5]
        #開催期間　7日間　午前10時から午後11時
        #自動延長設定
        #自動再出品　下げない
        #発送元　東京都　豊島区　中野区
        #送料負担落札者
        #配送グループデフォルトor2000円
        #発送までの日数1~3
        #保存先のフォルダ
        print(a1)
        print(a2)
        print(a3)
        print(a4)
        print(a5)
        print(a6)
        print(a7)
        print(a8)
        print(a9)
        print(a10)
        print(a11)
        print(a12)
        print(a13)
        print(a14)
        print(a15)
        print(a16)
        print(item_data[idx-1][10])
        #上池袋ver
        #管理番号
        time.sleep(5)
        element2 = driver.find_element(By.NAME, "businessCommodityIdInputText")
        element2.send_keys(a1)

        #タイトル
        # element3: name属性が "titleInputText" の要素を見つけて値を送信する
        element3 = driver.find_element(By.NAME, "titleInputText")
        element3.send_keys(a2)

        #カテゴリ
        2084207680
        element13 = driver.find_element(By.NAME, "categoryIdInputText")
        element13.send_keys(2084207680)
        #category_buttons = driver.find_elements(By.CSS_SELECTOR, '.sc-3d23ca91-0.bEjzRJ')
        #category_button = category_buttons[0]
        #driver.execute_script("arguments[0].click();", category_button)
        #category_buttons2 = driver.find_elements(By.CSS_SELECTOR, '.sc-d15216b7-3.fVLesw')
        #category_button2 = category_buttons2[0]
        #driver.execute_script("arguments[0].click();", category_button2)
        #element13 = driver.find_element(By.NAME, "searchCategoryKeywordInput")
        #element13.send_keys(a2)
        #kettei_buttons = driver.find_elements(By.CSS_SELECTOR, '.sc-3d23ca91-0.coWOHr')
        #kettei_button = kettei_buttons[1]
        #driver.execute_script("arguments[0].click();", kettei_button)
        #categories1 = driver.find_elements(By.CSS_SELECTOR, '.sc-39752b9c-1.jMmxar')
        #for index, category1 in enumerate(categories1):
        #    print(f"Radio Button {index}: {category1.get_attribute('outerHTML')}")
        #category1 = categories1[0]
        #driver.execute_script("arguments[0].click();", category1)
        #kettei_buttons2 = driver.find_elements(By.CSS_SELECTOR, '.sc-3d23ca91-0.coWOHr')
        #kettei_button2 = kettei_buttons2[1]
        #driver.execute_script("arguments[0].click();", kettei_button2)
        #htmlに切り替え
        # element4: name属性が "html_tag" の要素を見つけてクリックする
        element4 = driver.find_element(By.NAME, "html_tag")
        element4.click()

        #HTML入力
        # element5: name属性が "Description_plain" の要素を見つけて値を送信する
        element5 = driver.find_element(By.NAME, "Description_plain")
        element5.send_keys(a3 + a4 + a5 + a6 + a7 + a8 + a9 + a10 + a11 + a12 + a13 + a14 + a145)
        #ストア内商品検索キーワード
        element12 = driver.find_element(By.NAME, "storeKeywordInputText")
        element12.send_keys(a15)


        radio_buttons = driver.find_elements(By.CSS_SELECTOR, '.sc-96b820b5-2.cwZSya')
        for index, radio_button in enumerate(radio_buttons):
            print(f"Radio Button {index}: {radio_button.get_attribute('outerHTML')}")

        # element6: 商品の状態を表す要素を選択する（例えばXPathを使って）
        if item_data[idx-1][10] == "未使用品":
            radio_button = radio_buttons[0]
            driver.execute_script("arguments[0].click();", radio_button)
        elif item_data[idx-1][10] == "未使用品に近い":
            radio_button = radio_buttons[1]
            driver.execute_script("arguments[0].click();", radio_button)
        elif item_data[idx-1][10] == "目立った傷や汚れなし":
            radio_button = radio_buttons[2]
            driver.execute_script("arguments[0].click();", radio_button)
        elif item_data[idx-1][10] == "やや傷や汚れあり":
            radio_button = radio_buttons[3]
            driver.execute_script("arguments[0].click();", radio_button)
        elif item_data[idx-1][10] == "傷や汚れあり":
            radio_button = radio_buttons[4]
            driver.execute_script("arguments[0].click();", radio_button)
        elif item_data[idx-1][10] == "全体的に状態が悪い":
            radio_button = radio_buttons[5]
            driver.execute_script("arguments[0].click();", radio_button)

        #消費税
        # element7: 商品のカテゴリを表す要素を選択する（例えばXPathを使って）
        element7 = radio_buttons[8]
        driver.execute_script("arguments[0].click();", element7)
        time.sleep(1)
        #値段
        # element8: name属性が "startPriceInputText" の要素を見つけて値を送信する
        element8 = driver.find_element(By.NAME, "startPriceInputText")
        element8.send_keys(a16)
        #開催期間
        # combo_box1: name属性が "durationSelect" のコンボボックスを選択する
        combo_box1 = driver.find_element(By.NAME, "durationSelect")
        select1 = Select(combo_box1)
        select1.select_by_value("7")

        #開催時間
        # combo_box2: name属性が "durationSelect" のコンボボックスを選択する（別の方法）
        combo_box2 = driver.find_element(By.NAME, "endTimeSelect")
        select2 = Select(combo_box2)
        select2.select_by_value("22")
        #自動延長チェックボックス
        # element9: class名が "sc-e13d78e9-2 fJfvZC" の要素をクリックする
        select_box = driver.find_elements(By.CSS_SELECTOR, '.sc-e13d78e9-2.fJfvZC')
        element9 = select_box[1]
        driver.execute_script("arguments[0].click();", element9)

        #自動再出品回数
        # combo_box3: name属性が "numResubmitSelect" のコンボボックスを選択する
        combo_box3 = driver.find_element(By.NAME, "numResubmitSelect")
        select3 = Select(combo_box3)
        select3.select_by_value("3")

        time.sleep(1)

        #価格を下げない
        # combo_box4: name属性が "changePriceRatioResubmitSelect" のコンボボックスを選択する
        combo_box4 = driver.find_element(By.NAME, "changePriceRatioResubmitSelect")
        select4 = Select(combo_box4)
        select4.select_by_value("0")

        #配送元地域
        # combo_box5: name属性が "prefectureCodeSelect" のコンボボックスを選択する
        combo_box5 = driver.find_element(By.NAME, "prefectureCodeSelect")
        select5 = Select(combo_box5)
        select5.select_by_value("13")

        #区
        # element10: name属性が "cityNameInputText" の要素を見つけて値を送信する
        element10 = driver.find_element(By.NAME, "cityNameInputText")
        element10.send_keys(a17)

        #配送グループ
        # combo_box6: name属性が "deliveryGroupSelect" のコンボボックスを選択する
        combo_box6 = driver.find_element(By.NAME, "deliveryGroupSelect")
        select6 = Select(combo_box6)
        if item_data[idx-1][13] == "700":
            select6.select_by_value("1")
        elif item_data[idx-1][13] == "2000":
            select6.select_by_value("2")

        #発送までの日数
        # combo_box7: name属性が "prefectureCodeSelect" のコンボボックスを選択する（別の例）
        combo_box7 = driver.find_element(By.NAME, "leadTimeSelect")
        select7 = Select(combo_box7)
        select7.select_by_value("1")
        #
        # element11: class名が "sc-3d23ca91-0 eIJvRX" の要素をクリックする
        element11 = driver.find_element(By.CSS_SELECTOR, ".sc-3d23ca91-0.eIJvRX")
        driver.execute_script("arguments[0].click();", element11)


def calc(filepath, item_data_list):
    # Calcファイルを読み込む
    doc = ezodf.opendoc(filepath)

    # 書き込み開始シート（テンプレート開始位置）
    base_sheet_index = 0
    items_per_sheet = 20
    required_sheet_count = (len(item_data_list) - 1) // items_per_sheet + 1 if item_data_list else 1

    if base_sheet_index + required_sheet_count > len(doc.sheets):
        messagebox.showerror("エラー", f"値札出力に必要なシート数が不足しています。必要: {required_sheet_count} / 利用可能: {len(doc.sheets) - base_sheet_index}")
        return

    # 商品ごとにデータを書き込む
    for global_idx, item_info in enumerate(item_data_list, start=1):
        sheet_offset = (global_idx - 1) // items_per_sheet
        idx_in_sheet = ((global_idx - 1) % items_per_sheet) + 1
        sheet = doc.sheets[base_sheet_index + sheet_offset]

        if shop_val.get() == "上池袋":
            s_num = 22
        elif shop_val.get() == "要町":
            s_num = 11
        elif shop_val.get() == "中野":
            s_num = 44

        c_item_info = ""

        if item_info[14] != "":
            c_item_info += "サイズ" + item_info[14]
        if item_info[11] != "":
            situation = re.sub(r'[ 　、]+', '/', item_info[11])
            c_item_info += "/" + situation
        if item_info[20] != "":
            c_item_info += "/" + item_info[20]
        if item_info[6] == "レディース":
            c_item_info += "/" + item_info[6]
        c_item_info += "/" + item_info[8] + "/オーク"

        c_num = int(str(s_num) + str(year % 100) + str(month) + str(day) + str(global_idx).zfill(3))
        c_price = int(item_info[5])
        c_item_name = re.sub(r'[ 　、]+', '/', item_info[3])

        if idx_in_sheet >= 16:
            sheet[(idx_in_sheet - 16) * 7, 9].set_value(item_info[1])
            sheet[1 + (idx_in_sheet - 16) * 7, 9].set_value(c_num)
            sheet[2 + (idx_in_sheet - 16) * 7, 9].set_value(c_price)
            sheet[2 + (idx_in_sheet - 16) * 7, 10].set_value(item_info[9])
            sheet[4 + (idx_in_sheet - 16) * 7, 9].set_value(c_item_name)
            sheet[5 + (idx_in_sheet - 16) * 7, 9].set_value(c_item_info)
        elif idx_in_sheet >= 11:
            sheet[(idx_in_sheet - 11) * 7, 6].set_value(item_info[1])
            sheet[1 + (idx_in_sheet - 11) * 7, 6].set_value(c_num)
            sheet[2 + (idx_in_sheet - 11) * 7, 6].set_value(c_price)
            sheet[2 + (idx_in_sheet - 11) * 7, 7].set_value(item_info[9])
            sheet[4 + (idx_in_sheet - 11) * 7, 6].set_value(c_item_name)
            sheet[5 + (idx_in_sheet - 11) * 7, 6].set_value(c_item_info)
        elif idx_in_sheet >= 6:
            sheet[(idx_in_sheet - 6) * 7, 3].set_value(item_info[1])
            sheet[1 + (idx_in_sheet - 6) * 7, 3].set_value(c_num)
            sheet[2 + (idx_in_sheet - 6) * 7, 3].set_value(c_price)
            sheet[2 + (idx_in_sheet - 6) * 7, 4].set_value(item_info[9])
            sheet[4 + (idx_in_sheet - 6) * 7, 3].set_value(c_item_name)
            sheet[5 + (idx_in_sheet - 6) * 7, 3].set_value(c_item_info)
        else:
            sheet[(idx_in_sheet - 1) * 7, 0].set_value(item_info[1])
            sheet[1 + (idx_in_sheet - 1) * 7, 0].set_value(c_num)
            sheet[2 + (idx_in_sheet - 1) * 7, 0].set_value(c_price)
            sheet[2 + (idx_in_sheet - 1) * 7, 1].set_value(item_info[9])
            sheet[4 + (idx_in_sheet - 1) * 7, 0].set_value(c_item_name)
            sheet[5 + (idx_in_sheet - 1) * 7, 0].set_value(c_item_info)

    # 変更を保存する

    doc.save()

    # 変更したファイルをLibreOffice Calcで開く
    os.startfile(filepath)

def prev_button_action():
    global current_idx
    if current_idx == 1:
        error_label=ttk.Label(frame1, text="前のデータは存在しません",foreground='#ff0000')
        error_label.grid(row=1, column=1, sticky=W)
    else:
        price_error = price_name.get()
        if price_error == "" or price_error.isdigit() == False:
            price_name.set("0")
        if genre_val.get() == "選択してください":
            genre_val.set(genre[5])

        if current_idx > 1:
            item_info = [
                shop_val.get(), brand_name.get(), brand_kana.get(), item_name.get(),
                color_name.get(), price_name.get(), grb_val.get(), genre_val.get(),
                situation_val.get(), rank_val.get(), rank2_val.get(), ss_text_val.get(), s_text_val.get(), postage_val.get()
            ]
            item_info.extend(input2)
            while len(item_info) < 21:
                item_info.append("")
            if current_idx <= len(item_data):
                item_data[current_idx - 1] = item_info  # item_dataの該当するインデックスにitem_infoを代入
            else:
                item_data.append(item_info)  # item_dataの末尾にitem_infoを追加
            current_idx -= 1
            show_data(current_idx)
            update_current_label()

def clear_input_fields():
    global widgets
    brand_name.set("")
    brand_kana.set("")
    item_name.set("")
    color_name.set("")
    price_name.set("")
    grb_val.set("")
    genre_val.set("選択してください")
    situation_val.set(situation[5])
    rank_val.set(rank[4])
    rank2_val.set(rank2[2])
    ss_text_val.set("")
    t_text_val.set("")
    postage_val.set(postage[0])
    n_name.set("")
    m1_name.set("")
    m2_name.set("")
    m3_name.set("")
    m4_name.set("")
    motion_val.set("")
    for widget in widgets:
        if isinstance(widget, ttk.Entry):
            widget.destroy()
        if isinstance(widget, ttk.Combobox):
            widget.destroy()
        if isinstance(widget, ttk.Label):
            widget.destroy()
        elif isinstance(widget, StringVar):
            widget.set("")
    widgets = []

def update_s_text(*args):
    selected_value = situation_val.get()
    ss_text_value = re.sub(r'[ \u3000]+', '、', ss_text_val.get())
    if ss_text_value != "":
        ss_text_value = "と" + ss_text_value
    #motion_value = motion_val.get()
    #s_text_val.set(selected_value + "。通常の使用に伴う状態。" + ss_text_value)
    s_text_val.set("少々使用感" + ss_text_value + "はありますが、大きなダメージはなく中古並の状態です。")
def update_t_text(*args):
    brand_name_value = brand_name.get()
    brand_kana_value = brand_kana.get()
    item_name_value = item_name.get()
    n_name_value = n_name.get()
    color_name_value = color_name.get()
    motion_value = motion_val.get()
    genre_value = genre_val.get()
    situation_value = situation_val.get()

    if genre_value == "選択してください":
        genre_value = ""
    inputtext = brand_name_value + " " + brand_kana_value + " " + item_name_value
    c_inputtext = ""
    if n_name_value != "":
        c_inputtext += " サイズ" + n_name_value
    if color_name_value != "":
        c_inputtext += " " + color_name_value
    if motion_value != "":
        c_inputtext += " " + motion_value
    if situation_value != "中古品":
        c_inputtext += " " + situation_value
    if genre_value != "その他":
        c_inputtext += " " + genre_value
    if genre_value == "トップス" or genre_value == "ボトムス":
        grb_value = grb_val.get()
        c_inputtext +=" " + grb_value
    t_text_val.set(inputtext + c_inputtext)

def count_text_length(text):
    length = 0
    for char in text:
        if ord(char) > 255:
            length += 1  # 全角文字は1としてカウント
        else:
            length += 0.5  # 半角文字は0.5としてカウント
    return length

def update_count(*args):
    text = t_text_val.get()
    length = count_text_length(text)
    count_label.config(text=f"文字数: {length:.1f}/65")


def on_closing():
    if messagebox.askokcancel("確認", "アプリケーションを閉じますか？入力されたデータは失われます。"):
        save_settings()
        root.destroy()  # ウィンドウを閉じる

# メイン
current_idx = 1
item_data = []
error_log = []
idx = 1
idx_s = 1
i = 1
all_idx = str(current_idx) + "/" + str(idx_s)
filename = 'ネット用値札.ods'
filepath = os.path.join(base_path, filename)
input_data = []
year, month, day = Datetime()
date = Date(year, month, day)
p_date = P_date(year, month, day)
widgets = []

input2 = []
root = Tk()
root.title("EC_Bridge")
frame1 = ttk.Frame(root)
n_name = StringVar(value="")
m1_name = StringVar(value="")
m2_name = StringVar(value="")
m3_name = StringVar(value="")
m4_name = StringVar(value="")
genre_val = StringVar(value="")
motion = ['','ジャンク','通電未確認','動作未確認', '簡易通電確認済み', '通電確認済み', '簡易動作確認済み', '動作確認済み']
motion_val =StringVar(value="")
situation_val = StringVar(value="")
today = ttk.Label(frame1, text=p_date, font=("Helvetica", 16), padding=(10))
shop_label = ttk.Label(frame1, text="取扱店舗", padding=(10))


# 取扱店舗コンボボックス
shop_val = StringVar()
shop = ['上池袋', '要町', '中野']
default_settings = load_settings()
shop_val.set(default_settings.get('last_shop', shop[0]))
if shop_val.get() not in shop:
    shop_val.set(shop[0])
shop_cb = ttk.Combobox(frame1, state='readonly', textvariable=shop_val, values=shop)

firefox_profile_label = ttk.Label(frame1, text="Firefoxプロファイル", padding=(10))
firefox_profile_path_var = StringVar(value=default_settings.get('firefox_profile_path', r'C:\Users\user\AppData\Roaming\Mozilla\Firefox\Profiles\ifhijbkj.default'))
firefox_profile_entry = ttk.Entry(frame1, textvariable=firefox_profile_path_var, width=60)
firefox_profile_button = ttk.Button(frame1, text="参照", command=browse_firefox_profile)

brand_name_label = ttk.Label(frame1, text="商品ブランド(メーカー)", padding=(10))
brand_name = StringVar()
brand_name_entry = ttk.Entry(frame1, textvariable=brand_name, width=40)

brand_kana_label = ttk.Label(frame1, text="カタカナ")
brand_kana = StringVar()
brand_kana_entry = ttk.Entry(frame1, textvariable=brand_kana, width=40)

item_name_label = ttk.Label(frame1, text="商品名(値札1行目)", padding=(10))
item_name = StringVar()
item_name_entry = ttk.Entry(frame1, textvariable=item_name, width=40)


color_label = ttk.Label(frame1, text="カラー", padding=(10))
color_name = StringVar()
color_entry = ttk.Entry(frame1, textvariable=color_name, width=20)


te_label = ttk.Label(frame1, text="ネット出品タイトル", padding=(10))
t_text_val = StringVar()
update_t_text()  # 初期化
t_text_label = ttk.Entry(frame1, textvariable=t_text_val, width=90)
t_text_label.config(state='readonly')
count_label = tk.Label(frame1, text="文字数: 0.0/65")
t_text_val.trace_add('write', update_count)

price_label = ttk.Label(frame1, text="値段", padding=(10))
price_name = StringVar()
price_entry = ttk.Entry(frame1, textvariable=price_name, width=10)
price2_label = ttk.Label(frame1, text="円")


gender_label = ttk.Label(frame1, text="性別", padding=(10))
gender = ["記入無し", "メンズ", "レディース"]
grb_val = StringVar()
grb1 = ttk.Radiobutton(frame1, text=gender[0], value="", variable=grb_val, padding=(10))
grb2 = ttk.Radiobutton(frame1, text=gender[1], value=gender[1], variable=grb_val, padding=(10))
grb3 = ttk.Radiobutton(frame1, text=gender[2], value=gender[2], variable=grb_val, padding=(10))
grb1.bind('<Return>', select_focused_radiobutton)
grb2.bind('<Return>', select_focused_radiobutton)
grb3.bind('<Return>', select_focused_radiobutton)


genre_label = ttk.Label(frame1, text="商品ジャンル", padding=(10))
# ジャンルコンボボックス
genre_val = StringVar()
genre = ['トップス', 'ボトムス', 'シューズ', 'バッグ', '腕時計', 'その他']
genre_val.set("選択してください")
genre_cb = ttk.Combobox(frame1, state='readonly', textvariable=genre_val, values=genre, width=13)
# ジャンルコンボボックスで選択が変更されたときに measure() 関数を呼び出す
genre_cb.bind("<<ComboboxSelected>>", lambda event: measure(frame1, event, genre_val, input2,n_name,m1_name,m2_name,m3_name,m4_name))
genre_cb.bind('<Return>', open_combobox)
genre_cb.bind('<Down>', disable_dropdown)

situation_label = ttk.Label(frame1, text="商品状態", padding=(10))

# 状態コンボボックス
situation_val = StringVar()
situation = ['未使用品','未使用保管品','未使用タグ付き品','未使用箱付き品', '美中古品', '中古品', '現状品', '稼働品','ジャンク品','箱付き','ケース付き']
situation_val.set(situation[5])
situation_cb = ttk.Combobox(frame1, state='readonly', textvariable=situation_val, values=situation, width=15)
situation_cb.bind('<Return>', open_combobox)
situation_cb.bind('<Down>', disable_dropdown)


# ランクコンボボックス
rank_val = StringVar()
rank = ['A', 'AB', 'B', 'BC', 'C', 'CD', 'D', 'DE', 'E']
rank_val.set(rank[4])
rank_cb = ttk.Combobox(frame1, state='readonly', textvariable=rank_val, values=rank, width=5)
rank_cb.bind('<Return>', open_combobox)
rank_cb.bind('<Down>', disable_dropdown)

rank2_val = StringVar()
rank2 = ['未使用品', '未使用品に近い', '目立った傷や汚れなし', 'やや傷や汚れあり', '傷や汚れあり', '全体的に状態が悪い']
rank2_val.set(rank2[2])
rank2_cb = ttk.Combobox(frame1, state='readonly', textvariable=rank2_val, values=rank2, width=18)
rank2_cb.bind('<Return>', open_combobox)
rank2_cb.bind('<Down>', disable_dropdown)

ss_text_val = StringVar()
ss_text_entry = ttk.Entry(frame1, textvariable=ss_text_val, width=10)

ss_text_label = ttk.Label(frame1, text="←値札用状態 \n例:使用感、黄ばみ")

# 状態説明文
s_text_val = StringVar()
update_s_text()  # 初期化
s_text_entry = ttk.Entry(frame1, textvariable=s_text_val, width=90)
ss_text_val.trace_add('write', update_s_text)
situation_val.trace_add('write', update_s_text)
#s_text_val.trace_add('write', update_s_text)これ変えちゃだめ

postage_label = ttk.Label(frame1, text="送料", padding=(10))
postage = ["700", "2000"]
postage_val = StringVar()
postage_val.set(postage[0])
pos1 = ttk.Radiobutton(frame1, text=postage[0], value=postage[0], variable=postage_val, padding=(10))
pos2 = ttk.Radiobutton(frame1, text=postage[1], value=postage[1], variable=postage_val, padding=(10))
pos1.bind('<Return>', select_focused_radiobutton)
pos2.bind('<Return>', select_focused_radiobutton)

prev_button = ttk.Button(frame1, text="前へ", command=prev_button_action)
next_button = ttk.Button(frame1, text="次へ", command=button1)


calc_button = ttk.Button(frame1, text="値札出力", command=button2)

current_label_label = ttk.Label(frame1, text="商品番号", padding=(10))
print(all_idx)
current_label = ttk.Label(frame1, text=all_idx, padding=(10))



auc_button = ttk.Button(frame1, text="出品", command=button3)
delete_button = ttk.Button(frame1, text="削除", command=delete_current_item)

# 各入力フィールドでタイトルを更新するように変更
brand_name.trace_add('write', update_t_text)
brand_kana.trace_add('write', update_t_text)
item_name.trace_add('write', update_t_text)
n_name.trace_add('write', update_t_text)
color_name.trace_add('write', update_t_text)
grb_val.trace_add('write', update_t_text)
genre_val.trace_add('write', update_t_text)
motion_val.trace_add('write', update_t_text)
#situation_val.trace_add('write', update_t_text)つけると動かない

today.grid(row=0, column=1, sticky=W)
current_label_label.grid(row=2, column=0)
current_label.grid(row=2, column=1,sticky=W)
shop_label.grid(row=3, column=0)
shop_cb.grid(row=3, column=1, sticky=W)
firefox_profile_label.grid(row=4, column=0)
firefox_profile_entry.grid(row=4, column=1, sticky=W)
firefox_profile_button.grid(row=4, column=1, sticky=W, padx=620)
brand_name_label.grid(row=5, column=0)
brand_name_entry.grid(row=5, column=1, sticky=W)
brand_kana_label.grid(row=6, column=0)
brand_kana_entry.grid(row=6, column=1, sticky=W)
item_name_label.grid(row=7, column=0)
item_name_entry.grid(row=7, column=1, sticky=W)
color_label.grid(row=8, column=0)
color_entry.grid(row=8, column=1, sticky=W)
te_label.grid(row=9, column=0)
t_text_label.grid(row=9, column=1,sticky=W)
count_label.grid(row=9, column=1, sticky=W, padx=600,)
price_label.grid(row=10, column=0)
price_entry.grid(row=10, column=1, sticky=W)
price2_label.grid(row=10, column=1, sticky=W, padx=80)
gender_label.grid(row=11, column=0)
grb1.grid(row=11, column=1, sticky=W)
grb2.grid(row=11, column=1, sticky=W,padx=100)
grb3.grid(row=11, column=1, sticky=W,padx=200)

genre_label.grid(row=12, column=0)
genre_cb.grid(row=12, column=1, sticky=W)

situation_label.grid(row=16, column=0)
situation_cb.grid(row=16,column=1, sticky=W)
rank_cb.grid(row=16,column=1, sticky=W, padx=120)
rank2_cb.grid(row=16,column=1, sticky=W, padx=190)
ss_text_entry.grid(row=16,column=1, sticky=W, padx=340)
ss_text_label.grid(row=16,column=1, sticky=W, padx=410)
s_text_entry.grid(row=17, column=1, sticky=W)
postage_label.grid(row=18,column=0)
pos1.grid(row=18, column=1, sticky=W)
pos2.grid(row=18, column=1, sticky=W,padx=100)
prev_button.grid(row=19, column=1, sticky=W)
next_button.grid(row=19, column=1, sticky=W, padx=100)
calc_button.grid(row=19, column=1, sticky=W, padx=200)
auc_button.grid(row=19, column=1, sticky=W, padx=300)
delete_button.grid(row=19, column=1, sticky=W, padx=400)

shop_val.trace_add('write', lambda *args: save_settings())
firefox_profile_path_var.trace_add('write', lambda *args: save_settings())

frame1.pack()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()



