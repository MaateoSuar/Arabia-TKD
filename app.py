from flask import Flask, jsonify, request, render_template, send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime, date
import os

app = Flask(__name__)

# --- In-memory data stores (pueden reemplazarse por DB real más adelante) ---
students = []
calendar_events = []  # {id, date, title, type: 'general' | 'exam', notes}
fees = []  # {student_id, status, last_payment, history: [...]} 
exams = []  # {id, date, time, level, place, notes}


@app.route('/')
def index():
    return render_template('index.html')


# --- Students CRUD ---
@app.route('/api/students', methods=['GET', 'POST'])
def api_students():
    if request.method == 'GET':
        ordered = sorted(students, key=lambda s: (s.get('last_name','').lower(), s.get('first_name','').lower()))
        return jsonify(ordered)

    data = request.json or {}
    data['id'] = len(students) + 1
    students.append(data)
    return jsonify(data), 201


@app.route('/api/students/<int:student_id>', methods=['GET', 'PUT', 'DELETE'])
def api_student_detail(student_id: int):
    student = next((s for s in students if s['id'] == student_id), None)
    if not student:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if request.method == 'GET':
        return jsonify(student)

    if request.method == 'PUT':
        data = request.json or {}
        student.update(data)
        return jsonify(student)

    if request.method == 'DELETE':
        students.remove(student)
        return '', 204


# --- Calendar & Exams ---
@app.route('/api/events', methods=['GET', 'POST'])
def api_events():
    if request.method == 'GET':
        return jsonify(calendar_events)

    data = request.json or {}
    data['id'] = len(calendar_events) + 1
    calendar_events.append(data)
    if data.get('type') == 'exam':
        exams.append({
            'id': data['id'],
            'date': data.get('date'),
            'time': data.get('time'),
            'level': data.get('level'),
            'place': data.get('place'),
            'notes': data.get('notes'),
        })
    return jsonify(data), 201


@app.route('/api/events/<int:event_id>', methods=['GET'])
def api_event_detail(event_id: int):
    event = next((e for e in calendar_events if e['id'] == event_id), None)
    if not event:
        return jsonify({'error': 'Evento no encontrado'}), 404
    return jsonify(event)


# --- Fees ---
@app.route('/api/fees/<int:student_id>', methods=['GET', 'POST'])
def api_fees(student_id: int):
    record = next((f for f in fees if f['student_id'] == student_id), None)

    if request.method == 'GET':
        if not record:
            return jsonify({'student_id': student_id, 'status': 'sin_registro', 'history': []})

        # Recalcular estado en base a la fecha del último pago
        try:
            last_dt = datetime.strptime(record.get('last_payment', ''), '%Y-%m-%d').date()
        except ValueError:
            last_dt = None

        today = date.today()
        if last_dt is None:
            status = 'sin_registro'
        else:
            delta_days = (today - last_dt).days
            status = 'al_dia' if delta_days <= 30 else 'vencida'

        record['status'] = status
        return jsonify(record)

    data = request.json or {}
    payment_date = data.get('payment_date') or datetime.now().strftime('%Y-%m-%d')
    amount = data.get('amount', 0)

    if not record:
        record = {
            'student_id': student_id,
            'status': 'al_dia',  # se recalcula dinámicamente en GET
            'last_payment': payment_date,
            'history': [],
        }
        fees.append(record)

    record['history'].append({'date': payment_date, 'amount': amount})
    record['last_payment'] = payment_date
    # El estado real se recalcula en el GET; aquí devolvemos el registro actualizado
    return jsonify(record)


# --- PDF generation for exam inscription ---
@app.route('/api/exams/<int:event_id>/inscription-pdf', methods=['POST'])
def generate_exam_pdf(event_id: int):
    event = next((e for e in calendar_events if e['id'] == event_id and e.get('type') == 'exam'), None)
    if not event:
        return jsonify({'error': 'Examen no encontrado'}), 404

    student = None
    data = request.json or {}
    student_id = data.get('student_id')
    if student_id is not None:
        student = next((s for s in students if s['id'] == student_id), None)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Fondo simple tipo "marcial"
    p.setFillColorRGB(0, 0, 0)
    p.rect(0, 0, width, height, fill=1, stroke=0)

    # Marco blanco
    margin = 40
    p.setFillColorRGB(1, 1, 1)
    p.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)

    # Título
    p.setFillColorRGB(1, 1, 1)
    p.setFont('Helvetica-Bold', 24)
    p.drawCentredString(width / 2, height - 80, 'ESCUELA DE TAEKWONDO - ARABIA TKD')

    p.setFont('Helvetica', 14)
    p.drawCentredString(width / 2, height - 110, 'Ficha de Inscripción a Examen')

    y = height - 160
    p.setFont('Helvetica', 11)

    label_font = 'Helvetica-Bold'
    value_font = 'Helvetica'
    line_spacing = 24

    if student:
        p.setFont(label_font, 11)
        p.drawString(margin + 30, y, "Alumno:")
        p.setFont(value_font, 11)
        p.drawString(margin + 120, y, student.get('full_name', ''))
        y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Fecha de examen:")
    p.setFont(value_font, 11)
    p.drawString(margin + 150, y, f"{event.get('date', '')} {event.get('time', '')}")
    y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Tipo / Graduación:")
    p.setFont(value_font, 11)
    p.drawString(margin + 165, y, event.get('level', ''))
    y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Lugar:")
    p.setFont(value_font, 11)
    p.drawString(margin + 90, y, event.get('place', ''))
    y -= line_spacing

    notes = (event.get('notes') or '').strip()
    if notes:
        p.setFont(label_font, 11)
        p.drawString(margin + 30, y, "Notas / Observaciones:")
        y -= 18
        p.setFont(value_font, 10)
        for line in notes.split('\n'):
            p.drawString(margin + 40, y, line[:90])
            y -= 14
        p.setFont(value_font, 11)

    # Frase central
    p.setFont('Helvetica-BoldOblique', 14)
    p.drawCentredString(width / 2, height / 2, '\"No falten y no lleguen tarde...\" — Master VII DAN Fernando A. Monteros')

    # Logo Arabia TKD (si existe el archivo en static/img/logo.jpg)
    logo_path = os.path.join(app.static_folder, 'img', 'logo.jpg')
    if os.path.exists(logo_path):
      try:
        logo = ImageReader(logo_path)
        logo_width = 120
        logo_height = 120
        p.drawImage(logo, width / 2 - logo_width / 2, height - 320, width=logo_width, height=logo_height, mask='auto')
      except Exception:
        # Si no se puede leer el logo, se omite silenciosamente
        pass

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"inscripcion_examen_{event_id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)
