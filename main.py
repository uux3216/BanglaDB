import os
import json
import socket
import threading
import random
import string
from functools import partial
from flask import Flask, request, jsonify

# KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.spinner import MDSpinner
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.metrics import dp

# ==========================================
# ১. KV ডিজাইন (UI)
# ==========================================
KV_CODE = '''
<InfoCard@MDCard>:
    orientation: "vertical"
    padding: "15dp"
    size_hint: None, None
    size: "300dp", "160dp"
    pos_hint: {"center_x": .5}
    radius: [15, ]
    elevation: 4
    md_bg_color: 0.18, 0.18, 0.18, 1

<AuthCard@MDCard>:
    orientation: "vertical"
    padding: "20dp"
    spacing: "15dp"
    size_hint: 0.85, None
    height: "350dp"
    pos_hint: {"center_x": .5, "center_y": .5}
    radius: [20, ]
    elevation: 5
'''

# ==========================================
# ২. সার্ভার ও ব্যাকেন্ড ইঞ্জিন
# ==========================================
server = Flask(__name__)
SERVER_RUNNING = False
CURRENT_USER = None

class BackendEngine:
    def __init__(self):
        self.root = "BanglaDB_Data"
        self.auth_file = "bangladb_users.json"
        if not os.path.exists(self.root): os.makedirs(self.root)
        if not os.path.exists(self.auth_file):
            with open(self.auth_file, 'w') as f: json.dump({}, f)

    # --- User Management ---
    def register_user(self, user, password):
        with open(self.auth_file, 'r') as f: users = json.load(f)
        if user in users: return False, "User already exists!"
        users[user] = password  # In production, use hashing
        with open(self.auth_file, 'w') as f: json.dump(users, f)
        return True, "Registration Successful!"

    def login_user(self, user, password):
        with open(self.auth_file, 'r') as f: users = json.load(f)
        if user in users and users[user] == password:
            global CURRENT_USER
            CURRENT_USER = {"user": user, "pass": password}
            return True, "Login Success!"
        return False, "Invalid Credentials"

    # --- Database Operations ---
    def get_databases(self):
        return [f.replace('.json', '') for f in os.listdir(self.root) if f.endswith('.json')]

    def get_tables(self, db):
        try:
            with open(f"{self.root}/{db}.json", 'r') as f: return list(json.load(f)["tables"].keys())
        except: return []

    def get_table_data(self, db, table):
        try:
            with open(f"{self.root}/{db}.json", 'r') as f:
                data = json.load(f)["tables"].get(table)
                if data: return data["columns"], [[r.get(c, "") for c in data["columns"]] for r in data["rows"]]
        except: pass
        return [], []

    def create_db(self, name):
        with open(f"{self.root}/{name}.json", 'w') as f: json.dump({"tables": {}}, f)

    def create_table(self, db, table, cols):
        path = f"{self.root}/{db}.json"
        with open(path, 'r') as f: d = json.load(f)
        d["tables"][table] = {"columns": ["id"] + cols, "rows": []}
        with open(path, 'w') as f: json.dump(d, f, indent=4)

    def insert_data(self, db, table, data):
        path = f"{self.root}/{db}.json"
        with open(path, 'r') as f: d = json.load(f)
        rows = d["tables"][table]["rows"]
        new_id = str(max([int(r["id"]) for r in rows], default=0) + 1)
        data["id"] = new_id
        rows.append(data)
        with open(path, 'w') as f: json.dump(d, f, indent=4)

    def delete_rows(self, db, table, ids):
        path = f"{self.root}/{db}.json"
        with open(path, 'r') as f: d = json.load(f)
        d["tables"][table]["rows"] = [r for r in d["tables"][table]["rows"] if r["id"] not in ids]
        with open(path, 'w') as f: json.dump(d, f)

engine = BackendEngine()

# --- FLASK API ROUTES ---
@server.route('/api', methods=['POST'])
def api_handler():
    try:
        data = request.json
        req_user = data.get('user')
        req_pass = data.get('pass')
        
        # Verify Credentials
        is_valid, _ = engine.login_user(req_user, req_pass)
        if not is_valid: return jsonify({"status": "error", "msg": "Auth Failed"}), 401

        action = data.get('action')
        db = data.get('db')
        table = data.get('table')

        if action == "get":
            cols, rows = engine.get_table_data(db, table)
            return jsonify({"status": "success", "columns": cols, "data": rows})
        
        elif action == "insert":
            row_data = data.get('row')
            engine.insert_data(db, table, row_data)
            return jsonify({"status": "success", "msg": "Inserted"})

        return jsonify({"status": "error", "msg": "Invalid Action"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

def run_flask():
    server.run(host='0.0.0.0', port=5000)

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"

# ==========================================
# ৩. UI স্ক্রিনস
# ==========================================
class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.go_login, 2.5) # 2.5 সেকেন্ড পর লগইনে যাবে

    def go_login(self, dt):
        self.manager.current = "login"

class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', padding=30)
        
        # Logo Area
        self.layout.add_widget(MDIconButton(icon="database-lock", icon_size="64sp", pos_hint={"center_x": .5}))
        self.layout.add_widget(MDLabel(text="BanglaDB Secure Access", halign="center", font_style="H5", bold=True))
        self.layout.add_widget(MDLabel(size_hint_y=None, height=dp(20)))

        # Card
        self.card = Builder.load_string('<AuthCard>:\n AuthCard:')[0] if '<AuthCard>' not in Builder.load_string(KV_CODE) else Builder.template('AuthCard')
        
        self.tf_user = MDTextField(hint_text="Username", icon_right="account")
        self.tf_pass = MDTextField(hint_text="Password", icon_right="key", password=True)
        
        self.btn_login = MDRaisedButton(text="LOGIN", size_hint_x=1, on_release=self.do_login)
        self.btn_reg = MDFlatButton(text="Create New Account", pos_hint={"center_x": .5}, on_release=self.go_reg)

        self.layout.add_widget(self.tf_user)
        self.layout.add_widget(self.tf_pass)
        self.layout.add_widget(MDLabel(size_hint_y=None, height=dp(10)))
        self.layout.add_widget(self.btn_login)
        self.layout.add_widget(self.btn_reg)
        self.layout.add_widget(MDLabel()) # Spacer

        self.add_widget(self.layout)

    def do_login(self, x):
        u, p = self.tf_user.text, self.tf_pass.text
        res, msg = engine.login_user(u, p)
        if res:
            self.manager.current = "home"
        else:
            MDDialog(text=msg, buttons=[MDFlatButton(text="TRY AGAIN", on_release=lambda x: self.dialog.dismiss())]).open()
            self.dialog = MDDialog()

    def go_reg(self, x): self.manager.current = "register"

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(MDLabel(text="Create Account", halign="center", font_style="H5"))
        
        self.tf_user = MDTextField(hint_text="New Username")
        self.tf_pass = MDTextField(hint_text="New Password", password=True)
        
        btn = MDRaisedButton(text="REGISTER", size_hint_x=1, on_release=self.do_reg)
        btn_back = MDFlatButton(text="Back to Login", pos_hint={"center_x": .5}, on_release=lambda x: setattr(self.manager, 'current', 'login'))
        
        layout.add_widget(self.tf_user)
        layout.add_widget(self.tf_pass)
        layout.add_widget(btn)
        layout.add_widget(btn_back)
        layout.add_widget(MDLabel())
        self.add_widget(layout)

    def do_reg(self, x):
        res, msg = engine.register_user(self.tf_user.text, self.tf_pass.text)
        if res: self.manager.current = "login"
        # Alert logic shortened

class ConnectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.box = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
        self.box.add_widget(MDTopAppBar(title="Server Connect", left_action_items=[["arrow-left", lambda x: self.go_home()]]))
        
        # Start Server Button
        self.btn_start = MDRaisedButton(text="START SERVER", size_hint_x=1, md_bg_color=(0, 0.7, 0, 1), on_release=self.toggle_server)
        self.box.add_widget(self.btn_start)

        # Status Label
        self.lbl_status = MDLabel(text="Server Offline", halign="center", theme_text_color="Error")
        self.box.add_widget(self.lbl_status)

        # Dropdown for DB
        self.drop_item = MDTextField(hint_text="Select Database", readonly=True, on_focus=self.open_menu)
        self.box.add_widget(self.drop_item)

        # Connect Button
        self.btn_con = MDRaisedButton(text="GENERATE CONNECTION CODE", size_hint_x=1, on_release=self.gen_code, disabled=True)
        self.box.add_widget(self.btn_con)

        # Result Area
        self.res_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
        self.scr_res = ScrollView()
        self.scr_res.add_widget(self.res_box)
        self.box.add_widget(self.scr_res)
        
        self.add_widget(self.box)

    def go_home(self): self.manager.current = "home"

    def toggle_server(self, x):
        global SERVER_RUNNING
        if not SERVER_RUNNING:
            t = threading.Thread(target=run_flask, daemon=True)
            t.start()
            SERVER_RUNNING = True
            self.lbl_status.text = f"ONLINE: {get_ip()}:5000"
            self.lbl_status.theme_text_color = "Custom"
            self.lbl_status.text_color = (0, 1, 0, 1)
            self.btn_start.disabled = True
            self.btn_con.disabled = False
        
    def open_menu(self, instance, focus):
        if not focus: return
        items = [{"viewclass": "OneLineListItem", "text": db, "on_release": lambda x=db: self.set_db(x)} for db in engine.get_databases()]
        self.menu = MDDropdownMenu(caller=self.drop_item, items=items, width_mult=4)
        self.menu.open()

    def set_db(self, db):
        self.drop_item.text = db
        self.menu.dismiss()

    def gen_code(self, x):
        if not self.drop_item.text: return
        ip = get_ip()
        user = CURRENT_USER['user']
        pw = CURRENT_USER['pass']
        db = self.drop_item.text
        
        self.res_box.clear_widgets()
        
        # Display Credentials
        info = f"HOST: {ip}:5000\nUSER: {user}\nPASS: {pw}\nDB: {db}"
        self.res_box.add_widget(MDLabel(text=info, size_hint_y=None, height=dp(80)))
        
        # Copy Code Button
        code = f"""<?php
$url = "http://{ip}:5000/api";
$data = array("user"=>"{user}", "pass"=>"{pw}", "db"=>"{db}", "action"=>"get", "table"=>"YOUR_TABLE");
$options = array("http"=>array("header"=>"Content-type: application/json", "method"=>"POST", "content"=>json_encode($data)));
$result = file_get_contents($url, false, stream_context_create($options));
echo $result;
?>"""
        btn_copy = MDRaisedButton(text="Copy PHP Code", on_release=lambda x: (Clipboard.copy(code)))
        self.res_box.add_widget(btn_copy)

# ==========================================
# ৪. মেইন অ্যাপ ক্লাস
# ==========================================
class BanglaDBApp(MDApp):
    def build(self):
        Builder.load_string(KV_CODE)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(AuthScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        
        # Home & Others (Same logic as before, stored in variable)
        self.home_scr = Screen(name="home")
        box = MDBoxLayout(orientation='vertical')
        box.add_widget(MDTopAppBar(title="BanglaDB Manager", 
            left_action_items=[["server-network", lambda x: setattr(sm, 'current', 'connect')]],
            right_action_items=[["plus", lambda x: self.diag_db()], ["logout", lambda x: self.logout(sm)]]))
        self.list_view = MDList()
        sc = ScrollView(); sc.add_widget(self.list_view)
        box.add_widget(sc)
        self.home_scr.add_widget(box)
        sm.add_widget(self.home_scr)

        # Tables & Data Screens (Simplified for brevity, assuming standard logic)
        sm.add_widget(ConnectionScreen(name="connect"))
        # Add Tables/Data screens similar to previous version...
        
        self.sm = sm
        self.load_dbs()
        return sm

    def logout(self, sm):
        global CURRENT_USER
        CURRENT_USER = None
        sm.current = "login"

    def load_dbs(self):
        self.list_view.clear_widgets()
        for db in engine.get_databases():
            item = OneLineAvatarIconListItem(text=db)
            item.add_widget(IconLeftWidget(icon="database"))
            self.list_view.add_widget(item)

    def diag_db(self):
        self.tf = MDTextField(hint_text="DB Name")
        MDDialog(title="New DB", type="custom", content_cls=self.tf, buttons=[MDRaisedButton(text="OK", on_release=lambda x: (engine.create_db(self.tf.text), self.load_dbs()))]).open()

if __name__ == "__main__":
    BanglaDBApp().run()
