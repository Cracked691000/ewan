import imaplib
import email
import re
import sqlite3
import datetime
import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
EMAIL_USER = "cassycreda@gmail.com"  # your email here
EMAIL_PASS = "ohlt rgsc eajj pnrw"  # your email app password here (not email password)
IMAP_SERVER = "imap.gmail.com"  # do not change this unless you have your own imap server
TARGET_LABEL = "cfl"  # do not change this unless you want a specific label
DB_FILE = "termux_bot.db"  # do not change this
# ---------------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ref_code TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_latest_code():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        status, messages = mail.select(TARGET_LABEL)
        if status != 'OK': return None

        status, messages = mail.search(None, '(UNSEEN)')
        email_ids = messages[0].split()
        if not email_ids: return None

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        from email.header import decode_header
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes): subject = subject.decode(encoding if encoding else "utf-8")

        print(f"📧 New Email: {subject}")
        match = re.search(r'\b\d{5,6}\b', subject)
        
        if match:
            code = match.group(0)
            print(f"✅ CODE: {code}")
            mail.store(latest_email_id, '+FLAGS', '\\Seen')
            return code
        mail.store(latest_email_id, '+FLAGS', '\\Seen')
    except: pass
    return None
    
    
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>THEO SERVICE✌️</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">

    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg: #030412;
            --card: #0a0f22;
            --text: #e6e6e6;
            --muted: #8a8a8a;
            --fire: #ff8c24;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            padding: 16px;
            padding-bottom: 60px;
            background: radial-gradient(circle at top, #050720, #000);
            color: var(--text);
            font-family: 'Orbitron', sans-serif;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
        }

        .header h1 {
            margin: 0;
            font-size: 26px;
            color: #66ffd1;
            text-shadow: 0 0 16px rgba(102,255,209,0.8);
        }

        /* CARD */
        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 16px;
            border: 1px solid #27314d;
        }

        /* LIST */
        .list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .item {
            background: #050720;
            padding: 14px 14px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 3px solid rgba(255,140,36,0.9);
            animation: flamePulse 1.6s infinite alternate;
        }

        .item:hover {
            background: rgba(255,255,255,0.04);
        }

        .coins {
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
        }

        .coins img {
            width: 22px;
            margin-right: 6px;
            animation: flicker 0.15s infinite alternate;
        }

        .code {
            font-size: 11px;
            color: var(--muted);
            text-align: right;
            letter-spacing: 0.05em;
        }

        /* ANIMATIONS */
        @keyframes flamePulse {
            from { box-shadow: 0 0 14px rgba(255,140,36,0.45); }
            to   { box-shadow: 0 0 26px rgba(255,140,36,0.9); }
        }

        @keyframes flicker {
            0% { opacity: 0.85; transform: scale(1) rotate(-1deg); }
            50% { opacity: 1; transform: scale(1.08) rotate(1deg); }
            100% { opacity: 0.9; transform: scale(1) rotate(-0.5deg); }
        }

        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: #050720;
            border-top: 1px solid #27314d;
            text-align: center;
            padding: 20px;
            font-size: 30px;
            color: var(--muted);
        }
    </style>
</head>

<body>

<div class="header">
    <h1>THEO SERVICE✌️</h1>
</div>

<div class="card">
    <div class="list">
        {% for row in grouped_data %}
        <div class="item">
            <div class="coins">
                <img src="https://i.ibb.co/XxNHnDVX/flame.png">
                {{ row[1] * 10 }} Fire Coins
            </div>
            <div class="code">
                code = {{ row[0] }}
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<div class="footer">
    24 / 7 ACTIVE 🟢
</div>

</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    
    c.execute("SELECT COUNT(*) FROM history")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM history WHERE timestamp >= datetime('now', '-1 hour')")
    rate = c.fetchone()[0]
    
    
    c.execute('''
        SELECT ref_code, COUNT(*), MAX(timestamp) 
        FROM history 
        GROUP BY ref_code 
        ORDER BY MAX(timestamp) DESC
    ''')
    grouped = c.fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, view='summary', total=total, rate=rate, grouped_data=grouped)

@app.route('/details/<code_id>')
def details(code_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    
    c.execute("SELECT COUNT(*) FROM history")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM history WHERE timestamp >= datetime('now', '-1 hour')")
    rate = c.fetchone()[0]

   
    query = f"""
        SELECT strftime('%Y-%m-%d  %I:%M %p', timestamp, 'localtime') 
        FROM history 
        WHERE ref_code = ? 
        ORDER BY timestamp DESC
    """
    c.execute(query, (code_id,))
    data = c.fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, 
                                  view='details', 
                                  total=total, 
                                  rate=rate, 
                                  selected_code=code_id, 
                                  details_data=data,
                                  details_count=len(data))

@app.route('/log-success', methods=['POST'])
def log_success():
    ref_code = request.form.get('code', 'Unknown')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (ref_code) VALUES (?)", (ref_code,))
    conn.commit()
    conn.close()
    print(f"✅ SUCCESS: {ref_code} (+10 Flames)")
    return "OK"

@app.route('/trigger-alarm', methods=['POST'])
def alarm():
    print("🚨 ALARM TRIGGERED! (No audio—check logs for captcha detection)")
    return "ALARM_REQUEST_RECEIVED"

@app.route('/get-code', methods=['GET'])
def fetch_code():
    code = get_latest_code()
    return jsonify({"code": code, "status": "found"}) if code else jsonify({"status": "waiting"})

if __name__ == '__main__':
    init_db()
    print("--- 📱 THEO SERVICE✌️ (ADVANCED) ---")
    print("")
    app.run(host='0.0.0.0', port=5000)
