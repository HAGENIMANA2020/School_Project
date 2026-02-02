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

# HTML DESIGN (Added more professional styling)
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DIOGENE SCHOOL PRO</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; display: flex; }
        .sidebar { width: 260px; background: #1a252f; color: white; height: 100vh; padding: 25px; position: fixed; }
        .main { margin-left: 310px; padding: 25px; width: 100%; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); flex: 1; text-align: center; border-bottom: 4px solid #3498db; }
        .form-card { background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; border: 1px solid #eee; text-align: left; }
        th { background: #3498db; color: white; font-weight: 600; }
        tr:hover { background: #f9f9f9; }
        .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: bold; transition: 0.3s; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        input { padding: 10px; margin: 8px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }
    </style>
</head>
<body>
    {% if not session.logged_in %}
    <div style="width:100%; display:flex; justify-content:center; align-items:center; height:100vh; background:#1a252f">
        <div style="background:white; padding:40px; border-radius:15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 350px;">
            <h2 style="text-align:center; color:#1a252f">🔒 DIOGENE ADMIN</h2>
            <p style="text-align:center; color:#666">Enter credentials to manage system</p>
            <form method="post" action="/login">
                <input type="password" name="pw" placeholder="Password" required>
                <button class="btn" style="background:#3498db; width:100%; margin-top:15px">LOGIN TO SYSTEM</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <h2 style="color:#3498db">DIOGENE PRO</h2>
        <p style="color:#bdc3c7">ELT Management v1.0</p>
        <hr style="border:0.5px solid #34495e; margin: 20px 0;">
        <div style="margin-bottom: 30px;">
            <p>Active Students: <b>{{ students|length }}</b></p>
            <p>Total Revenue: <b>{{ "{:,.0f}".format(total_fees) }} FRW</b></p>
        </div>
        <form action="/logout" method="post"><button class="btn" style="background:#e74c3c; width:100%">LOGOUT</button></form>
    </div>
    <div class="main">
        <div style="display:flex; gap:25px; margin-bottom:30px">
            <div class="stat-card"><h3>TOTAL STUDENTS</h3><h2 style="color:#2c3e50">{{ students|length }}</h2></div>
            <div class="stat-card"><h3>COLLECTED FEES</h3><h2 style="color:#27ae60">{{ "{:,.0f}".format(total_fees) }} FRW</h2></div>
            <div class="stat-card"><h3>AVG PERFORMANCE</h3><h2 style="color:#8e44ad">{{ avg_perf }}%</h2></div>
        </div>

        <div style="display:flex; gap:25px">
            <div class="form-card" style="flex:1">
                <h3 style="color:#27ae60">1. New Registration</h3>
                <form action="/add" method="post">
                    <input name="name" placeholder="Full Name" required>
                    <input name="class" placeholder="Class (e.g., L3 ELT)" required>
                    <input name="parent" placeholder="Parent Contact">
                    <button class="btn" style="background:#27ae60; width:100%; margin-top:10px">REGISTER STUDENT</button>
                </form>
            </div>
            <div class="form-card" style="flex:1">
                <h3 style="color:#f39c12">2. Financial & Discipline</h3>
                <form action="/update" method="post">
                    <input name="id" placeholder="Student ID (e.g., STU-1)" required>
                    <input type="number" name="fees" placeholder="Add Fees (FRW)">
                    <input type="number" name="disc" placeholder="Deduct Discipline Marks">
                    <button class="btn" style="background:#f39c12; width:100%; margin-top:10px">UPDATE STATUS</button>
                </form>
            </div>
        </div>

        <div class="form-card">
            <h3 style="color:#8e44ad">3. Enter Academic Marks</h3>
            <form action="/marks" method="post" style="display:flex; gap:15px">
                <input name="id" placeholder="ID" required style="flex:1">
                <input type="number" name="m" placeholder="Math" style="flex:1">
                <input type="number" name="e" placeholder="English" style="flex:1">
                <input type="number" name="p" placeholder="Physics" style="flex:1">
                <button class="btn" style="background:#8e44ad">SAVE MARKS</button>
            </form>
        </div>

        <div class="form-card">
            <h3>Student Master Records</h3>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Class</th>
                    <th>Avg %</th>
                    <th>Disc.</th>
                    <th>Fees Paid</th>
                    <th>Actions</th>
                </tr>
                {% for s in students %}
                <tr>
                    <td><b>{{ s.ID }}</b></td>
                    <td>{{ s.Name }}</td>
                    <td><span class="badge" style="background:#34495e">{{ s.Class }}</span></td>
                    {% set avg = ((s.Math + s.Eng + s.Phys)/3)|round(1) %}
                    <td>
                        <span class="badge" style="background:{% if avg >= 50 %}#27ae60{% else %}#e74c3c{% endif %}">
                            {{ avg }}%
                        </span>
                    </td>
                    <td>{{ s.Discipline }}/100</td>
                    <td>{{ "{:,.0f}".format(s.Fees) }} FRW</td>
                    <td>
                        <a href="/pdf/{{ s.ID }}" style="text-decoration:none; color:#8e44ad; margin-right:10px">📄 PDF</a> 
                        <a href="/del/{{ s.ID }}" style="text-decoration:none; color:#e74c3c" onclick="return confirm('Delete this student?')">🗑️ Del</a>
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
    if request.form.get('pw') == ADMIN_PASSWORD: session['logged_in'] = True
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout(): session.clear(); return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    data = load_csv()
    new_id = f"STU-{len(data)+1}"
    data.append({
        "ID":new_id, "Name":request.form['name'].upper(), "Class":request.form['class'].upper(), 
        "Parent":request.form['parent'], "Math":0, "Eng":0, "Phys":0, "Discipline":100, "Fees":0.0
    })
    save_csv(data); return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            if request.form['fees']: s['Fees'] += float(request.form['fees'])
            if request.form['disc']: s['Discipline'] = max(0, s['Discipline'] - int(request.form['disc']))
    save_csv(data); return redirect('/')

@app.route('/marks', methods=['POST'])
def marks():
    data = load_csv(); s_id = request.form['id'].upper()
    for s in data:
        if s['ID'] == s_id:
            s['Math']=int(request.form['m'] or 0)
            s['Eng']=int(request.form['e'] or 0)
            s['Phys']=int(request.form['p'] or 0)
    save_csv(data); return redirect('/')

@app.route('/pdf/<id>')
def pdf(id):
    s = next(x for x in load_csv() if x['ID'] == id)
    buf = BytesIO(); p = canvas.Canvas(buf)
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "DIOGENE SCHOOL MANAGEMENT SYSTEM")
    p.setFont("Helvetica", 12)
    p.drawString(100, 785, "---------------------------------------------------------")
    
    # Student Info
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 750, f"OFFICIAL REPORT CARD: {s['Name']}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Student ID: {s['ID']} | Class: {s['Class']}")
    p.drawString(100, 715, f"Parent Contact: {s['Parent']}")
    
    # Marks Table-like
    p.drawString(100, 680, "ACADEMIC PERFORMANCE:")
    p.drawString(120, 660, f"Mathematics: {s['Math']}%")
    p.drawString(120, 640, f"English Language: {s['Eng']}%")
    p.drawString(120, 620, f"Physics: {s['Phys']}%")
    
    # Summary
    avg = (s['Math'] + s['Eng'] + s['Phys']) / 3
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 590, f"FINAL AVERAGE: {round(avg, 1)}%")
    p.drawString(100, 570, f"DISCIPLINE SCORE: {s['Discipline']}/100")
    
    # Financial
    p.setFont("Helvetica", 12)
    p.drawString(100, 540, f"FEES STATUS: Paid {s['Fees']} FRW")
    
    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 100, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 85, "Authorized signature: ______________________")
    
    p.showPage(); p.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"Report_{s['Name']}.pdf")

@app.route('/del/<id>')
def delete(id):
    data = [x for x in load_csv() if x['ID'] != id]
    save_csv(data); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)