import os
import sqlite3
import random
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'dairycare_secret_key_123'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# UltraMsg Configuration Credentials
ULTRAMSG_INSTANCE_ID = "instance190472"
ULTRAMSG_TOKEN = "pf1ljkblxznwo5"

def get_db_connection():
    conn = sqlite3.connect('dairycare.db', timeout=20)
    conn.row_factory = sqlite3.Row
    return conn
    
def init_user_table_migration():
    try:
        conn = get_db_connection()
        conn.execute('ALTER TABLE users ADD COLUMN telegram_chat_id TEXT;')
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        pass

init_user_table_migration()

def parse_calving_date(exp_date_str):
    exp_date_str = str(exp_date_str).strip()
    if not exp_date_str or exp_date_str in ['N/A', 'None', '']:
        return None
    normalized = exp_date_str.replace('/', '-')
    for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return None

def send_telegram_alert(bot_token, chat_id, cow_name, days_left):
    try:
        if not chat_id:
            return False, "no_chat_id"
        message = f"🐄 DairyCare Alert:\nगाभण गाय '{cow_name}' चे विण्यासाठी फक्त {days_left} दिवस शिल्लक आहेत. कृपया काळजी घ्या!"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": str(chat_id).strip(), "text": message}
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        ok = response.json().get('ok', False)
        return ok, (None if ok else f"api_rejected:{response.text[:200]}")
    except Exception as e:
        print(f"Telegram Exception: {e}")
        return False, f"exception:{e}"

def send_whatsapp_alert(phone_number, cow_name, days_left):
    try:
        if not phone_number:
            return False, "no_phone"
        clean_phone = "".join(filter(str.isdigit, str(phone_number)))
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"
            
        message = f"🐄 DairyCare Alert:\nगाभण गाय '{cow_name}' चे विण्यासाठी फक्त {days_left} दिवस शिल्लक आहेत. कृपया काळजी घ्या!"
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": clean_phone,
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        ok = response.status_code == 200 and '"sent":"true"' in response.text
        return ok, (None if ok else f"status_{response.status_code}:{response.text[:200]}")
    except Exception as e:
        print(f"WhatsApp Exception: {e}")
        return False, f"exception:{e}"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def home():
    if 'user_phone' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', user_phone=session['user_phone'])

@app.route('/login')
def login_page():
    if 'user_phone' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_phone', None)
    return redirect(url_for('login_page'))

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    phone = data.get('phone')
    if not phone or len(phone) != 10:
        return jsonify({'error': '१० अंकी वैध मोबाईल नंबर टाका!'}), 400
    otp = str(random.randint(1000, 9999))
    session['temp_phone'] = phone
    session['temp_otp'] = otp
    return jsonify({'message': f'तुमचा OTP आहे: {otp}'})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    entered_otp = data.get('otp')
    if entered_otp and entered_otp == session.get('temp_otp'):
        phone = session.get('temp_phone')
        session['user_phone'] = phone
        conn = get_db_connection()
        conn.execute('INSERT OR IGNORE INTO users (phone_number) VALUES (?)', (phone,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Login Successful!', 'redirect': '/'})
    else:
        return jsonify({'error': 'चुकीचा OTP! पुन्हा प्रयत्न करा.'}), 400

@app.route('/api/user/update-telegram', methods=['POST'])
def update_telegram():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    data = request.json or {}
    tg_chat_id = data.get('telegram_chat_id')
    if not tg_chat_id:
        return jsonify({'error': 'कृपया वैध Telegram Chat ID टाका!'}), 400
    try:
        conn = get_db_connection()
        conn.execute('UPDATE users SET telegram_chat_id = ? WHERE phone_number = ?', (tg_chat_id, user_phone))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Telegram Chat ID successfully updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    cows = conn.execute('SELECT * FROM cows WHERE user_phone = ?', (user_phone,)).fetchall()
    if not cows:
        cows = conn.execute('SELECT * FROM cows').fetchall()
    conn.close()
    
    total_cows = len(cows)
    pregnant_cows = 0
    upcoming_calving = 0
    today = datetime.now().date()
    for cow in cows:
        if 'pregnant' in str(cow['pregnancy_status']).strip().lower() and 'not' not in str(cow['pregnancy_status']).strip().lower():
            pregnant_cows += 1
            calving_date = parse_calving_date(cow['expected_calving_date'])
            if calving_date:
                days_rem = (calving_date - today).days
                if 0 <= days_rem <= 30:
                    upcoming_calving += 1
    return jsonify({'total': total_cows, 'pregnant': pregnant_cows, 'upcoming': upcoming_calving})

@app.route('/api/cows/all', methods=['GET'])
def get_all_cows():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    
    conn = get_db_connection()
    cows = conn.execute('SELECT * FROM cows WHERE user_phone = ? ORDER BY id DESC', (user_phone,)).fetchall()
    
    if not cows:
        clean_phone = "".join(filter(str.isdigit, str(user_phone)))[-10:]
        cows = conn.execute('SELECT * FROM cows WHERE user_phone LIKE ? ORDER BY id DESC', (f"%{clean_phone}",)).fetchall()
    
    if not cows:
        cows = conn.execute('SELECT * FROM cows ORDER BY id DESC').fetchall()
        
    conn.close()
    return jsonify([dict(cow) for cow in cows])

@app.route('/api/cow/<tag_no>', methods=['GET'])
def get_cow_details(tag_no):
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
        
    conn = get_db_connection()
    cow = conn.execute('SELECT * FROM cows WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?))', (tag_no,)).fetchone()
    conn.close()
    
    if cow is None:
        return jsonify({'error': 'या टॅगची गाय सापडली नाही!'}), 404
        
    cow_dict = dict(cow)
    days_remaining = "N/A"
    if 'pregnant' in str(cow_dict.get('pregnancy_status', '')).strip().lower():
        calving_date = parse_calving_date(cow_dict.get('expected_calving_date'))
        if calving_date:
            today = datetime.now().date()
            days_remaining = max(0, (calving_date - today).days)
        else:
            days_remaining = "Invalid Date"
            
    cow_dict['days_remaining'] = days_remaining
    return jsonify(cow_dict)

@app.route('/api/cow/add', methods=['POST'])
def add_cow():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    data = request.json or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cows (
                user_phone, tag_no, name, breed, age, pregnancy_status,
                ai_date, expected_calving_date, supplements,
                treatment_history, vaccination_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_phone, data['tag_no'], data['name'], data['breed'], data['age'],
            data['pregnancy_status'], data['ai_date'], data['expected_calving_date'],
            data['supplements'], data['treatment_history'], data['vaccination_history']
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cow record added successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'हा Tag Number आधीच वापरला आहे!'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cow/update', methods=['POST'])
def update_cow():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    data = request.json or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cows SET
                name = ?, breed = ?, age = ?, pregnancy_status = ?,
                ai_date = ?, expected_calving_date = ?, supplements = ?,
                treatment_history = ?, vaccination_history = ?
            WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?))
        ''', (
            data['name'], data['breed'], data['age'], data['pregnancy_status'],
            data['ai_date'], data['expected_calving_date'], data['supplements'],
            data['treatment_history'], data['vaccination_history'],
            data['tag_no']
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cow record updated successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cow/mark-calved/<tag_no>', methods=['POST'])
def mark_cow_calved(tag_no):
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cows SET is_calved = 1, pregnancy_status = 'Not Pregnant'
            WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?))
        ''', (tag_no,))
        conn.commit()
        conn.close()
        return jsonify({'message': '🎉 अभिनंदन! गाय विण्याच्या नोंदीचा अपडेट झाला आणि ऑटो-अलर्ट्स बंद करण्यात आले.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cow/delete/<tag_no>', methods=['DELETE'])
def delete_cow(tag_no):
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cows WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?))', (tag_no,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cow record deleted successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_report')
def download_report():
    user_phone = session.get('user_phone')
    if not user_phone:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    cows = conn.execute("SELECT * FROM cows WHERE user_phone = ?", (user_phone,)).fetchall()
    if not cows:
        cows = conn.execute("SELECT * FROM cows").fetchall()
    conn.close()

    html_content = f"""
    <html>
    <head>
        <title>DairyCare - Cow Records Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h2 {{ color: #2c3e50; text-align: center; margin-bottom: 5px; }}
            p {{ text-align: center; color: #7f8c8d; font-size: 14px; margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }}
            th {{ background-color: #27ae60; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body onload="window.print()">
        <h2>🐄 DairyCare - सर्व गाईंचे रेकॉर्ड्स</h2>
        <p>मोबाईल नंबर: {user_phone}</p>
        <table>
            <tr>
                <th>टॅग क्र.</th>
                <th>नाव</th>
                <th>जात</th>
                <th>वय</th>
                <th>गाभण स्थिती</th>
                <th>AI तारीख</th>
                <th>संभाव्य विण्याची तारीख</th>
            </tr>
    """
    for cow in cows:
        html_content += f"""
        <tr>
            <td>{cow['tag_no']}</td>
            <td>{cow['name']}</td>
            <td>{cow['breed']}</td>
            <td>{cow['age']}</td>
            <td>{cow['pregnancy_status']}</td>
            <td>{cow['ai_date'] or '-'}</td>
            <td>{cow['expected_calving_date'] or '-'}</td>
        </tr>
        """
    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content

@app.route('/api/send-calving-alerts', methods=['GET'])
def send_calving_alerts():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401

    TELEGRAM_BOT_TOKEN = "8574098006:AAEni0BSuAlLch19YhUpQSvuSJBC9Lfuos8"

    conn = get_db_connection()
    user_row = conn.execute("SELECT telegram_chat_id FROM users WHERE phone_number = ?", (user_phone,)).fetchone()
    user_tg_chat_id = user_row['telegram_chat_id'] if (user_row and user_row['telegram_chat_id']) else "6010782749"

    cows = conn.execute("SELECT * FROM cows WHERE user_phone = ?", (user_phone,)).fetchall()
    if not cows:
        cows = conn.execute("SELECT * FROM cows").fetchall()
    conn.close()

    tg_alerts = 0
    wa_alerts = 0
    wa_errors = []
    today = datetime.now().date()
    sent_tags = set()

    for r in cows:
        cow = dict(r)
        tag = str(cow.get('tag_no'))

        if cow.get('is_calved') == 1 or tag in sent_tags:
            continue

        status = str(cow.get('pregnancy_status', '')).strip().lower()
        if 'pregnant' in status and 'not' not in status:
            cow_name = cow.get('name', 'Cow')
            exp_date_str = str(cow.get('expected_calving_date', '')).strip()

            days_rem = 6
            if exp_date_str and exp_date_str not in ['N/A', 'None', '']:
                try:
                    parts = exp_date_str.replace('/', '-').split('-')
                    if len(parts) == 3:
                        if len(parts[0]) == 4:
                            c_date = datetime(int(parts[0]), int(parts[1]), int(parts[2])).date()
                        else:
                            c_date = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                        days_rem = max(0, (c_date - today).days)
                except Exception:
                    pass

            # Telegram Alert
            if send_telegram_alert(TELEGRAM_BOT_TOKEN, user_tg_chat_id, cow_name, days_rem)[0]:
                tg_alerts += 1

            # UltraMsg WhatsApp Alert
            target_phone = cow.get('user_phone') or user_phone
            wa_ok, wa_err = send_whatsapp_alert(target_phone, cow_name, days_rem)
            if wa_ok:
                wa_alerts += 1
            else:
                wa_errors.append(f"Phone {target_phone}: {wa_err}")

            sent_tags.add(tag)

    return jsonify({
        'message': f'✅ Telegram ({tg_alerts}) आणि WhatsApp ({wa_alerts}) अलर्ट यशस्वीरीत्या पाठवले!',
        'whatsapp_debug_errors': wa_errors
    })

@app.route('/api/cron/send-alerts', methods=['GET', 'POST'])
def cron_send_alerts():
    TELEGRAM_BOT_TOKEN = "8574098006:AAEni0BSuAlLch19YhUpQSvuSJBC9Lfuos8"
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM cows").fetchall()
    conn.close()

    tg_alerts = 0
    wa_alerts = 0
    today = datetime.now().date()

    for r in rows:
        cow = dict(r)
        status = str(cow.get('pregnancy_status', '')).strip().lower()
        if 'pregnant' in status and 'not' not in status and cow.get('is_calved', 0) != 1:
            owner_phone = cow.get('user_phone')
            if owner_phone:
                conn_u = get_db_connection()
                user_row = conn_u.execute("SELECT telegram_chat_id FROM users WHERE phone_number = ?", (owner_phone,)).fetchone()
                conn_u.close()

                owner_tg_id = user_row['telegram_chat_id'] if user_row and user_row['telegram_chat_id'] else "6010782749"
                cow_name = cow.get('name', 'Cow')

                calving_date = parse_calving_date(cow.get('expected_calving_date'))
                days_rem = max(0, (calving_date - today).days) if calving_date else 0

                tg_ok, _ = send_telegram_alert(TELEGRAM_BOT_TOKEN, owner_tg_id, cow_name, days_rem)
                if tg_ok:
                    tg_alerts += 1
                wa_ok, _ = send_whatsapp_alert(owner_phone, cow_name, days_rem)
                if wa_ok:
                    wa_alerts += 1

    return jsonify({'status': 'success', 'telegram_alerts_sent': tg_alerts, 'whatsapp_alerts_sent': wa_alerts}), 200

if __name__ == '__main__':
    from database import init_db
    init_db()
    app.run(host='0.0.0.0', debug=True, port=5000)
