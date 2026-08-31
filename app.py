import os
import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'dairycare_secret_key_123'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_connection():
    db_path = os.path.join(BASE_DIR, 'dairycare.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Favicon Error 404 घालवण्यासाठी
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

# 1. Send OTP API (Direct Alert / Pop-up Mode)
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    phone = data.get('phone')
    if not phone or len(phone) != 10:
        return jsonify({'error': '१० अंकी वैध मोबाईल नंबर टाका!'}), 400

    otp = str(random.randint(1000, 9999))
    session['temp_phone'] = phone
    session['temp_otp'] = otp

    print(f"\n==============================")
    print(f"  📲 LOGIN OTP FOR {phone} : {otp}")
    print(f"==============================\n")

    return jsonify({'message': f'तुमचा OTP आहे: {otp}'})

# 2. Verify OTP API
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

# 3. Dashboard Summary Stats API
@app.route('/api/stats', methods=['GET'])
def get_stats():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    cows = conn.execute('SELECT * FROM cows WHERE user_phone = ?', (user_phone,)).fetchall()
    conn.close()

    total_cows = len(cows)
    pregnant_cows = 0
    upcoming_calving = 0
    today = datetime.now()

    for cow in cows:
        if cow['pregnancy_status'] == 'Pregnant':
            pregnant_cows += 1
            if cow['expected_calving_date'] and cow['expected_calving_date'] != 'N/A':
                try:
                    calving_date = datetime.strptime(cow['expected_calving_date'], '%Y-%m-%d')
                    days_rem = (calving_date - today).days
                    if 0 <= days_rem <= 30:
                        upcoming_calving += 1
                except ValueError:
                    pass

    return jsonify({
        'total': total_cows,
        'pregnant': pregnant_cows,
        'upcoming': upcoming_calving
    })

# 4. Get All Cows
@app.route('/api/cows/all', methods=['GET'])
def get_all_cows():
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401

    conn = get_db_connection()
    cows = conn.execute('SELECT * FROM cows WHERE user_phone = ? ORDER BY id DESC', (user_phone,)).fetchall()
    conn.close()

    return jsonify([dict(cow) for cow in cows])

# 5. Search Cow API
@app.route('/api/cow/<tag_no>', methods=['GET'])
def get_cow_details(tag_no):
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401

    conn = get_db_connection()
    cow = conn.execute('SELECT * FROM cows WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?)) AND user_phone = ?', (tag_no, user_phone)).fetchone()
    conn.close()

    if cow is None:
        return jsonify({'error': 'तुमच्या अकाउंटवर या टॅगची गाय सापडली नाही!'}), 404

    cow_dict = dict(cow)
    days_remaining = "N/A"
    if cow_dict.get('expected_calving_date') and cow_dict['pregnancy_status'] == 'Pregnant':
        try:
            calving_date = datetime.strptime(cow_dict['expected_calving_date'], '%Y-%m-%d')
            today = datetime.now()
            delta = (calving_date - today).days
            days_remaining = max(0, delta)
        except ValueError:
            days_remaining = "Invalid Date"

    cow_dict['days_remaining'] = days_remaining
    return jsonify(cow_dict)

# 6. Add Cow API
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

# 7. Update Cow API
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
            WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?)) AND user_phone = ?
        ''', (
            data['name'], data['breed'], data['age'], data['pregnancy_status'],
            data['ai_date'], data['expected_calving_date'], data['supplements'],
            data['treatment_history'], data['vaccination_history'],
            data['tag_no'], user_phone
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cow record updated successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 8. Delete Cow API
@app.route('/api/cow/delete/<tag_no>', methods=['DELETE'])
def delete_cow(tag_no):
    user_phone = session.get('user_phone')
    if not user_phone:
        return jsonify({'error': 'कृपया आधी लॉगिन करा!'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cows WHERE UPPER(TRIM(tag_no)) = UPPER(TRIM(?)) AND user_phone = ?', (tag_no, user_phone))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()

        if rows_deleted == 0:
            return jsonify({'error': 'हा टॅग नंबर डेटाबेसमध्ये सापडला नाही!'}), 404

        return jsonify({'message': 'Cow record deleted successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from database import init_db
    init_db()
    app.run(host='0.0.0.0', debug=True, port=5000)