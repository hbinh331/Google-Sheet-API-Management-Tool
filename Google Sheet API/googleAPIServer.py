from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
from urllib.parse import parse_qs
import gspread
from google.oauth2.service_account import Credentials
import json
import tempfile
import os
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
]

creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)


def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS USERS (username TEXT, password TEXT)')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO USERS VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def check_username(username):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM USERS WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return False
    else:
        return True

def check_user(username, password):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM USERS WHERE username = ? AND password = ?', (username, password))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return False
    else:
        return True

class RequestHandler(BaseHTTPRequestHandler):
    def is_authenticated(self):
        if "session=logged_in" in self.headers.get('Cookie', ''):
            return True
        else:
            return False

    def get_gui(self, filename, new_content, status):
        with open(filename, "r") as f:
            content = f.read()
        if new_content:
            alert = f'<div class="alert alert-{status}" role="alert">{new_content}</div>'
        else:
            alert = ''
        return content.replace('{{ALERT}}', alert).encode()

    def make_html(self, content):
        with open("dummy.html", "r", encoding='utf-8') as f:
            file = f.read()
        res = file.replace('{{CONTENT}}', content)
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='html', delete=False)
        tmp.write(res)
        tmp.close()
        return tmp.name

    def show_field(self, filename, field_to_replace1, field_to_replace2,
                   field_to_replace3, html_code1, html_code2, html_code3,
                   fetchBtn, selected_action, sheet_url, email_value, notification, notification_status):
        with open(filename, "r", encoding='utf-8') as f:
            content = f.read()
        if selected_action:
            content = content.replace(f'value="{selected_action}"', f'value="{selected_action}" selected')

        if html_code1:
            with open(html_code1, "r", encoding='utf-8') as f:
                replace_code1 = f.read()
            content = content.replace(field_to_replace1, replace_code1)
        else:
            content = content.replace(field_to_replace1, "")

        if html_code2:
            with open(html_code2, "r", encoding='utf-8') as f:
                replace_code2 = f.read()
            content = content.replace(field_to_replace2, replace_code2)
        else:
            content = content.replace(field_to_replace2, "")

        if html_code3:
            with open(html_code3, "r", encoding='utf-8') as f:
                replace_code3 = f.read()
            content = content.replace(field_to_replace3, replace_code3)
        else:
            content = content.replace(field_to_replace3, "")

        if fetchBtn == 0:
            content = content.replace('{{FETCH}}', "")
        else:
            with open('fetchButton.html', 'r', encoding='utf-8') as f:
                btn_code = f.read()
            content = content.replace("{{FETCH}}", btn_code)
        content = content.replace("{{SHEETURL}}", sheet_url if sheet_url else '')
        content = content.replace("{{EMAIL_VALUE}}", email_value if email_value else '')
        content = content.replace("{{NOTIFICATION}}", f'<div class="alert alert-{notification_status}" role="alert">{notification}</div>' if notification else '')
        return content.encode()

    def do_GET(self):
        if self.path == '/bg.jpg':
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            with open("bg.jpg", "rb") as f:
                self.wfile.write(f.read())


        if not self.is_authenticated():
            if self.path == '/register':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("register.html", "", ""))
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("login.html", "", ""))
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}",
                                             "{{UPDATENAME}}", "", "", "", 0,
                                             "", "", "","",""))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        parsed_body = parse_qs(body)
        username = parsed_body.get('username', [''])[0]
        password = parsed_body.get('password',[''])[0]
        action = parsed_body.get('action',[''])[0]
        fetch_btn = parsed_body.get('fetch',[''])[0]
        email = parsed_body.get('emailField', [''])[0].strip()
        name = parsed_body.get('nameField', [''])[0]
        sheet_url = parsed_body.get('sheetURL', [''])[0]

        if self.path == '/register':
            if not username or not password:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("register.html", "Username or password must not be empty", "danger"))
            elif check_username(username):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("register.html", "Username already existed", "warning"))
            else:
                register_user(username, password)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("login.html", "Registered successfully", "success"))
        elif self.path == '/login':
            if not username or not password:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("login.html", "Username or password must not be empty", "danger"))
            elif check_user(username, password):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Set-Cookie', 'session=logged_in; Path=/')
                self.end_headers()
                self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}",
                                                 "{{UPDATENAME}}", "", "", "", 0,
                                                 "", "", "","",""))
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(self.get_gui("login.html", "Incorrect username or password", "warning"))

        elif self.path == '/ggsheetapimain':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            if fetch_btn == 'Fetch':
                sheet_url = parsed_body.get('sheetURL', [''])[0]
                sheet_id = sheet_url.split('/d/')
                sheet_id = sheet_id[1].split('/')
                sheet_id = sheet_id[0]
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.get_worksheet(0)
                data = worksheet.get_all_records()

                match action:
                    case '1': #Create
                        row = [name, email]
                        for item in data:
                            if email == list(item.values())[1]:
                                self.wfile.write(
                                    self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                    "", "",
                                                    "", 0, action, sheet_url, "", '{"success": false}', "warning"))
                                return
                        worksheet.append_row(row)
                        self.wfile.write(
                        self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}", "", "",
                                            "", 0, action, sheet_url, "", '{"success": true}', "success"))
                    case '2': #Update
                        new_name = parsed_body.get('newName', [''])[0]
                        if not new_name: #gửi giao diện cập nhật name
                            self.wfile.write(
                                self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}", "",
                                                "", "updatename.html", 1, action, sheet_url, email, "", ""))
                        else:
                            cell = worksheet.find(email, in_column=2)
                            if cell:
                                worksheet.update_cell(cell.row, 1, new_name)
                                self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                                 "", "","",0, "", sheet_url, email,
                                                                 '{"success": true}', "success"))
                            else:               #nếu ko thấy email thì trả về false
                                self.wfile.write(
                                    self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                    "", "", "responseFalse.html", 0, "", sheet_url, email,
                                                    '{"success": false}', "warning"))
                    case '3': #Read
                        json_data = json.dumps(data)
                        newFile = self.make_html(json_data)
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                        "", "", f"{newFile}", 0, "", sheet_url, email,"",""))
                        os.remove(newFile)
                    case '4':
                        cell = worksheet.find(email, in_column=2)
                        if cell:  # nếu tìm thấy email thì thực hiện delete
                            worksheet.delete_rows(cell.row)
                            self.wfile.write(
                                self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                "", "", "", 0, "", sheet_url, email,
                                                '{"success": true}', "success"))
                        else:  # nếu ko thấy email thì trả về false
                            self.wfile.write(
                                self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                "", "", "", 0, "", sheet_url, email,
                                                '{"success": false}',"warning"))

            else:
                match action:
                    case '0':
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                         "",  "","", 0,
                                                            action, sheet_url,"", "", ""))
                    case '1': #Create
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                         "emailField.html", "nameField.html","", 1, action, sheet_url, "","",""))
                    case '2': #Update
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                         "emailField.html", None,"", 1, action, sheet_url, "", "",""))
                    case '3': #Read
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                         None, None, "", 1, action, sheet_url, "","",""))
                    case '4': #Delete
                        self.wfile.write(self.show_field("ggsheetapimain.html", "{{EMAIL}}", "{{NAME}}", "{{UPDATENAME}}",
                                                         "emailField.html", None, "", 1, action, sheet_url, "","",""))

init_db()
HOST = 'localhost'
PORT = 8000

def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = (HOST, PORT)
    httpd = server_class(server_address, handler_class)
    print("Server is running...")
    httpd.serve_forever()
    httpd.server_close()

run()

