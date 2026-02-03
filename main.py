import os
import json
import socket
import threading
import shutil
import zipfile
import uuid
import traceback  # 🔥 ডিবাগিং এর জন্য ইম্পোর্ট করা হলো
from datetime import datetime
from flask import Flask, request, jsonify

# 🔥 FIX: লাল ডট (Multi-touch Red Dot) বন্ধ করার কনফিগারেশন
from kivy.config import Config
try:
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    print("DEBUG: Kivy Config Set Successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to set Kivy Config: {e}")

# Kivy & KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, ThreeLineAvatarIconListItem, IRightBodyTouch
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDFillRoundFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer, MDNavigationDrawerMenu, MDNavigationDrawerItem, MDNavigationDrawerHeader
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.widget import Widget 

# কিবোর্ড সমস্যা সমাধান
Window.softinput_mode = "below_target"

# ==========================================
# 🔥 CRITICAL FIX: Right Content Container Class
# ==========================================
class RightContentCls(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True

# ==========================================
# ১. KV ডিজাইন (কালার ও লেআউট)
# ==========================================
KV_CODE = '''
#:set color_bg_milky [0.98, 0.98, 0.98, 1]
#:set color_primary_blue [0, 0.48, 1, 1]
#:set color_success_green [0, 0.8, 0.3, 1]
#:set color_danger_red [1, 0.2, 0.2, 1]
#:set color_warning_yellow [1, 0.75, 0, 1]
#:set color_card_white [1, 1, 1, 1]

<DrawerClickableItem@MDNavigationDrawerItem>
    focus_color: 0, 0.48, 1, 0.1
    text_color: 0.2, 0.2, 0.2, 1
    icon_color: 0, 0.48, 1, 1
    ripple_color: 0, 0.48, 1, 0.2
    selected_color: 0, 0.48, 1, 0.2

<AuthScreen>:
    md_bg_color: color_bg_milky
    ScrollView:
        do_scroll_x: False
        MDBoxLayout:
            orientation: 'vertical'
            padding: "20dp"
            spacing: "20dp"
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {"top": 1}

            MDBoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "150dp"
                spacing: "10dp"
                MDIconButton:
                    icon: "shield-check"
                    icon_size: "80sp"
                    pos_hint: {"center_x": .5}
                    theme_text_color: "Custom"
                    text_color: color_primary_blue
                MDLabel:
                    text: "BanglaDB Secure Login"
                    halign: "center"
                    font_style: "H5"
                    theme_text_color: "Custom"
                    text_color: 0.2, 0.2, 0.2, 1
                    bold: True

            MDCard:
                orientation: "vertical"
                padding: "20dp"
                spacing: "20dp"
                size_hint: 1, None
                height: "300dp"
                radius: [15, ]
                elevation: 3
                md_bg_color: color_card_white
                
                MDTextField:
                    id: user
                    hint_text: "Username"
                    icon_right: "account"
                    mode: "rectangle"
                MDTextField:
                    id: pasw
                    hint_text: "Password"
                    icon_right: "key"
                    password: True
                    mode: "rectangle"
                MDFillRoundFlatButton:
                    text: "LOGIN TO DASHBOARD"
                    font_size: "16sp"
                    size_hint_x: 1
                    md_bg_color: color_primary_blue
                    on_release: root.do_login()

            MDFlatButton:
                text: "Don't have an account? Register"
                pos_hint: {"center_x": .5}
                theme_text_color: "Custom"
                text_color: color_primary_blue
                on_release: app.switch_screen('register')

<RegisterScreen>:
    md_bg_color: color_bg_milky
    ScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            padding: "20dp"
            spacing: "20dp"
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {"top": 1}
            MDLabel:
                text: "Create New Account"
                halign: "center"
                font_style: "H4"
                size_hint_y: None
                height: "100dp"
                theme_text_color: "Custom"
                text_color: color_primary_blue
                bold: True
            MDCard:
                orientation: "vertical"
                padding: "20dp"
                spacing: "20dp"
                size_hint: 1, None
                height: "300dp"
                radius: [15, ]
                elevation: 3
                md_bg_color: color_card_white
                MDTextField:
                    id: reg_user
                    hint_text: "New Username"
                    mode: "rectangle"
                MDTextField:
                    id: reg_pass
                    hint_text: "New Password"
                    password: True
                    mode: "rectangle"
                MDFillRoundFlatButton:
                    text: "REGISTER ACCOUNT"
                    size_hint_x: 1
                    md_bg_color: color_success_green
                    on_release: root.do_reg()
            MDFlatButton:
                text: "Back to Login"
                pos_hint: {"center_x": .5}
                on_release: app.switch_screen('login')

<HomeScreen>:
    MDNavigationLayout:
        ScreenManager:
            Screen:
                name: "dashboard"
                MDBoxLayout:
                    orientation: 'vertical'
                    md_bg_color: color_bg_milky
                    MDTopAppBar:
                        title: "BanglaDB Panel"
                        elevation: 2
                        md_bg_color: color_card_white
                        specific_text_color: color_primary_blue
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]

                    ScrollView:
                        MDBoxLayout:
                            orientation: 'vertical'
                            padding: "15dp"
                            spacing: "15dp"
                            adaptive_height: True

                            MDCard:
                                orientation: "vertical"
                                padding: "20dp"
                                spacing: "10dp"
                                size_hint: 1, None
                                height: "160dp"
                                radius: [15, ]
                                elevation: 4
                                md_bg_color: color_card_white
                                line_color: (0.9, 0.9, 0.9, 1)
                                MDLabel:
                                    id: lbl_ip
                                    text: "SERVER: STOPPED"
                                    halign: "center"
                                    theme_text_color: "Custom"
                                    text_color: color_danger_red
                                    font_style: "H6"
                                    bold: True
                                MDFillRoundFlatButton:
                                    id: btn_server
                                    text: "START SERVER"
                                    font_size: "18sp"
                                    size_hint_x: 1
                                    md_bg_color: color_success_green
                                    on_release: root.toggle_server()

                            MDBoxLayout:
                                adaptive_height: True
                                padding: [0, "10dp", 0, 0]
                                MDLabel:
                                    text: "Your Databases"
                                    font_style: "H6"
                                    bold: True
                                    theme_text_color: "Custom"
                                    text_color: 0.3, 0.3, 0.3, 1

                            MDList:
                                id: db_list_view
                                spacing: "5dp"

        MDNavigationDrawer:
            id: nav_drawer
            radius: (0, 16, 16, 0)
            md_bg_color: color_card_white
            MDNavigationDrawerMenu:
                MDNavigationDrawerHeader:
                    title: "BanglaDB"
                    text: "Menu"
                    spacing: "4dp"
                    padding: "12dp", 0, 0, "56dp"
                DrawerClickableItem:
                    icon: "database-plus"
                    text: "Create New Database"
                    on_release: 
                        nav_drawer.set_state("close")
                        root.show_create_db_dialog()
                DrawerClickableItem:
                    icon: "lan-connect"
                    text: "Connection Info"
                    on_release: 
                        nav_drawer.set_state("close")
                        app.switch_screen('connect')
                DrawerClickableItem:
                    icon: "backup-restore"
                    text: "Backup & Restore"
                    on_release: 
                        nav_drawer.set_state("close")
                        app.switch_screen('backup')
                DrawerClickableItem:
                    icon: "logout"
                    text: "Logout"
                    text_color: color_danger_red
                    icon_color: color_danger_red
                    on_release: 
                        nav_drawer.set_state("close")
                        app.logout()

<TableScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: color_bg_milky
        MDTopAppBar:
            title: root.db_name
            md_bg_color: color_card_white
            specific_text_color: color_primary_blue
            left_action_items: [["arrow-left", lambda x: app.switch_screen('home')]]
            right_action_items: [["table-plus", lambda x: root.add_table_dialog()]]
        ScrollView:
            MDList:
                id: table_list
                padding: "10dp"
                spacing: "5dp"

<DataScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: color_bg_milky
        MDTopAppBar:
            title: root.table_name
            md_bg_color: color_card_white
            specific_text_color: color_primary_blue
            left_action_items: [["arrow-left", lambda x: app.switch_screen('tables')]]
            right_action_items: [["database-plus", lambda x: root.add_data_dialog()]]
        ScrollView:
            MDList:
                id: data_list
                padding: "10dp"
                spacing: "5dp"

<ConnectionScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: color_bg_milky
        MDTopAppBar:
            title: "Connection Info"
            md_bg_color: color_card_white
            specific_text_color: color_primary_blue
            left_action_items: [["arrow-left", lambda x: app.switch_screen('home')]]
        MDBoxLayout:
            orientation: 'vertical'
            padding: "20dp"
            spacing: "20dp"
            MDFillRoundFlatButton:
                id: btn_sel
                text: "SELECT DATABASE"
                size_hint_x: 1
                md_bg_color: color_primary_blue
                on_release: root.open_db_selector()
            MDRaisedButton:
                text: "GENERATE CODE"
                size_hint_x: 1
                md_bg_color: 0.2, 0.2, 0.2, 1
                on_release: root.gen_info()
            MDCard:
                size_hint_y: None
                height: "200dp"
                padding: "15dp"
                md_bg_color: color_card_white
                radius: [10, ]
                elevation: 2
                MDLabel:
                    id: res_lbl
                    text: "Code will appear here..."
                    halign: "center"
            MDLabel:

<BackupScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: color_bg_milky
        MDTopAppBar:
            title: "Backup & Restore"
            md_bg_color: color_card_white
            specific_text_color: color_primary_blue
            left_action_items: [["arrow-left", lambda x: app.switch_screen('home')]]
        
        MDBoxLayout:
            orientation: 'vertical'
            padding: "10dp"
            spacing: "10dp"
            
            MDBoxLayout:
                size_hint_y: None
                height: "100dp"
                orientation: 'vertical'
                spacing: "10dp"
                
                MDFillRoundFlatButton:
                    id: btn_select_db
                    text: "SELECT DATABASE (ALL)"
                    size_hint_x: 1
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    on_release: root.open_db_selector()

                MDBoxLayout:
                    spacing: "10dp"
                    MDFillRoundFlatButton:
                        text: "CREATE BACKUP"
                        size_hint_x: 0.5
                        md_bg_color: color_success_green
                        on_release: root.create_backup()
                    MDFillRoundFlatButton:
                        text: "UPLOAD FILE"
                        size_hint_x: 0.5
                        md_bg_color: color_primary_blue
                        on_release: root.open_file_manager()

            MDLabel:
                text: "Existing Backups (Tap to Restore)"
                size_hint_y: None
                height: "30dp"
                halign: "center"
                bold: True
                color: 0.5, 0.5, 0.5, 1

            ScrollView:
                MDList:
                    id: backup_list
                    spacing: "5dp"
'''

# ==========================================
# ২. ব্যাকেন্ড ইঞ্জিন (Backend)
# ==========================================
server = Flask(__name__)
SERVER_THREAD_STARTED = False
SERVER_ACTIVE = False
CURRENT_USER = None

class BackendEngine:
    def __init__(self):
        print("DEBUG: Initializing BackendEngine...")
        self.root = os.path.abspath("BanglaDB_Data")
        self.auth_file = os.path.abspath("bangladb_users.json")
        
        if platform == 'android':
            from android.storage import primary_external_storage_path
            self.backup_dir = os.path.join(primary_external_storage_path(), "BanglaDB_Backups")
        else:
            self.backup_dir = os.path.abspath("BanglaDB_Backups")
        
        try:
            if not os.path.exists(self.root): os.makedirs(self.root)
            if not os.path.exists(self.backup_dir): os.makedirs(self.backup_dir)
            print(f"DEBUG: Directories created/verified: {self.root}, {self.backup_dir}")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to create directories: {e}")
        
        # User auth file initialization
        try:
            if not os.path.exists(self.auth_file):
                with open(self.auth_file, 'w') as f: json.dump([], f)
                print("DEBUG: Created new auth file.")
            else:
                try:
                    with open(self.auth_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict): 
                             with open(self.auth_file, 'w') as f: json.dump([], f)
                             print("DEBUG: Reset auth file (was dict, expected list).")
                except:
                     with open(self.auth_file, 'w') as f: json.dump([], f)
                     print("DEBUG: Reset auth file (corrupted).")
        except Exception as e:
            print(f"DEBUG ERROR: Auth file init failed: {e}")

    def register_user(self, user, password):
        print(f"DEBUG: Registering user {user}")
        try:
            with open(self.auth_file, 'r') as f: users = json.load(f)
            for u in users:
                if u['user'] == user and u['pass'] == password:
                    print("DEBUG: User already exists")
                    return False, "This User+Password combination already exists!"
            
            unique_id = str(uuid.uuid4())
            users.append({"user": user, "pass": password, "uid": unique_id})
            with open(self.auth_file, 'w') as f: json.dump(users, f)
            
            user_folder = os.path.join(self.root, unique_id)
            if not os.path.exists(user_folder): os.makedirs(user_folder)
            
            print("DEBUG: Registration success")
            return True, "Success"
        except Exception as e:
            print(f"DEBUG ERROR: Register user failed: {e}")
            return False, f"Error: {str(e)}"

    def login_user(self, user, password):
        print(f"DEBUG: Attempting login for {user}")
        try:
            with open(self.auth_file, 'r') as f: users = json.load(f)
            for u in users:
                if u['user'] == user and u['pass'] == password:
                    global CURRENT_USER
                    CURRENT_USER = u
                    user_folder = os.path.join(self.root, u.get('uid'))
                    if not os.path.exists(user_folder): os.makedirs(user_folder)
                    print("DEBUG: Login success")
                    return True, "Login Success!"
            print("DEBUG: Login failed - Invalid credentials")
            return False, "Invalid Credentials"
        except Exception as e:
            print(f"DEBUG ERROR: Login failed: {e}")
            return False, f"Error: {str(e)}"

    def get_user_path(self, target_user_dict=None):
        user_info = target_user_dict if target_user_dict else CURRENT_USER
        if user_info and 'uid' in user_info:
            return os.path.join(self.root, user_info['uid'])
        return self.root

    # --- CRUD Operations ---
    def get_databases(self):
        try:
            user_path = self.get_user_path()
            if not os.path.exists(user_path): return []
            dbs = [f.replace('.json', '') for f in os.listdir(user_path) if f.endswith('.json')]
            print(f"DEBUG: Found databases: {dbs}")
            return dbs
        except Exception as e:
            print(f"DEBUG ERROR: get_databases failed: {e}")
            return []

    def create_db(self, name):
        print(f"DEBUG: Creating DB {name}")
        try:
            user_path = self.get_user_path()
            path = f"{user_path}/{name}.json"
            if not os.path.exists(path):
                with open(path, 'w') as f: json.dump({"tables": {}}, f)
                print("DEBUG: DB Created")
                return True
            print("DEBUG: DB Exists")
            return False
        except Exception as e:
            print(f"DEBUG ERROR: create_db failed: {e}")
            return False

    def rename_db(self, old_name, new_name):
        print(f"DEBUG: Renaming DB {old_name} to {new_name}")
        try:
            user_path = self.get_user_path()
            old_path = os.path.join(user_path, f"{old_name}.json")
            new_path = os.path.join(user_path, f"{new_name}.json")
            if os.path.exists(old_path) and not os.path.exists(new_path):
                os.rename(old_path, new_path)
                return True
            return False
        except Exception as e:
            print(f"DEBUG ERROR: rename_db failed: {e}")
            return False

    def delete_db(self, name):
        print(f"DEBUG: Deleting DB {name}")
        try:
            user_path = self.get_user_path()
            path = f"{user_path}/{name}.json"
            if os.path.exists(path): os.remove(path)
        except Exception as e:
            print(f"DEBUG ERROR: delete_db failed: {e}")

    def get_tables(self, db, user_obj=None):
        try:
            path = f"{self.get_user_path(user_obj)}/{db}.json"
            with open(path, 'r') as f: return list(json.load(f)["tables"].keys())
        except Exception as e:
            print(f"DEBUG ERROR: get_tables failed: {e}")
            return []

    def create_table(self, db, table, cols, user_obj=None):
        print(f"DEBUG: Creating table {table} in {db}")
        try:
            path = f"{self.get_user_path(user_obj)}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            if table not in d["tables"]:
                d["tables"][table] = {"columns": ["id"] + cols, "rows": []}
                with open(path, 'w') as f: json.dump(d, f, indent=4)
        except Exception as e:
            print(f"DEBUG ERROR: create_table failed: {e}")

    def update_table_struct(self, db, old_table_name, new_table_name, new_cols):
        print(f"DEBUG: Updating table struct {old_table_name} -> {new_table_name}")
        try:
            path = f"{self.get_user_path()}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            
            if old_table_name in d["tables"]:
                table_data = d["tables"].pop(old_table_name)
                
                if "id" not in new_cols: new_cols.insert(0, "id")
                table_data["columns"] = new_cols
                
                d["tables"][new_table_name] = table_data
                
                with open(path, 'w') as f: json.dump(d, f, indent=4)
                return True
            return False
        except Exception as e:
            print(f"DEBUG ERROR: update_table_struct failed: {e}")
            return False

    def delete_table(self, db, table):
        print(f"DEBUG: Deleting table {table}")
        try:
            path = f"{self.get_user_path()}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            if table in d["tables"]:
                del d["tables"][table]
                with open(path, 'w') as f: json.dump(d, f, indent=4)
        except Exception as e:
            print(f"DEBUG ERROR: delete_table failed: {e}")

    def get_table_data(self, db, table, user_obj=None):
        try:
            path = f"{self.get_user_path(user_obj)}/{db}.json"
            with open(path, 'r') as f:
                data = json.load(f)["tables"].get(table)
                if data: return data["columns"], data["rows"]
        except Exception as e:
            print(f"DEBUG ERROR: get_table_data failed: {e}")
        return [], []

    def insert_data(self, db, table, data, user_obj=None):
        print(f"DEBUG: Inserting data into {table}")
        try:
            path = f"{self.get_user_path(user_obj)}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            rows = d["tables"][table]["rows"]
            new_id = str(max([int(r.get("id", 0)) for r in rows], default=0) + 1)
            data["id"] = new_id
            rows.append(data)
            with open(path, 'w') as f: json.dump(d, f, indent=4)
        except Exception as e:
            print(f"DEBUG ERROR: insert_data failed: {e}")

    def update_row_data(self, db, table, row_id, new_data, user_obj=None):
        print(f"DEBUG: Updating row {row_id} in {table}")
        try:
            path = f"{self.get_user_path(user_obj)}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            rows = d["tables"][table]["rows"]
            
            for i, row in enumerate(rows):
                if str(row.get("id")) == str(row_id):
                    new_data["id"] = row_id
                    rows[i] = new_data
                    with open(path, 'w') as f: json.dump(d, f, indent=4)
                    return True
            return False
        except Exception as e:
            print(f"DEBUG ERROR: update_row_data failed: {e}")
            return False

    def delete_data(self, db, table, row_id):
        print(f"DEBUG: Deleting row {row_id} from {table}")
        try:
            path = f"{self.get_user_path()}/{db}.json"
            with open(path, 'r') as f: d = json.load(f)
            d["tables"][table]["rows"] = [r for r in d["tables"][table]["rows"] if str(r.get("id")) != str(row_id)]
            with open(path, 'w') as f: json.dump(d, f, indent=4)
        except Exception as e:
            print(f"DEBUG ERROR: delete_data failed: {e}")

    # --- Backup System ---
    def create_backup(self, db_name=None):
        print(f"DEBUG: Creating backup for {db_name}")
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_path = self.get_user_path()
            
            if db_name and db_name != "ALL":
                source_file = os.path.join(user_path, f"{db_name}.json")
                if not os.path.exists(source_file): return "Database not found!"
                
                zip_filename = f"{CURRENT_USER['user']}_{db_name}_{ts}.zip"
                save_path = os.path.join(self.backup_dir, zip_filename)
                
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(source_file, arcname=f"{db_name}.json")
                return f"Backup Saved!\nLocation:\n{save_path}"
            else:
                base_name = f"{CURRENT_USER['user']}_FULL_{ts}.zip"
                save_path = os.path.join(self.backup_dir, base_name)
                
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(user_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zf.write(file_path, arcname=file)
                return f"Full Backup Saved!\nLocation:\n{save_path}"
        except Exception as e:
            print(f"DEBUG ERROR: create_backup failed: {e}")
            return f"Error: {str(e)}"

    def get_backups(self):
        try:
            return [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]
        except Exception as e:
            print(f"DEBUG ERROR: get_backups failed: {e}")
            return []

    def restore_backup(self, filepath):
        print(f"DEBUG: Restoring backup from {filepath}")
        try:
            target_path = self.get_user_path()
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(target_path)
            return True, "Restore Successful!"
        except Exception as e:
            print(f"DEBUG ERROR: restore_backup failed: {e}")
            return False, str(e)
            
    def authenticate_api_user(self, user, password):
        try:
            with open(self.auth_file, 'r') as f: users = json.load(f)
            for u in users:
                if u['user'] == user and u['pass'] == password:
                    if 'uid' not in u: u['uid'] = str(uuid.uuid4())
                    return u
        except Exception as e:
            print(f"DEBUG ERROR: authenticate_api_user failed: {e}")
        return None

try:
    engine = BackendEngine()
except Exception as e:
    print(f"DEBUG CRITICAL: Engine Init Failed: {e}")
    traceback.print_exc()

# --- FLASK API ---
@server.route('/api', methods=['POST'])
def api_handler():
    if not SERVER_ACTIVE: return jsonify({"status": "error", "msg": "Server is Stopped"}), 503
    try:
        data = request.json
        user_obj = engine.authenticate_api_user(data.get('user'), data.get('pass'))
        
        if not user_obj:
            return jsonify({"status": "error", "msg": "Auth Failed"}), 401
        
        action = data.get('action')
        db, table = data.get('db'), data.get('table')
        
        if action == "get":
            c, r = engine.get_table_data(db, table, user_obj=user_obj)
            rows_list = [[r.get(col, "") for col in c] for r in r]
            return jsonify({"status": "success", "columns": c, "data": rows_list})
        elif action == "insert":
            engine.insert_data(db, table, data.get('row'), user_obj=user_obj)
            return jsonify({"status": "success"})
        elif action == "update":
            row_id = data.get('id')
            new_data = data.get('data')
            if engine.update_row_data(db, table, row_id, new_data, user_obj=user_obj):
                return jsonify({"status": "success", "msg": "Updated"})
            else:
                return jsonify({"status": "error", "msg": "ID not found"})
                
        return jsonify({"status": "error", "msg": "Invalid Action"})
    except Exception as e:
        print(f"DEBUG ERROR: API Handler failed: {e}")
        return jsonify({"status": "error", "msg": str(e)})

def run_flask():
    print("DEBUG: Starting Flask Server...")
    try:
        server.run(host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"DEBUG CRITICAL: Flask Server Failed: {e}")

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception as e:
        print(f"DEBUG ERROR: get_ip failed: {e}")
        return "127.0.0.1"

# ==========================================
# ৩. UI Logic (Screens)
# ==========================================
class AuthScreen(Screen):
    dialog = None
    def do_login(self):
        print("DEBUG: Login Button Pressed")
        try:
            res, msg = engine.login_user(self.ids.user.text, self.ids.pasw.text)
            if res: 
                MDApp.get_running_app().switch_screen('home')
            else: 
                self.show_alert(msg)
        except Exception as e:
            print(f"DEBUG ERROR: do_login failed: {e}")
            self.show_alert(f"Error: {e}")
    
    def show_alert(self, t):
        if not self.dialog:
            self.dialog = MDDialog(text=t, buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.text = t
        self.dialog.open()

class RegisterScreen(Screen):
    dialog = None
    def do_reg(self):
        print("DEBUG: Register Button Pressed")
        try:
            res, msg = engine.register_user(self.ids.reg_user.text, self.ids.reg_pass.text)
            if not self.dialog:
                self.dialog = MDDialog(buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
            self.dialog.text = msg
            self.dialog.bind(on_dismiss=lambda x: MDApp.get_running_app().switch_screen('login') if res else None)
            self.dialog.open()
        except Exception as e:
            print(f"DEBUG ERROR: do_reg failed: {e}")

class HomeScreen(Screen):
    dialog = None
    create_dialog = None
    
    def on_enter(self): 
        print("DEBUG: HomeScreen Entered")
        self.load_dbs()
    
    def load_dbs(self):
        print("DEBUG: Loading Databases to List")
        try:
            self.ids.db_list_view.clear_widgets()
            for db in engine.get_databases():
                item = OneLineAvatarIconListItem(
                    text=db, 
                    bg_color=(1,1,1,1), 
                    on_release=lambda x, d=db: MDApp.get_running_app().open_table_screen(d)
                )
                item.add_widget(IconLeftWidget(icon="database", theme_text_color="Custom", text_color=(0, 0.48, 1, 1)))
                
                right_container = RightContentCls(spacing=dp(15))
                
                edit_btn = MDIconButton(icon="pencil", theme_text_color="Custom", text_color=(1, 0.75, 0, 1), pos_hint={"center_y": .5})
                edit_btn.bind(on_release=lambda x, d=db: self.show_rename_db_dialog(d))
                
                del_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1), pos_hint={"center_y": .5})
                del_btn.bind(on_release=lambda x, d=db: self.confirm_delete(d))
                
                spacer = Widget(size_hint_x=None, width=dp(15)) 
                
                right_container.add_widget(edit_btn)
                right_container.add_widget(del_btn)
                right_container.add_widget(spacer) 
                
                item.add_widget(right_container)
                self.ids.db_list_view.add_widget(item)
        except Exception as e:
            print(f"DEBUG ERROR: load_dbs failed: {e}")

    def show_rename_db_dialog(self, old_name):
        self.tf_rename = MDTextField(text=old_name, hint_text="New Database Name")
        self.dialog = MDDialog(title="Rename Database", type="custom", content_cls=self.tf_rename,
                               buttons=[MDRaisedButton(text="RENAME", on_release=lambda x: (engine.rename_db(old_name, self.tf_rename.text), self.load_dbs(), self.dialog.dismiss())),
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def confirm_delete(self, db):
        self.dialog = MDDialog(title="Delete Database?", text=f"Delete '{db}'? ALL DATA WILL BE LOST!",
                               buttons=[MDRaisedButton(text="DELETE", md_bg_color=(1,0.2,0.2,1), on_release=lambda x: (engine.delete_db(db), self.load_dbs(), self.dialog.dismiss())),
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()
    
    def toggle_server(self):
        global SERVER_ACTIVE, SERVER_THREAD_STARTED
        print(f"DEBUG: Toggling Server. Current State: {SERVER_ACTIVE}")
        btn = self.ids.btn_server; lbl = self.ids.lbl_ip
        if not SERVER_ACTIVE:
            if not SERVER_THREAD_STARTED: 
                threading.Thread(target=run_flask, daemon=True).start()
                SERVER_THREAD_STARTED = True
                print("DEBUG: Server Thread Started")
            SERVER_ACTIVE = True; btn.text = "STOP SERVER"; btn.md_bg_color = (1, 0.2, 0.2, 1); lbl.text = f"RUNNING: {get_ip()}:5000"; lbl.text_color = (0, 0.8, 0.3, 1)
        else:
            SERVER_ACTIVE = False; btn.text = "START SERVER"; btn.md_bg_color = (0, 0.8, 0.3, 1); lbl.text = "SERVER: STOPPED"; lbl.text_color = (1, 0.2, 0.2, 1)

    def show_create_db_dialog(self):
        self.tf = MDTextField(hint_text="Database Name")
        self.create_dialog = MDDialog(title="Create DB", type="custom", content_cls=self.tf,
                                      buttons=[MDRaisedButton(text="CREATE", on_release=lambda x: (engine.create_db(self.tf.text), self.load_dbs(), self.create_dialog.dismiss())),
                                               MDFlatButton(text="CANCEL", on_release=lambda x: self.create_dialog.dismiss())])
        self.create_dialog.open()

class TableScreen(Screen):
    db_name = StringProperty("")
    dialog = None
    create_dialog = None
    
    def on_enter(self):
        print(f"DEBUG: TableScreen Entered for DB: {self.db_name}")
        self.ids.table_list.clear_widgets()
        try:
            for t in engine.get_tables(self.db_name):
                item = OneLineAvatarIconListItem(
                    text=t, 
                    bg_color=(1,1,1,1), 
                    on_release=lambda x, table=t: MDApp.get_running_app().open_data_screen(self.db_name, table)
                )
                item.add_widget(IconLeftWidget(icon="table", theme_text_color="Custom", text_color=(0, 0.48, 1, 1)))
                
                right_container = RightContentCls(spacing=dp(15))
                
                edit_btn = MDIconButton(icon="pencil", theme_text_color="Custom", text_color=(1, 0.75, 0, 1), pos_hint={"center_y": .5})
                edit_btn.bind(on_release=lambda x, table=t: self.show_edit_table_dialog(table))
                
                del_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1), pos_hint={"center_y": .5})
                del_btn.bind(on_release=lambda x, table=t: self.confirm_delete(table))
                
                spacer = Widget(size_hint_x=None, width=dp(15))
                
                right_container.add_widget(edit_btn)
                right_container.add_widget(del_btn)
                right_container.add_widget(spacer)
                
                item.add_widget(right_container)
                self.ids.table_list.add_widget(item)
        except Exception as e:
            print(f"DEBUG ERROR: Table load failed: {e}")

    def show_edit_table_dialog(self, old_table_name):
        c, _ = engine.get_table_data(self.db_name, old_table_name)
        cols_str = ",".join([col for col in c if col != 'id'])
        
        self.bx = MDBoxLayout(orientation="vertical", size_hint_y=None, height="120dp")
        self.tf_name_edit = MDTextField(text=old_table_name, hint_text="Table Name")
        self.tf_cols_edit = MDTextField(text=cols_str, hint_text="Columns (comma separated)")
        self.bx.add_widget(self.tf_name_edit)
        self.bx.add_widget(self.tf_cols_edit)
        
        self.dialog = MDDialog(title="Edit Table & Columns", type="custom", content_cls=self.bx,
                               buttons=[MDRaisedButton(text="UPDATE", on_release=lambda x: (engine.update_table_struct(self.db_name, old_table_name, self.tf_name_edit.text, self.tf_cols_edit.text.split(',')), self.on_enter(), self.dialog.dismiss())),
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()
    
    def confirm_delete(self, table):
        self.dialog = MDDialog(title="Delete Table?", text=f"Delete table '{table}'?", 
                               buttons=[MDRaisedButton(text="DELETE", md_bg_color="red", on_release=lambda x: (engine.delete_table(self.db_name, table), self.on_enter(), self.dialog.dismiss())),
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def add_table_dialog(self):
        self.bx = MDBoxLayout(orientation="vertical", size_hint_y=None, height="120dp"); self.tf_name = MDTextField(hint_text="Table Name"); self.tf_cols = MDTextField(hint_text="Cols (name,age)")
        self.bx.add_widget(self.tf_name); self.bx.add_widget(self.tf_cols)
        self.create_dialog = MDDialog(title="New Table", type="custom", content_cls=self.bx, 
                                      buttons=[MDRaisedButton(text="CREATE", on_release=lambda x: (engine.create_table(self.db_name, self.tf_name.text, self.tf_cols.text.split(',')), self.on_enter(), self.create_dialog.dismiss())), 
                                               MDFlatButton(text="CANCEL", on_release=lambda x: self.create_dialog.dismiss())])
        self.create_dialog.open()

class DataScreen(Screen):
    db_name = StringProperty(""); table_name = StringProperty("")
    dialog = None
    create_dialog = None
    
    def on_enter(self):
        print(f"DEBUG: DataScreen Entered for Table: {self.table_name}")
        self.ids.data_list.clear_widgets()
        try:
            cols, rows = engine.get_table_data(self.db_name, self.table_name)
            if not rows: self.ids.data_list.add_widget(MDLabel(text="No Data Found", halign="center")); return
                
            for r in rows:
                row_id = r.get("id", "?")
                all_data = " | ".join([f"{k}:{v}" for k,v in r.items() if k != 'id'])
                
                item = ThreeLineAvatarIconListItem(text=f"ID: {row_id}", secondary_text=all_data, bg_color=(1,1,1,1))
                item.add_widget(IconLeftWidget(icon="text-box-outline", theme_text_color="Custom", text_color=(0, 0.48, 1, 1)))
                
                right_container = RightContentCls(spacing=dp(15))
                
                edit_btn = MDIconButton(icon="pencil", theme_text_color="Custom", text_color=(1, 0.75, 0, 1), pos_hint={"center_y": .5})
                edit_btn.bind(on_release=lambda x, d=r: self.show_edit_row_dialog(d))
                
                del_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1), pos_hint={"center_y": .5})
                del_btn.bind(on_release=lambda x, rid=row_id: self.confirm_delete(rid))
                
                spacer = Widget(size_hint_x=None, width=dp(15))
                
                right_container.add_widget(edit_btn)
                right_container.add_widget(del_btn)
                right_container.add_widget(spacer)
                
                item.add_widget(right_container)
                self.ids.data_list.add_widget(item)
        except Exception as e:
            print(f"DEBUG ERROR: Row load failed: {e}")

    def show_edit_row_dialog(self, row_data):
        c, _ = engine.get_table_data(self.db_name, self.table_name)
        dialog_height = dp(60 * (len(c) - 1)) if len(c) > 1 else dp(100)
        self.bx = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dialog_height)
        self.inputs = {}
        
        for col in c:
            if col == 'id': continue
            tf = MDTextField(text=str(row_data.get(col, "")), hint_text=col)
            self.inputs[col] = tf
            self.bx.add_widget(tf)
            
        self.dialog = MDDialog(title=f"Edit Row ID: {row_data.get('id')}", type="custom", content_cls=self.bx,
                               buttons=[MDRaisedButton(text="UPDATE", on_release=lambda x: (engine.update_row_data(self.db_name, self.table_name, row_data.get('id'), {k: v.text for k,v in self.inputs.items()}), self.on_enter(), self.dialog.dismiss())),
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def confirm_delete(self, row_id):
        self.dialog = MDDialog(title="Delete Row?", text=f"Delete ID: {row_id}?", 
                               buttons=[MDRaisedButton(text="DELETE", md_bg_color="red", on_release=lambda x: (engine.delete_data(self.db_name, self.table_name, row_id), self.on_enter(), self.dialog.dismiss())), 
                                        MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def add_data_dialog(self):
        c, _ = engine.get_table_data(self.db_name, self.table_name)
        dialog_height = dp(60 * (len(c) - 1)) if len(c) > 1 else dp(100)
        self.bx = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dialog_height); 
        self.inputs = {col: MDTextField(hint_text=col) for col in c if col != 'id'}
        for w in self.inputs.values(): self.bx.add_widget(w)
        self.create_dialog = MDDialog(title="Add Data", type="custom", content_cls=self.bx, 
                                      buttons=[MDRaisedButton(text="SAVE", on_release=lambda x: (engine.insert_data(self.db_name, self.table_name, {k: v.text for k,v in self.inputs.items()}), self.on_enter(), self.create_dialog.dismiss())), 
                                               MDFlatButton(text="CANCEL", on_release=lambda x: self.create_dialog.dismiss())])
        self.create_dialog.open()

class ConnectionScreen(Screen):
    selected_db = StringProperty("")
    dialog = None
    
    def open_db_selector(self):
        dbs = engine.get_databases()
        if not dbs: return
        items = MDList()
        for db in dbs:
            item = OneLineAvatarIconListItem(text=db, on_release=lambda x, d=db: self.set_db(d))
            item.add_widget(IconLeftWidget(icon="database"))
            items.add_widget(item)
        self.dialog = MDDialog(title="Select DB", type="custom", content_cls=ScrollView(size_hint_y=None, height="200dp", do_scroll_x=False), buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.content_cls.add_widget(items)
        self.dialog.open()
    
    def set_db(self, db): self.selected_db = db; self.ids.btn_sel.text = f"SELECTED: {db}"; self.dialog.dismiss()
    def gen_info(self):
        if not self.selected_db: return
        ip = get_ip(); u=CURRENT_USER['user']; p=CURRENT_USER['pass']
        code = f"""<?php
$url = "http://{ip}:5000/api";
$data = array("user"=>"{u}", "pass"=>"{p}", "db"=>"{self.selected_db}", "action"=>"get", "table"=>"YOUR_TABLE");
$options = array("http"=>array("header"=>"Content-type: application/json", "method"=>"POST", "content"=>json_encode($data)));
$result = file_get_contents($url, false, stream_context_create($options));
echo $result;
?>"""
        self.ids.res_lbl.text = f"HOST: {ip}:5000\nUser: {u}\nPass: {p}\nDB: {self.selected_db}\n(Code Copied)"; Clipboard.copy(code)

class BackupScreen(Screen):
    dialog = None
    file_manager = None
    selected_db_to_backup = StringProperty("ALL")
    
    def on_enter(self): self.load_backups()
    
    def load_backups(self):
        self.ids.backup_list.clear_widgets()
        try:
            for f in engine.get_backups():
                item = OneLineAvatarIconListItem(text=f, on_release=lambda x, fi=f: self.restore_internal(fi))
                item.add_widget(IconLeftWidget(icon="zip-box"))
                self.ids.backup_list.add_widget(item)
        except Exception as e:
            print(f"DEBUG ERROR: load_backups failed: {e}")
    
    def open_db_selector(self):
        dbs = engine.get_databases()
        if not dbs: return
        items = MDList()
        item_all = OneLineAvatarIconListItem(text="ALL DATABASES (Full Backup)", on_release=lambda x: self.set_backup_db("ALL"))
        item_all.add_widget(IconLeftWidget(icon="folder-zip"))
        items.add_widget(item_all)
        for db in dbs:
            item = OneLineAvatarIconListItem(text=db, on_release=lambda x, d=db: self.set_backup_db(d))
            item.add_widget(IconLeftWidget(icon="database"))
            items.add_widget(item)
        self.dialog = MDDialog(title="Select Database", type="custom", content_cls=ScrollView(size_hint_y=None, height="200dp", do_scroll_x=False), buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.content_cls.add_widget(items)
        self.dialog.open()

    def set_backup_db(self, db):
        self.selected_db_to_backup = db
        self.ids.btn_select_db.text = f"SELECTED: {db}"
        self.dialog.dismiss()

    def create_backup(self):
        msg = engine.create_backup(self.selected_db_to_backup)
        self.dialog = MDDialog(text=msg, buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()
        self.load_backups()
    
    def restore_internal(self, f):
        self.dialog = MDDialog(title="Restore?", text=f"Restore {f}?", 
                               buttons=[MDRaisedButton(text="YES", md_bg_color="red", on_release=lambda x: (engine.restore_backup(f"{engine.backup_dir}/{f}"), self.dialog.dismiss())), 
                                        MDFlatButton(text="NO", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def open_file_manager(self):
        if not self.file_manager:
            path = os.path.expanduser("~")
            if platform == 'android': path = "/storage/emulated/0"
            self.file_manager = MDFileManager(exit_manager=self.exit_manager, select_path=self.select_path, ext=['.zip'])
        self.file_manager.show(os.path.expanduser("~"))

    def select_path(self, path):
        self.exit_manager()
        res, msg = engine.restore_backup(path)
        self.dialog = MDDialog(text=msg, buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def exit_manager(self, *args):
        if self.file_manager: self.file_manager.close()

class BanglaDBApp(MDApp):
    def build(self):
        print("DEBUG: Building App Layout")
        Builder.load_string(KV_CODE)
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(AuthScreen(name="login"))
        self.sm.add_widget(RegisterScreen(name="register"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(TableScreen(name="tables"))
        self.sm.add_widget(DataScreen(name="data"))
        self.sm.add_widget(ConnectionScreen(name="connect"))
        self.sm.add_widget(BackupScreen(name="backup"))
        return self.sm

    # 🔥 FIX: অ্যাপ চালু হওয়ার সময় পারমিশন চাওয়া
    def on_start(self):
        print("DEBUG: App Started")
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE, 
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.INTERNET
                ])
                print("DEBUG: Permissions Requested")
            except Exception as e:
                print(f"DEBUG CRITICAL: Permission Request Failed: {e}")

    def switch_screen(self, name): self.sm.current = name
    def open_table_screen(self, db): self.sm.get_screen("tables").db_name = db; self.switch_screen("tables")
    def open_data_screen(self, db, t): s=self.sm.get_screen("data"); s.db_name=db; s.table_name=t; self.switch_screen("data")
    def logout(self): global CURRENT_USER; CURRENT_USER=None; self.switch_screen("login")

if __name__ == "__main__":
    try:
        BanglaDBApp().run()
    except Exception as e:
        print(f"CRITICAL APP CRASH: {e}")
        traceback.print_exc()
