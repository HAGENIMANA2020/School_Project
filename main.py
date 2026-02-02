from flask import Flask, render_template_string, request, redirect, session, url_for, send_file
import csv, os
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'diogene_master_key_2026'

# FILES
STUDENT_FILE = 'students.csv'
USER_FILE = 'users.csv'

# --- DATABASE LOGIC ---
def load_users():
    if not os.path.exists(USER_FILE):
        admin = [{"username": "admin", "password": "123", "role": "ADMIN", "status": "ACTIVE"}]
        save_users(admin)
        return admin
    with open(USER_FILE, mode='r') as f:
        return list(csv.DictReader(f))

def save_users(users):
    fields = ["username", "password", "role", "status"]
    with open(USER_FILE, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(users)

def load_students():
    if not os.path.exists(STUDENT_FILE): return []
    with open(STUDENT_FILE, mode='r') as f:
        data = list(csv.DictReader(f))
        for r in data:
            r['Math'] = int(r.get('Math', 0)); r['Eng'] = int(r.get('Eng', 0))
            r['Phys'] = int(r.get('Phys', 0)); r['Fees'] = float(r.get('Fees', 0.0))
            r['Discipline'] = int(r.get('Discipline', 100))
        return data

def save_students(data):
    fields = ["ID", "Name", "Class", "Parent", "Math", "Eng", "Phys", "Discipline", "Fees", "Status"]
    with open(STUDENT_FILE, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(data)

# --- HTML MASTER UI ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DIOGENE SCHOOL PRO v2.0</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; display: flex; }
        .sidebar { width: 260px; background: #1a252f; color: white; height: 100vh; padding: 25px; position: fixed; }
        .main { margin-left: 310px; padding: 25px; width: calc(100% - 350px); }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
        input, select { padding: 10px; margin: 5px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .btn { padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: bold; text-decoration: none; display: inline-block; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px; border: 1px solid #eee; text-align: left; }
        th { background: #3498db; color: white; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; color: white; font-weight: bold; }
    </style>
</head>
<body>
    {% if not session.logged_in %}
    <div style="width:100%; height:100vh; display:flex; justify-content:center; align-items:center; background:#1a252f">
        <div class="card" style="width:350px">
            <h2 style="text-align:center">🔒 DIOGENE PRO LOGIN</h2>
            <form method="post" action="/login">
                <input name="un" placeholder="Username" required>
                <input type="password" name="pw" placeholder="Password" required>
                <button class="btn" style="background:#3498db; width:100%; margin-top:10px">LOGIN</button>
            </form>
            <p style="text-align:center; font-size:14px">New Staff? <a href="/register_page">Register Account</a></p>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <h2 style="color:#3498db">DIOGENE PRO</h2>
        <p>User: <b>{{ session.user }}</b></p>
        <p>Role: <span class="badge" style="background:#f39c12">{{ session.role }}</span></p>
        <hr style="border:0.5px solid #34495e; margin:20px 0;">
        <a href="/" class="btn" style="background:#34495e; width:100%; margin-bottom:10px">Dashboard</a>
        <form action="/logout" method="post"><button class="btn" style="background:#e74c3c; width:100%">LOGOUT</button></form>
    </div>

    <div class="main">
        <h1>Dashboard - {{ session.role }}</h1>

        {% if session.role == 'ADMIN' %}
        <div class="card">
            <h3>Staff Activation (Users)</h3>
            <table>
                <tr><th>Username</th><th>Role</th><th>Status</th><th>Action</th></tr>
                {% for u in users %}{% if u.username != 'admin' %}
                <tr>
                    <td>{{ u.username }}</td><td>{{ u.role }}</td>
                    <td><span class="badge" style="background:{{ '#27ae60' if u.status=='ACTIVE' else '#e74c3c' }}">{{ u.status }}</span></td>
                    <td>{% if u.status == 'INACTIVE' %}<a href="/activate_user/{{ u.username }}" class="btn" style="background:#2ecc71; font-size:11px">ACTIVATE</a>{% endif %}</td>
                </tr>
                {% endif %}{% endfor %}
            </table>
        </div>
        {% endif %}

        <div style="display:flex; gap:20px">
            <div class="card" style="flex:1">
                <h3 style="color:#27ae60">1. Student Registration</h3>
                <form action="/add_student" method="post">
                    <input name="name" placeholder="Full Name" required>
                    <input name="class" placeholder="Class" required>
                    <input name="parent" placeholder="Parent Contact">
                    <button class="btn" style="background:#27ae60; width:100%">REGISTER (PENDING)</button>
                </form>
            </div>

            {% if session.role in ['ADMIN', 'BURSAR', 'DOD'] %}
            <div class="card" style="flex:1">
                <h3 style="color:#f39c12">2. Fees & Discipline</h3>
                <form action="/update_student" method="post">
                    <input name="id" placeholder="Student ID (e.g., STU-1)" required>
                    {% if session.role in ['ADMIN', 'BURSAR'] %}<input type="number" name="fees" placeholder="Add Fees Paid">{% endif %}
                    {% if session.role in ['ADMIN', 'DOD'] %}<input type="number" name="disc" placeholder="Deduct Discipline Marks">{% endif %}
                    <button class="btn" style="background:#f39c12; width:100%">UPDATE DATA</button>
                </form>
            </div>
            {% endif %}
        </div>

        {% if session.role in ['ADMIN', 'TEACHER', 'DOS'] %}
        <div class="card">
            <h3 style="color:#8e44ad">3. Academic Marks Entry</h3>
            <form action="/marks" method="post" style="display:flex; gap:10px">
                <input name="id" placeholder="ID" required style="flex:1">
                <input type="number" name="m" placeholder="Math" style="flex:1">
                <input type="number" name="e" placeholder="English" style="flex:1">
                <input type="number" name="p" placeholder="Physics" style="flex:1">
                <button class="btn" style="background:#8e44ad">SAVE MARKS</button>
            </form>
        </div>
        {% endif %}

        <div class="card">
            <h3>Student Master Records</h3>
            <table>
                <tr><th>ID</th><th>Name</th><th>Class</th><th>Avg %</th><th>Fees</th><th>Status</th><th>Actions</th></tr>
                {% for s in students %}
                <tr>
                    <td><b>{{ s.ID }}</b></td><td>{{ s.Name }}</td><td>{{ s.Class }}</td>
                    {% set avg = ((s.Math + s.Eng + s.Phys)/3)|round(1) %}
                    <td>{{ avg }}%</td><td>{{ "{:,.0f}".format(s.Fees) }} FRW</td>
                    <td><span class="badge" style="background:{{ '#27ae60' if s.Status=='APPROVED' else '#f39c12' }}">{{ s.Status }}</span></td>
                    <td>
                        {% if session.role == 'ADMIN' and s.Status == 'PENDING' %}
                        <a href="/approve_student/{{ s.ID }}" class="btn" style="background:#2ecc71; font-size:11px">APPROVE</a>
                        {% endif %}
                        {% if s.Status == 'APPROVED' %}<a href="/pdf/{{ s.ID }}" style="color:#8e44ad">📄 PDF</a>{% endif %}
                        {% if session.role == 'ADMIN' %} | <a href="/del/{{ s.ID }}" style="color:red; font-size:11px">Del</a>{% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

REG_HTML = """
<div style="width:100%; height:100vh; display:flex; justify-content:center; align-items:center; background:#1a252f; font-family:sans-serif">
    <div style="background:white; padding:30px; border-radius:10px; width:350px">
        <h2 style="text-align:center">Staff Registration</h2>
        <form method="post" action="/register">
            <input name="un" placeholder="Choose Username" required style="width:100%; padding:10px; margin:5px 0">
            <input type="password" name="pw" placeholder="Create Password" required style="width:100%; padding:10px; margin:5px 0">
            <select name="role" style="width:100%; padding:10px; margin:5px 0">
                <option value="TEACHER">TEACHER</option><option value="BURSAR">BURSAR</option>
                <option value="DOS">DOS</option><option value="DOD">DOD</option>
            </select>
            <button style="background:#27ae60; color:white; border:none; padding:12px; width:100%; border-radius:5px; margin-top:10px; cursor:pointer">REGISTER</button>
        </form>
        <p style="text-align:center"><a href="/">Back to Login</a></p>
    </div>
</div>
"""

# --- ROUTES LOGIC ---
@app.route('/')
def index():
    if not session.get('logged_in'): return render_template_string(HTML)
    return render_template_string(HTML, students=load_students(), users=load_users())

@app.route('/register_page')
def register_page(): return REG_HTML

@app.route('/register', methods=['POST'])
def register():
    users = load_users()
    un = request.form['un'].lower()
    if any(u['username'] == un for u in users): return "Username exists!"
    users.append({"username": un, "password": request.form['pw'], "role": request.form['role'], "status": "INACTIVE"})
    save_users(users); return "Success! Wait for Admin Activation. <a href='/'>Go Back</a>"

@app.route('/login', methods=['POST'])
def login():
    un = request.form['un'].lower(); pw = request.form['pw']; users = load_users()
    for u in users:
        if u['username'] == un and u['password'] == pw:
            if u['status'] == 'ACTIVE':
                session['logged_in'] = True; session['user'] = un; session['role'] = u['role']
                return redirect('/')
            return "Account is INACTIVE!"
    return "Invalid Credentials!"

@app.route('/activate_user/<un>')
def activate_user(un):
    if session.get('role') != 'ADMIN': return "Unauthorized", 403
    users = load_users(); [u.update({"status": "ACTIVE"}) for u in users if u['username'] == un]
    save_users(users); return redirect('/')

@app.route('/add_student', methods=['POST'])
def add_student():
    data = load_students(); new_id = f"STU-{len(data)+1}"
    data.append({"ID":new_id, "Name":request.form['name'].upper(), "Class":request.form['class'].upper(), "Status":"PENDING", "Math":0, "Eng":0, "Phys":0, "Fees":0.0, "Discipline":100, "Parent":request.form['parent']})
    save_students(data); return redirect('/')

@app.route('/approve_student/<id>')
def approve_student(id):
    if session.get('role') != 'ADMIN': return "Unauthorized", 403
    data = load_students(); [s.update({"Status": "APPROVED"}) for s in data if s['ID'] == id]
    save_students(data); return redirect('/')

@app.route('/update_student', methods=['POST'])
def update_student():
    data = load_students(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            if request.form.get('fees') and session['role'] in ['ADMIN', 'BURSAR']: s['Fees'] += float(request.form['fees'])
            if request.form.get('disc') and session['role'] in ['ADMIN', 'DOD']: s['Discipline'] = max(0, s['Discipline'] - int(request.form['disc']))
    save_students(data); return redirect('/')

@app.route('/marks', methods=['POST'])
def marks():
    data = load_students(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            s['Math']=int(request.form['m'] or 0); s['Eng']=int(request.form['e'] or 0); s['Phys']=int(request.form['p'] or 0)
    save_students(data); return redirect('/')

@app.route('/pdf/<id>')
def pdf(id):
    s = next(x for x in load_students() if x['ID'] == id)
    buf = BytesIO(); p = canvas.Canvas(buf)
    p.drawString(100, 800, f"REPORT CARD: {s['Name']}")
    p.drawString(100, 770, f"Class: {s['Class']} | Avg: {round((s['Math']+s['Eng']+s['Phys'])/3,1)}%")
    p.drawString(100, 750, f"Fees Paid: {s['Fees']} FRW | Discipline: {s['Discipline']}/100")
    p.showPage(); p.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{id}.pdf")

@app.route('/del/<id>')
def delete(id):
    if session.get('role') != 'ADMIN': return "Admin Only", 403
    data = [x for x in load_students() if x['ID'] != id]; save_students(data); return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)