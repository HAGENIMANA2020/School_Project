from flask import Flask, render_template_string, request, redirect, session, url_for, send_file
import csv, os
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'diogene_final_2026'

# CONFIG - USERS & PASSWORDS
PASSWORDS = {
    "ADMIN": "admin123",
    "TEACHER": "teach123",
    "BURSAR": "pay123",
    "DOS": "dos123",
    "DOD": "dod123"
}
STUDENT_FILE = 'students.csv'

def save_csv(data):
    fields = ["ID", "Name", "Class", "Parent", "Math", "Eng", "Phys", "Discipline", "Fees"]
    with open(STUDENT_FILE, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)

def load_csv():
    if not os.path.exists(STUDENT_FILE): return []
    with open(STUDENT_FILE, mode='r') as f:
        data = list(csv.DictReader(f))
        for row in data:
            row['Math'] = int(row.get('Math', 0))
            row['Eng'] = int(row.get('Eng', 0))
            row['Phys'] = int(row.get('Phys', 0))
            row['Discipline'] = int(row.get('Discipline', 100))
            row['Fees'] = float(row.get('Fees', 0.0))
        return data

# HTML DESIGN WITH ROLE-BASED ACCESS
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DIOGENE SMART SCHOOL</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; display: flex; }
        .sidebar { width: 260px; background: #1a252f; color: white; height: 100vh; padding: 25px; position: fixed; }
        .main { margin-left: 310px; padding: 25px; width: 100%; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); flex: 1; text-align: center; border-bottom: 4px solid #3498db; }
        .form-card { background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; border: 1px solid #eee; text-align: left; }
        th { background: #3498db; color: white; }
        .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: bold; }
        input { padding: 10px; margin: 8px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }
        .role-tag { background: #f39c12; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
    </style>
</head>
<body>
    {% if not session.logged_in %}
    <div style="width:100%; display:flex; justify-content:center; align-items:center; height:100vh; background:#1a252f">
        <div style="background:white; padding:40px; border-radius:15px; width: 350px;">
            <h2 style="text-align:center;">🔐 LOGIN</h2>
            <form method="post" action="/login">
                <input type="password" name="pw" placeholder="Enter System Password" required>
                <button class="btn" style="background:#3498db; width:100%; margin-top:15px">ACCESS DASHBOARD</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <h2 style="color:#3498db">DIOGENE PRO</h2>
        <span class="role-tag">ROLE: {{ session.role }}</span>
        <hr style="border:0.5px solid #34495e; margin: 20px 0;">
        <p>Students: <b>{{ students|length }}</b></p>
        <form action="/logout" method="post"><button class="btn" style="background:#e74c3c; width:100%">LOGOUT</button></form>
    </div>

    <div class="main">
        <h2>Welcome to {{ session.role }} Dashboard</h2>
        
        <div style="display:flex; gap:25px; margin-bottom:30px">
            <div class="stat-card"><h3>STUDENTS</h3><h2>{{ students|length }}</h2></div>
            {% if session.role in ['ADMIN', 'BURSAR'] %}
            <div class="stat-card"><h3>REVENUE</h3><h2>{{ "{:,.0f}".format(total_fees) }} FRW</h2></div>
            {% endif %}
            <div class="stat-card"><h3>AVG PERF</h3><h2>{{ avg_perf }}%</h2></div>
        </div>

        <div style="display:flex; gap:25px">
            {# 1. REGISTRATION - ADMIN, DOS #}
            {% if session.role in ['ADMIN', 'DOS'] %}
            <div class="form-card" style="flex:1">
                <h3 style="color:#27ae60">Student Registration</h3>
                <form action="/add" method="post">
                    <input name="name" placeholder="Full Name" required>
                    <input name="class" placeholder="Class" required>
                    <input name="parent" placeholder="Parent Phone">
                    <button class="btn" style="background:#27ae60; width:100%">REGISTER</button>
                </form>
            </div>
            {% endif %}

            {# 2. FEES & DISCIPLINE - BURSAR, DOD, ADMIN #}
            {% if session.role in ['ADMIN', 'BURSAR', 'DOD'] %}
            <div class="form-card" style="flex:1">
                <h3 style="color:#f39c12">Fees & Discipline</h3>
                <form action="/update" method="post">
                    <input name="id" placeholder="Student ID (STU-1)" required>
                    {% if session.role in ['ADMIN', 'BURSAR'] %}
                    <input type="number" name="fees" placeholder="Add Fees Paid (FRW)">
                    {% endif %}
                    {% if session.role in ['ADMIN', 'DOD'] %}
                    <input type="number" name="disc" placeholder="Discipline Marks Deduction">
                    {% endif %}
                    <button class="btn" style="background:#f39c12; width:100%">UPDATE STUDENT</button>
                </form>
            </div>
            {% endif %}
        </div>

        {# 3. MARKS - TEACHER, DOS, ADMIN #}
        {% if session.role in ['ADMIN', 'TEACHER', 'DOS'] %}
        <div class="form-card">
            <h3 style="color:#8e44ad">Academic Marks Entry</h3>
            <form action="/marks" method="post" style="display:flex; gap:15px">
                <input name="id" placeholder="ID" required style="flex:1">
                <input type="number" name="m" placeholder="Math" style="flex:1">
                <input type="number" name="e" placeholder="English" style="flex:1">
                <input type="number" name="p" placeholder="Physics" style="flex:1">
                <button class="btn" style="background:#8e44ad">SAVE Amanota</button>
            </form>
        </div>
        {% endif %}

        <div class="form-card">
            <h3>Student Records</h3>
            <table>
                <tr>
                    <th>ID</th><th>Name</th><th>Class</th><th>Avg %</th>
                    {% if session.role in ['ADMIN', 'DOD'] %}<th>Disc.</th>{% endif %}
                    {% if session.role in ['ADMIN', 'BURSAR'] %}<th>Fees</th>{% endif %}
                    <th>Actions</th>
                </tr>
                {% for s in students %}
                <tr>
                    <td><b>{{ s.ID }}</b></td>
                    <td>{{ s.Name }}</td>
                    <td>{{ s.Class }}</td>
                    {% set avg = ((s.Math + s.Eng + s.Phys)/3)|round(1) %}
                    <td><span class="badge" style="background:{% if avg >= 50 %}#27ae60{% else %}#e74c3c{% endif %}">{{ avg }}%</span></td>
                    {% if session.role in ['ADMIN', 'DOD'] %}<td>{{ s.Discipline }}/100</td>{% endif %}
                    {% if session.role in ['ADMIN', 'BURSAR'] %}<td>{{ "{:,.0f}".format(s.Fees) }} FRW</td>{% endif %}
                    <td>
                        <a href="/pdf/{{ s.ID }}">📄 PDF</a>
                        {% if session.role == 'ADMIN' %} | <a href="/del/{{ s.ID }}" style="color:red">Delete</a>{% endif %}
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

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template_string(HTML)
    data = load_csv()
    total = sum(s['Fees'] for s in data)
    perf = sum((s['Math']+s['Eng']+s['Phys'])/3 for s in data)/len(data) if data else 0
    return render_template_string(HTML, students=data, total_fees=total, avg_perf=round(perf,1))

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('pw')
    for role, password in PASSWORDS.items():
        if pw == password:
            session['logged_in'] = True
            session['role'] = role
            return redirect('/')
    return "Password Itariyo! Gerageza: admin123, teach123, pay123, dos123, cyangwa dod123"

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    if session.get('role') not in ['ADMIN', 'DOS']: return "No Permission", 403
    data = load_csv()
    new_id = f"STU-{len(data)+1}"
    data.append({"ID":new_id, "Name":request.form['name'].upper(), "Class":request.form['class'].upper(), "Parent":request.form['parent'], "Math":0, "Eng":0, "Phys":0, "Discipline":100, "Fees":0.0})
    save_csv(data); return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    if session.get('role') not in ['ADMIN', 'BURSAR', 'DOD']: return "No Permission", 403
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            if request.form.get('fees') and session['role'] in ['ADMIN', 'BURSAR']: 
                s['Fees'] += float(request.form['fees'])
            if request.form.get('disc') and session['role'] in ['ADMIN', 'DOD']: 
                s['Discipline'] = max(0, s['Discipline'] - int(request.form['disc']))
    save_csv(data); return redirect('/')

@app.route('/marks', methods=['POST'])
def marks():
    if session.get('role') not in ['ADMIN', 'TEACHER', 'DOS']: return "No Permission", 403
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            s['Math']=int(request.form['m'] or 0); s['Eng']=int(request.form['e'] or 0); s['Phys']=int(request.form['p'] or 0)
    save_csv(data); return redirect('/')

@app.route('/pdf/<id>')
def pdf(id):
    s = next(x for x in load_csv() if x['ID'] == id)
    buf = BytesIO(); p = canvas.Canvas(buf)
    p.drawString(100, 800, f"REPORT CARD: {s['Name']}")
    p.drawString(100, 780, f"Role Generated: {session.get('role')}")
    p.drawString(100, 750, f"Math: {s['Math']}% | Eng: {s['Eng']}% | Phys: {s['Phys']}%")
    p.showPage(); p.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{id}.pdf")

@app.route('/del/<id>')
def delete(id):
    if session.get('role') != 'ADMIN': return "Admin Only", 403
    data = [x for x in load_csv() if x['ID'] != id]; save_csv(data); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)