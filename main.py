from flask import Flask, render_template_string, request, redirect, session, url_for, send_file
import csv, os
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'diogene_final_2026'

# CONFIG
ADMIN_PASSWORD = "123"
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

# HTML DESIGN
HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: sans-serif; margin: 0; background: #f4f4f9; display: flex; }
        .sidebar { width: 250px; background: #2c3e50; color: white; height: 100vh; padding: 20px; position: fixed; }
        .main { margin-left: 290px; padding: 20px; width: 100%; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); flex: 1; text-align: center; }
        .form-card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background: #3498db; color: white; }
        .btn { padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; color: white; font-weight: bold; }
        input { padding: 8px; margin: 5px 0; width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    {% if not session.logged_in %}
    <div style="width:100%; display:flex; justify-content:center; align-items:center; height:100vh; background:#2c3e50">
        <div style="background:white; padding:40px; border-radius:10px">
            <h2>🔒 DIOGENE ADMIN</h2>
            <form method="post" action="/login"><input type="password" name="pw" placeholder="Password"><button class="btn" style="background:#3498db; width:100%">LOGIN</button></form>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <h2>DIOGENE PRO</h2><hr>
        <p>Students: {{ students|length }}</p>
        <p>Total Revenue: {{ total_fees }} FRW</p>
        <form action="/logout" method="post"><button class="btn" style="background:#e74c3c; width:100%">LOGOUT</button></form>
    </div>
    <div class="main">
        <div style="display:flex; gap:20px; margin-bottom:20px">
            <div class="stat-card"><h3>STUDENTS</h3><h2>{{ students|length }}</h2></div>
            <div class="stat-card"><h3>TOTAL FEES</h3><h2>{{ total_fees }} FRW</h2></div>
            <div class="stat-card"><h3>AVG PERFORMANCE</h3><h2>{{ avg_perf }}%</h2></div>
        </div>

        <div style="display:flex; gap:20px">
            <div class="form-card" style="flex:1">
                <h3>1. New Registration</h3>
                <form action="/add" method="post">
                    <input name="name" placeholder="Name" required><input name="class" placeholder="Class" required><input name="parent" placeholder="Parent Phone">
                    <button class="btn" style="background:#27ae60">REGISTER</button>
                </form>
            </div>
            <div class="form-card" style="flex:1">
                <h3>2. Update Student (ID Based)</h3>
                <form action="/update" method="post">
                    <input name="id" placeholder="Student ID (STU-1)" required>
                    <input type="number" name="fees" placeholder="Add Fees (FRW)">
                    <input type="number" name="disc" placeholder="Minus Discipline">
                    <button class="btn" style="background:#f39c12">UPDATE STATUS</button>
                </form>
            </div>
        </div>

        <div class="form-card">
            <h3>3. Enter Academic Marks</h3>
            <form action="/marks" method="post" style="display:flex; gap:10px">
                <input name="id" placeholder="ID" required><input type="number" name="m" placeholder="Math"><input type="number" name="e" placeholder="English"><input type="number" name="p" placeholder="Physics">
                <button class="btn" style="background:#8e44ad">SAVE MARKS</button>
            </form>
        </div>

        <div class="form-card">
            <h3>Student Master Table</h3>
            <table>
                <tr><th>ID</th><th>Name</th><th>Class</th><th>Parent</th><th>Academic %</th><th>Fees</th><th>Actions</th></tr>
                {% for s in students %}
                <tr>
                    <td>{{ s.ID }}</td><td>{{ s.Name }}</td><td>{{ s.Class }}</td><td>{{ s.Parent }}</td>
                    <td>{{ ((s.Math + s.Eng + s.Phys)/3)|round(1) }}%</td><td>{{ s.Fees }} FRW</td>
                    <td><a href="/pdf/{{ s.ID }}" style="color:#8e44ad; font-weight:bold">PDF</a> | <a href="/del/{{ s.ID }}" style="color:red">Delete</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'): return render_template_string(HTML)
    data = load_csv()
    total = sum(s['Fees'] for s in data)
    perf = sum((s['Math']+s['Eng']+s['Phys'])/3 for s in data)/len(data) if data else 0
    return render_template_string(HTML, students=data, total_fees=total, avg_perf=round(perf,1))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pw') == ADMIN_PASSWORD: session['logged_in'] = True
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    data = load_csv(); new_id = f"STU-{len(data)+1}"
    data.append({"ID":new_id, "Name":request.form['name'].upper(), "Class":request.form['class'].upper(), "Parent":request.form['parent'], "Math":0, "Eng":0, "Phys":0, "Discipline":100, "Fees":0.0})
    save_csv(data); return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            if request.form['fees']: s['Fees'] += float(request.form['fees'])
            if request.form['disc']: s['Discipline'] -= int(request.form['disc'])
    save_csv(data); return redirect('/')

@app.route('/marks', methods=['POST'])
def marks():
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            s['Math']=int(request.form['m'] or 0); s['Eng']=int(request.form['e'] or 0); s['Phys']=int(request.form['p'] or 0)
    save_csv(data); return redirect('/')

@app.route('/pdf/<id>')
def pdf(id):
    s = next(x for x in load_csv() if x['ID'] == id)
    buf = BytesIO(); p = canvas.Canvas(buf)
    p.drawString(100, 800, f"REPORT CARD: {s['Name']} ({s['ID']})")
    p.drawString(100, 770, f"Class: {s['Class']} | Parent: {s['Parent']}")
    p.drawString(100, 740, f"Math: {s['Math']}% | English: {s['Eng']}% | Physics: {s['Phys']}%")
    p.drawString(100, 710, f"Discipline: {s['Discipline']}/100 | Fees: {s['Fees']} FRW")
    p.showPage(); p.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{id}.pdf")

@app.route('/del/<id>')
def delete(id):
    data = [x for x in load_csv() if x['ID'] != id]; save_csv(data); return redirect('/')

if __name__ == '__main__': app.run(debug=True)