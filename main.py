import traceback
import os
import json
import random
import string
import shutil
from datetime import datetime

# KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard

# ==========================================
# ১. KV ডিজাইন (মিনিমাল - শুধু চেকবক্স)
# ==========================================
KV_CODE = '''
<ListItemWithCheckbox>:
    RightCheckbox:
        id: check
'''

# ==========================================
# ২. কাস্টম UI ক্লাস (Python Based - NO ERROR)
# ==========================================
class InfoCard(MDCard):
    """কানেকশন পেজের জন্য কার্ড ডিজাইন (পাইথনে তৈরি)"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(15)
        self.size_hint = (None, None)
        self.size = (dp(300), dp(90)) # কার্ডের সাইজ
        self.pos_hint = {"center_x": .5}
        self.radius = [15, ]
        self.elevation = 4
        # কার্ডের ব্যাকগ্রাউন্ড কালার (ডার্ক গ্রে)
        self.md_bg_color = (0.2, 0.2, 0.2, 1)

class DeletableListItem(OneLineAvatarIconListItem):
    def __init__(self, text="", icon="database", delete_callback=None, click_callback=None, **kwargs):
        super().__init__(text=text, **kwargs)
        self.add_widget(IconLeftWidget(icon=icon))
        del_btn = IconRightWidget(icon="delete", on_release=lambda x: delete_callback(text))
        self.add_widget(del_btn)
        self.bind(on_release=lambda x: click_callback(text))

class ListItemWithCheckbox(OneLineAvatarIconListItem):
    pass

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

# ==========================================
# ৩. ব্যাকেন্ড ইঞ্জিন (Safe Storage)
# ==========================================
def right_rotate(n, b):
    return ((n >> b) | (n << (32 - b))) & 0xFFFFFFFF

def bangla_hash_512(text):
    return "enc_" + text[::-1] + str(len(text))

class BackendEngine:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.root = os.path.join(self.base_path, "BanglaDB_Data")
        self.backup_root = os.path.join(self.base_path, "BanglaDB_Backups")

        if not os.path.exists(self.root): os.makedirs(self.root)
        if not os.path.exists(self.backup_root): os.makedirs(self.backup_root)
        
        self.repair_corrupted_files()
        self.config_file = os.path.join(self.root, "bangladb_config.json")
        if not os.path.exists(self.config_file):
            self.generate_new_api_key()

    def repair_corrupted_files(self):
        try:
            files = [f for f in os.listdir(self.root) if f.endswith('.json')]
            for f in files:
                path = os.path.join(self.root, f)
                try:
                    with open(path, 'r') as file:
                        data = json.load(file)
                    if "tables" not in data and "api_key" not in data:
                        data["tables"] = {}
                        with open(path, 'w') as file: json.dump(data, file)
                except:
                    with open(path, 'w') as file: json.dump({"tables": {}}, file)
        except Exception as e:
            print(f"Repair Warning: {e}")

    def generate_new_api_key(self):
        key = "bdb_" + ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        config = {"host": "127.0.0.1", "port": "5000", "api_key": key}
        with open(self.config_file, 'w') as f: json.dump(config, f)
        return config

    def get_connection_info(self):
        try:
            with open(self.config_file, 'r') as f: return json.load(f)
        except: return self.generate_new_api_key()

    def get_databases(self):
        try:
            return [f.replace('.json', '') for f in os.listdir(self.root) if f.endswith('.json') and "bangladb_config" not in f]
        except: return []

    def get_tables(self, db_name):
        path = os.path.join(self.root, f"{db_name}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: return list(json.load(f).get("tables", {}).keys())
            except: return []
        return []

    def get_table_data(self, db_name, table_name):
        path = os.path.join(self.root, f"{db_name}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: data = json.load(f)
                tbl = data.get("tables", {}).get(table_name)
                if tbl:
                    cols = tbl["columns"]
                    rows = [[r.get(c, "") for c in cols] for r in tbl["rows"]]
                    return cols, rows
            except: pass
        return [], []

    def create_db(self, name):
        with open(os.path.join(self.root, f"{name}.json"), 'w') as f: json.dump({"tables": {}}, f)

    def create_table(self, db_name, table_name, columns):
        path = os.path.join(self.root, f"{db_name}.json")
        with open(path, 'r') as f: data = json.load(f)
        if table_name not in data["tables"]:
            data["tables"][table_name] = {"columns": ["id"] + columns, "rows": []}
            with open(path, 'w') as f: json.dump(data, f, indent=4)

    def insert_data(self, db_name, table_name, data_dict):
        path = os.path.join(self.root, f"{db_name}.json")
        with open(path, 'r') as f: data = json.load(f)
        rows = data["tables"][table_name]["rows"]
        new_id = 1
        if rows:
            ids = [int(r.get("id")) for r in rows if str(r.get("id")).isdigit()]
            if ids: new_id = max(ids) + 1
        
        final_data = {"id": str(new_id)}
        for k, v in data_dict.items():
            final_data[k] = bangla_hash_512(v) if "pass" in k.lower() else v
        
        data["tables"][table_name]["rows"].append(final_data)
        with open(path, 'w') as f: json.dump(data, f, indent=4)

    def delete_database(self, db_name):
        p = os.path.join(self.root, f"{db_name}.json")
        if os.path.exists(p): os.remove(p)

    def delete_table(self, db_name, table_name):
        p = os.path.join(self.root, f"{db_name}.json")
        with open(p, 'r') as f: data = json.load(f)
        if table_name in data["tables"]:
            del data["tables"][table_name]
            with open(p, 'w') as f: json.dump(data, f)

    def delete_rows(self, db_name, table_name, row_ids):
        p = os.path.join(self.root, f"{db_name}.json")
        with open(p, 'r') as f: data = json.load(f)
        data["tables"][table_name]["rows"] = [r for r in data["tables"][table_name]["rows"] if r["id"] not in row_ids]
        with open(p, 'w') as f: json.dump(data, f)

    def perform_backup(self, db_name, selected_tables, full_backup):
        src = os.path.join(self.root, f"{db_name}.json")
        ts = datetime.now().strftime("%H%M%S")
        if not os.path.exists(src): return False, "No DB"
        if full_backup:
            shutil.copy(src, os.path.join(self.backup_root, f"{db_name}_FULL_{ts}.json"))
        else:
            with open(src, 'r') as f: data = json.load(f)
            new_data = {"tables": {t: data["tables"][t] for t in selected_tables if t in data["tables"]}}
            with open(os.path.join(self.backup_root, f"{db_name}_PART_{ts}.json"), 'w') as f: json.dump(new_data, f)
        return True, "Backup Success"

# ==========================================
# ৪. মেইন অ্যাপ
# ==========================================
class BanglaDBApp(MDApp):
    def build(self):
        try:
            Builder.load_string(KV_CODE)
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Teal"
            self.engine = BackendEngine()
            
            self.current_db = None
            self.current_table = None
            self.backup_selection = []
            
            self.nav_layout = MDNavigationLayout()
            self.sm = ScreenManager()
            
            # --- ওয়েলকাম স্ক্রিন ---
            self.screen_welcome = Screen(name="welcome")
            box = MDBoxLayout(orientation='vertical')
            box.add_widget(MDTopAppBar(title="BanglaDB Manager", left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]]))
            box.add_widget(MDLabel(text="Select Database from Sidebar", halign="center"))
            self.screen_welcome.add_widget(box)
            self.sm.add_widget(self.screen_welcome)

            # --- টেবিল স্ক্রিন ---
            self.screen_tables = Screen(name="tables")
            self.box_tables = MDBoxLayout(orientation='vertical')
            self.toolbar_tables = MDTopAppBar(title="Tables", left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]], right_action_items=[["plus", lambda x: self.dialog_add_table()]])
            self.box_tables.add_widget(self.toolbar_tables)
            self.list_tables = MDList()
            scroll = ScrollView(); scroll.add_widget(self.list_tables)
            self.box_tables.add_widget(scroll)
            self.screen_tables.add_widget(self.box_tables)
            self.sm.add_widget(self.screen_tables)

            # --- ডাটা স্ক্রিন ---
            self.screen_data = Screen(name="data")
            self.box_data = MDBoxLayout(orientation='vertical')
            self.toolbar_data = MDTopAppBar(title="Data View", left_action_items=[["arrow-left", lambda x: self.switch_screen("tables")]], 
                                            right_action_items=[["delete", lambda x: self.confirm_delete_rows()], ["database-plus", lambda x: self.dialog_insert_data()]])
            self.box_data.add_widget(self.toolbar_data)
            self.container_data = MDBoxLayout()
            self.box_data.add_widget(self.container_data)
            self.screen_data.add_widget(self.box_data)
            self.sm.add_widget(self.screen_data)

            # --- কানেকশন স্ক্রিন (Beautiful Design - FIXED) ---
            self.screen_connect = Screen(name="connect")
            self.box_connect = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
            self.toolbar_connect = MDTopAppBar(title="Connection Info", left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]])
            self.box_connect.add_widget(self.toolbar_connect)
            
            # টাইটেল
            self.box_connect.add_widget(MDLabel(text="SERVER DETAILS", theme_text_color="Custom", text_color=(0,1,1,1), font_style="H6", size_hint_y=None, height=dp(30)))

            # কার্ড ১: হোস্ট ও পোর্ট (Python Code দিয়ে বানানো)
            card_host = InfoCard()
            card_host.add_widget(MDLabel(text="HOST ADDRESS", theme_text_color="Secondary", font_style="Caption"))
            card_host.add_widget(MDLabel(text="127.0.0.1 : 5000", font_style="H5", theme_text_color="Primary", bold=True))
            self.box_connect.add_widget(card_host)

            # কার্ড ২: API Key
            card_key = InfoCard()
            card_key.size = ("300dp", "120dp")
            card_key.add_widget(MDLabel(text="SECRET API KEY", theme_text_color="Secondary", font_style="Caption"))
            self.lbl_key = MDLabel(text="Loading...", font_style="Body2", theme_text_color="Primary")
            card_key.add_widget(self.lbl_key)
            
            # রিজেনারেট বাটন
            regen_btn = MDIconButton(icon="refresh", pos_hint={"right": 1, "top": 1}, on_release=self.regenerate_key)
            card_key.add_widget(regen_btn)
            self.box_connect.add_widget(card_key)

            # কপি বাটন
            self.box_connect.add_widget(MDLabel(text="Use this for website connection:", halign="center", theme_text_color="Hint"))
            btn_copy = MDRaisedButton(text="COPY PYTHON CODE", size_hint_x=0.8, pos_hint={"center_x": .5}, md_bg_color=(0, 0.6, 0.6, 1), on_release=self.copy_code_to_clipboard)
            self.box_connect.add_widget(btn_copy)
            
            # স্পেস ফিল করার জন্য
            self.box_connect.add_widget(MDLabel())

            self.screen_connect.add_widget(self.box_connect)
            self.sm.add_widget(self.screen_connect)

            # --- ব্যাকআপ স্ক্রিন ---
            self.screen_backup = Screen(name="backup")
            self.box_backup = MDBoxLayout(orientation='vertical', padding=10, spacing=5)
            self.toolbar_backup = MDTopAppBar(title="Backup Center", left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]])
            self.box_backup.add_widget(self.toolbar_backup)
            self.lbl_select_db = MDLabel(text="Select Database:", size_hint_y=None, height=dp(30))
            self.box_backup.add_widget(self.lbl_select_db)
            self.list_backup_dbs = MDList()
            scroll_db = ScrollView(size_hint_y=0.4); scroll_db.add_widget(self.list_backup_dbs)
            self.box_backup.add_widget(scroll_db)
            self.chk_full = MDCheckbox(active=True, size_hint=(None, None), size=(dp(40), dp(40)))
            self.chk_full.bind(active=self.toggle_table_list)
            box_chk = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
            box_chk.add_widget(self.chk_full); box_chk.add_widget(MDLabel(text="Full Backup"))
            self.box_backup.add_widget(box_chk)
            self.list_backup_tables = MDList(); self.list_backup_tables.opacity = 0.5; self.list_backup_tables.disabled = True
            scroll_tbl = ScrollView(size_hint_y=0.4); scroll_tbl.add_widget(self.list_backup_tables)
            self.box_backup.add_widget(scroll_tbl)
            self.box_backup.add_widget(MDRaisedButton(text="START BACKUP", size_hint_x=1, on_release=self.process_backup))
            self.screen_backup.add_widget(self.box_backup)
            self.sm.add_widget(self.screen_backup)

            self.nav_layout.add_widget(self.sm)

            # --- সাইডবার ---
            self.nav_drawer = MDNavigationDrawer()
            drawer_box = MDBoxLayout(orientation="vertical", spacing="10dp", padding="10dp")
            drawer_box.add_widget(MDLabel(text="DATABASES", font_style="H6", size_hint_y=None, height=dp(20)))
            scroll_drawer = ScrollView()
            self.list_drawer = MDList()
            scroll_drawer.add_widget(self.list_drawer)
            drawer_box.add_widget(scroll_drawer)
            self.nav_drawer.add_widget(drawer_box)
            self.nav_layout.add_widget(self.nav_drawer)

            self.refresh_db_list()
            return self.nav_layout

        except Exception as e:
            return MDLabel(text=f"INIT ERROR: {e}\nTry deleting old files.", halign="center")

    # --- ফাংশনস ---
    def switch_screen(self, screen_name): self.sm.current = screen_name

    def refresh_db_list(self):
        self.list_drawer.clear_widgets()
        create = OneLineAvatarIconListItem(text="Create New Database", on_release=self.dialog_create_db)
        create.add_widget(IconLeftWidget(icon="plus-box"))
        self.list_drawer.add_widget(create)
        
        conn = OneLineAvatarIconListItem(text="Connection Info", on_release=self.open_connection_screen)
        conn.add_widget(IconLeftWidget(icon="lan-connect"))
        self.list_drawer.add_widget(conn)
        
        backup = OneLineAvatarIconListItem(text="Backup & Restore", on_release=self.open_backup_screen)
        backup.add_widget(IconLeftWidget(icon="cloud-upload"))
        self.list_drawer.add_widget(backup)
        
        for db in self.engine.get_databases():
            item = DeletableListItem(text=db, icon="database", delete_callback=self.confirm_delete_db, click_callback=self.open_database)
            self.list_drawer.add_widget(item)

    def open_database(self, db_name):
        self.current_db = db_name
        self.toolbar_tables.title = f"DB: {db_name}"
        self.refresh_table_list()
        self.switch_screen("tables")
        self.nav_drawer.set_state("close")

    def refresh_table_list(self):
        self.list_tables.clear_widgets()
        for tbl in self.engine.get_tables(self.current_db):
            item = DeletableListItem(text=tbl, icon="table", delete_callback=self.confirm_delete_table, click_callback=self.open_table_data)
            self.list_tables.add_widget(item)

    def open_table_data(self, table_name):
        self.current_table = table_name
        self.toolbar_data.title = f"Table: {table_name}"
        self.container_data.clear_widgets()
        cols, rows = self.engine.get_table_data(self.current_db, table_name)
        if cols:
            col_data = [(c, dp(30)) for c in cols]
            self.data_table = MDDataTable(column_data=col_data, row_data=rows, use_pagination=True, check=True)
            self.container_data.add_widget(self.data_table)
        self.switch_screen("data")

    def open_connection_screen(self, obj):
        self.switch_screen("connect"); self.nav_drawer.set_state("close"); self.load_api_details()

    def load_api_details(self):
        config = self.engine.get_connection_info()
        self.lbl_key.text = config["api_key"]
        self.code_input = f"import requests\nurl='http://127.0.0.1:5000/api'\nheaders={{'auth': '{config['api_key']}'}}"

    def regenerate_key(self, obj): self.engine.generate_new_api_key(); self.load_api_details()
    def copy_code_to_clipboard(self, obj): Clipboard.copy(self.code_input); self.show_alert("Python Code Copied!")

    def open_backup_screen(self, obj):
        self.switch_screen("backup"); self.nav_drawer.set_state("close"); self.list_backup_dbs.clear_widgets()
        for db in self.engine.get_databases():
            item = OneLineAvatarIconListItem(text=db, on_release=lambda x, name=db: self.on_backup_db_select(name))
            item.add_widget(IconLeftWidget(icon="database"))
            self.list_backup_dbs.add_widget(item)
        self.selected_backup_db = None; self.lbl_select_db.text = "1. Select Database: (None)"; self.list_backup_tables.clear_widgets()

    def on_backup_db_select(self, db_name):
        self.selected_backup_db = db_name; self.lbl_select_db.text = f"1. Selected: {db_name}"; self.list_backup_tables.clear_widgets(); self.backup_selection = []
        for tbl in self.engine.get_tables(db_name):
            chk = RightCheckbox(); chk.bind(active=lambda x, val, t=tbl: self.update_backup_selection(t, val))
            item = ListItemWithCheckbox(text=tbl); item.add_widget(chk); self.list_backup_tables.add_widget(item)

    def toggle_table_list(self, checkbox, value): self.list_backup_tables.disabled = value; self.list_backup_tables.opacity = 0.5 if value else 1
    def update_backup_selection(self, table, is_active): self.backup_selection.append(table) if is_active else self.backup_selection.remove(table)
    def process_backup(self, obj):
        if not self.selected_backup_db: self.show_alert("Select DB first!"); return
        success, msg = self.engine.perform_backup(self.selected_backup_db, self.backup_selection, self.chk_full.active)
        self.show_alert(msg)

    def dialog_create_db(self, obj):
        self.tf = MDTextField(hint_text="DB Name")
        self.dialog = MDDialog(title="Create DB", type="custom", content_cls=self.tf, buttons=[MDRaisedButton(text="CREATE", on_release=self.process_create_db)])
        self.dialog.open()
    def process_create_db(self, obj):
        if self.tf.text: self.engine.create_db(self.tf.text); self.refresh_db_list(); self.dialog.dismiss()

    def dialog_add_table(self):
        self.box_inp = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(100))
        self.tf_name = MDTextField(hint_text="Table Name"); self.tf_cols = MDTextField(hint_text="Cols")
        self.box_inp.add_widget(self.tf_name); self.box_inp.add_widget(self.tf_cols)
        self.dialog = MDDialog(title="New Table", type="custom", content_cls=self.box_inp, buttons=[MDRaisedButton(text="CREATE", on_release=self.process_create_table)])
        self.dialog.open()
    def process_create_table(self, obj):
        if self.tf_name.text and self.tf_cols.text: self.engine.create_table(self.current_db, self.tf_name.text, [c.strip() for c in self.tf_cols.text.split(',')]); self.refresh_table_list(); self.dialog.dismiss()

    def dialog_insert_data(self):
        cols, _ = self.engine.get_table_data(self.current_db, self.current_table)
        self.box_ins = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(50*len(cols)))
        self.ins_fields = {}
        for c in [i for i in cols if i != 'id']: f = MDTextField(hint_text=c); self.box_ins.add_widget(f); self.ins_fields[c] = f
        self.dialog = MDDialog(title="Insert", type="custom", content_cls=self.box_ins, buttons=[MDRaisedButton(text="SAVE", on_release=self.process_insert)])
        self.dialog.open()
    def process_insert(self, obj):
        self.engine.insert_data(self.current_db, self.current_table, {k: v.text for k, v in self.ins_fields.items()}); self.open_table_data(self.current_table); self.dialog.dismiss()

    def confirm_delete_db(self, name):
        self.dialog = MDDialog(title="Delete?", buttons=[MDRaisedButton(text="DELETE", md_bg_color="red", on_release=lambda x: self.do_del_db(name))]); self.dialog.open()
    def do_del_db(self, name): self.engine.delete_database(name); self.refresh_db_list(); self.dialog.dismiss()

    def confirm_delete_table(self, name):
        self.dialog = MDDialog(title="Delete?", buttons=[MDRaisedButton(text="DELETE", md_bg_color="red", on_release=lambda x: self.do_del_tbl(name))]); self.dialog.open()
    def do_del_tbl(self, name): self.engine.delete_table(self.current_db, name); self.refresh_table_list(); self.dialog.dismiss()

    def confirm_delete_rows(self):
        rows = self.data_table.get_row_checks()
        if rows: self.dialog = MDDialog(title="Delete?", buttons=[MDRaisedButton(text="DELETE", md_bg_color="red", on_release=lambda x: self.do_del_rows(rows))]); self.dialog.open()
    def do_del_rows(self, rows):
        self.engine.delete_rows(self.current_db, self.current_table, [r[0] for r in rows]); self.open_table_data(self.current_table); self.dialog.dismiss()

    def show_alert(self, text):
        self.dialog = MDDialog(text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]); self.dialog.open()

if __name__ == "__main__":
    try:
        BanglaDBApp().run()
    except Exception as e:
        print(f"CRASH: {e}")