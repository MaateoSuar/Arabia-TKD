from flask import Flask, jsonify, request, render_template, send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)


# --- Config DB (Postgres en Railway vía DATABASE_URL) ---
db_url = os.environ.get("DATABASE_URL")

# Railway suele entregar postgres://; lo adaptamos a SQLAlchemy con psycopg3
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///arabia_tkd.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

with app.app_context():
    try:
        from sqlalchemy import text

        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE students ADD COLUMN notes TEXT"))
            conn.commit()
    except Exception:
        # Si falla (por ejemplo en SQLite viejo), se ignora y se asume que la tabla se recreará en limpio.
        pass


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(120))
    first_name = db.Column(db.String(120))
    dni = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    birthdate = db.Column(db.Date)
    blood = db.Column(db.String(10))
    nationality = db.Column(db.String(80))
    province = db.Column(db.String(80))
    country = db.Column(db.String(80))
    city = db.Column(db.String(80))
    address = db.Column(db.String(200))
    zip = db.Column(db.String(20))
    school = db.Column(db.String(120))
    belt = db.Column(db.String(40))
    father_name = db.Column(db.String(200))
    mother_name = db.Column(db.String(200))
    father_phone = db.Column(db.String(40))
    mother_phone = db.Column(db.String(40))
    parent_email = db.Column(db.String(120))
    notes = db.Column(db.Text)


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    time = db.Column(db.String(8))  # HH:MM
    title = db.Column(db.String(200))
    type = db.Column(db.String(20), nullable=False, default="general")  # 'general' | 'exam'
    level = db.Column(db.String(80))
    place = db.Column(db.String(160))
    notes = db.Column(db.Text)


class FeePayment(db.Model):
    __tablename__ = "fee_payments"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    payment_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def index():
    return render_template('index.html')


# --- Students CRUD ---
@app.route('/api/students', methods=['GET', 'POST'])
def api_students():
    if request.method == 'GET':
        students_q = Student.query.order_by(
            (Student.last_name.is_(None)).asc(),
            Student.last_name.asc(),
            Student.first_name.asc(),
        ).all()
        result = []
        for s in students_q:
            result.append({
                'id': s.id,
                'full_name': s.full_name,
                'last_name': s.last_name,
                'first_name': s.first_name,
                'dni': s.dni,
                'gender': s.gender,
                'birthdate': s.birthdate.isoformat() if s.birthdate else None,
                'blood': s.blood,
                'nationality': s.nationality,
                'province': s.province,
                'country': s.country,
                'city': s.city,
                'address': s.address,
                'zip': s.zip,
                'school': s.school,
                'belt': s.belt,
                'father_name': s.father_name,
                'mother_name': s.mother_name,
                'father_phone': s.father_phone,
                'mother_phone': s.mother_phone,
                'parent_email': s.parent_email,
                'notes': s.notes,
            })
        return jsonify(result)

    data = request.json or {}
    birthdate_val = data.get('birthdate')
    birthdate_parsed = None
    if birthdate_val:
        try:
            birthdate_parsed = datetime.strptime(birthdate_val, '%Y-%m-%d').date()
        except ValueError:
            birthdate_parsed = None

    student = Student(
        full_name=data.get('full_name', ''),
        last_name=data.get('last_name'),
        first_name=data.get('first_name'),
        dni=data.get('dni'),
        gender=data.get('gender'),
        birthdate=birthdate_parsed,
        blood=data.get('blood'),
        nationality=data.get('nationality'),
        province=data.get('province'),
        country=data.get('country'),
        city=data.get('city'),
        address=data.get('address'),
        zip=data.get('zip'),
        school=data.get('school'),
        belt=data.get('belt'),
        father_name=data.get('father_name'),
        mother_name=data.get('mother_name'),
        father_phone=data.get('father_phone'),
        mother_phone=data.get('mother_phone'),
        parent_email=data.get('parent_email'),
        notes=data.get('notes'),
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({'id': student.id, 'full_name': student.full_name}), 201


@app.route('/api/students/<int:student_id>', methods=['GET', 'PUT', 'DELETE'])
def api_student_detail(student_id: int):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': student.id,
            'full_name': student.full_name,
            'last_name': student.last_name,
            'first_name': student.first_name,
            'dni': student.dni,
            'gender': student.gender,
            'birthdate': student.birthdate.isoformat() if student.birthdate else None,
            'blood': student.blood,
            'nationality': student.nationality,
            'province': student.province,
            'country': student.country,
            'city': student.city,
            'address': student.address,
            'zip': student.zip,
            'school': student.school,
            'belt': student.belt,
            'father_name': student.father_name,
            'mother_name': student.mother_name,
            'father_phone': student.father_phone,
            'mother_phone': student.mother_phone,
            'parent_email': student.parent_email,
            'notes': student.notes,
        })

    if request.method == 'PUT':
        data = request.json or {}
        for field in [
            'full_name', 'last_name', 'first_name', 'dni', 'gender', 'blood',
            'nationality', 'province', 'country', 'city', 'address', 'zip',
            'school', 'belt', 'father_name', 'mother_name', 'father_phone',
            'mother_phone', 'parent_email', 'notes',
        ]:
            if field in data:
                setattr(student, field, data[field])

        if 'birthdate' in data:
            try:
                student.birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                student.birthdate = None

        db.session.commit()
        return jsonify({'status': 'ok'})

    if request.method == 'DELETE':
        # Borramos primero todas las cuotas asociadas a este alumno
        FeePayment.query.filter_by(student_id=student.id).delete()

        # Luego borramos el alumno en sí
        db.session.delete(student)
        db.session.commit()

        return '', 204


# --- Calendar & Exams ---
@app.route('/api/events', methods=['GET', 'POST'])
def api_events():
    if request.method == 'GET':
        events = Event.query.all()
        result = []
        for e in events:
            result.append({
                'id': e.id,
                'date': e.date,
                'time': e.time,
                'title': e.title,
                'type': e.type,
                'level': e.level,
                'place': e.place,
                'notes': e.notes,
            })
        return jsonify(result)

    data = request.json or {}
    event = Event(
        date=data.get('date'),
        time=data.get('time'),
        title=data.get('title'),
        type=data.get('type') or 'general',
        level=data.get('level'),
        place=data.get('place'),
        notes=data.get('notes'),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'id': event.id}), 201


@app.route('/api/events/<int:event_id>', methods=['GET', 'DELETE'])
def api_event_detail(event_id: int):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Evento no encontrado'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': event.id,
            'date': event.date,
            'time': event.time,
            'title': event.title,
            'type': event.type,
            'level': event.level,
            'place': event.place,
            'notes': event.notes,
        })

    # DELETE
    db.session.delete(event)
    db.session.commit()
    return '', 204


# --- Fees ---

def _compute_fees_status(student_id: int):
    payments = (
        FeePayment.query
        .filter_by(student_id=student_id)
        .order_by(FeePayment.payment_date.asc())
        .all()
    )

    if not payments:
        return {'student_id': student_id, 'status': 'sin_registro', 'history': []}

    last_payment = payments[-1].payment_date
    try:
        last_dt = datetime.strptime(last_payment, '%Y-%m-%d').date()
    except ValueError:
        last_dt = None

    today = date.today()
    if last_dt is None:
        status = 'sin_registro'
    else:
        delta_days = (today - last_dt).days
        status = 'al_dia' if delta_days <= 30 else 'vencida'

    history = [
        {
            'id': p.id,
            'date': p.payment_date,
            'amount': float(p.amount),
        }
        for p in payments
    ]

    return {
        'student_id': student_id,
        'status': status,
        'last_payment': last_payment,
        'history': history,
    }


@app.route('/api/fees/<int:student_id>', methods=['GET', 'POST'])
def api_fees(student_id: int):
    if request.method == 'GET':
        data = _compute_fees_status(student_id)
        return jsonify(data)

    # POST: registrar pago (un registro por envío)
    data = request.json or {}
    payment_date = data.get('payment_date') or datetime.now().strftime('%Y-%m-%d')
    amount = data.get('amount', 0)

    payment = FeePayment(
        student_id=student_id,
        payment_date=payment_date,
        amount=amount,
    )
    db.session.add(payment)
    db.session.commit()

    # Devolver el estado actualizado reutilizando la misma lógica del GET
    updated = _compute_fees_status(student_id)
    return jsonify(updated)


@app.route('/api/fees/payment/<int:payment_id>', methods=['DELETE'])
def api_fee_payment_delete(payment_id: int):
    """Eliminar un pago individual de cuotas (idempotente)."""
    payment = FeePayment.query.get(payment_id)
    if payment:
        db.session.delete(payment)
        db.session.commit()

    # Aunque no exista, devolvemos 204 para que el frontend quede consistente
    return '', 204


@app.route('/admin/clear-fees', methods=['GET'])
def admin_clear_fees():
    """Borrar TODOS los pagos de cuotas (uso administrativo, solo local)."""
    deleted = FeePayment.query.delete()
    db.session.commit()
    return jsonify({'deleted': deleted}), 200


# --- PDF generation for exam inscription ---
@app.route('/api/exams/<int:event_id>/inscription-pdf', methods=['POST'])
def generate_exam_pdf(event_id: int):
    """Genera un PDF de inscripción para un examen almacenado en la BD."""
    # Buscar el evento en la base de datos
    event = Event.query.get(event_id)
    if not event or event.type != 'exam':
        return jsonify({'error': 'Examen no encontrado'}), 404

    # (Opcional) en el futuro se podría vincular Student vía BD.
    student = None
    data = request.json or {}
    student_id = data.get('student_id')
    if student_id is not None:
        student = Student.query.get(student_id)

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
        # Student.full_name proviene del modelo
        p.drawString(margin + 120, y, getattr(student, 'full_name', '') or '')
        y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Fecha de examen:")
    p.setFont(value_font, 11)
    p.drawString(margin + 150, y, f"{event.date or ''} {event.time or ''}")
    y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Tipo / Graduación:")
    p.setFont(value_font, 11)
    p.drawString(margin + 165, y, event.level or '')
    y -= line_spacing

    p.setFont(label_font, 11)
    p.drawString(margin + 30, y, "Lugar:")
    p.setFont(value_font, 11)
    p.drawString(margin + 90, y, event.place or '')
    y -= line_spacing

    notes = (event.notes or '').strip()
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


@app.route('/api/exams/<int:event_id>/evaluation-pdf', methods=['POST'])
def generate_exam_evaluation_pdf(event_id: int):
    """Genera un PDF de evaluación (solicitud de graduación) para un examen."""

    event = Event.query.get(event_id)
    if not event or event.type != 'exam':
        return jsonify({'error': 'Examen no encontrado'}), 404

    data = request.json or {}
    student_id = data.get('student_id')
    student = Student.query.get(student_id) if student_id is not None else None

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 40

    # Fondo blanco
    p.setFillColorRGB(1, 1, 1)
    p.rect(0, 0, width, height, fill=1, stroke=0)

    # Marco suave en tonos oscuros (paleta de la escuela)
    p.setStrokeColorRGB(0.1, 0.1, 0.1)
    p.setLineWidth(1.5)
    p.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)

    # Encabezado principal
    y = height - 60
    p.setFont('Helvetica-Bold', 16)
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.drawCentredString(width / 2, y, 'ESCUELA DE TAEKWON-DO ARABIA TKD')
    y -= 20

    p.setFont('Helvetica', 10)
    p.drawCentredString(width / 2, y, 'Afiliada a la Federación Argentina de Asociaciones de Taekwon-do')
    y -= 25

    p.setFont('Helvetica-Bold', 14)
    p.drawCentredString(width / 2, y, 'Solicitud de graduación')
    y -= 25

    # Fecha (ligeramente más hacia la izquierda)
    p.setFont('Helvetica', 10)
    p.drawRightString(width - margin - 20, y, f"Fecha: {event.date or ''}")
    y -= 25

    def draw_label_value(label, value, x_label, x_value):
        p.setFont('Helvetica', 10)
        p.drawString(x_label, y, label)
        p.drawString(x_value, y, value or '')

    # Datos del alumno
    full_name = ''
    birth_str = ''
    age_str = ''
    gender = ''
    address = ''
    phone = ''
    nationality = ''
    dni = ''

    if student:
        full_name = student.full_name or ''
        gender = student.gender or ''
        dni = student.dni or ''
        nationality = student.nationality or ''
        address_parts = [student.address, student.city, student.province, student.country]
        address = ' - '.join([p_ for p_ in address_parts if p_])
        phone = student.father_phone or student.mother_phone or ''

        if student.birthdate:
            birth_str = student.birthdate.strftime('%d/%m/%Y')
            today = date.today()
            age = today.year - student.birthdate.year - (
                (today.month, today.day) < (student.birthdate.month, student.birthdate.day)
            )
            age_str = str(age)

    x1 = margin + 10
    # Columna principal de valores (ligeramente más a la izquierda)
    x2 = margin + 110

    draw_label_value('Apellido y Nombre:', full_name, x1, x2)
    y -= 18
    draw_label_value('Fecha de Nacimiento:', birth_str, x1, x2)
    # Bloque derecho más hacia adentro para evitar desfasaje
    p.drawString(x2 + 80, y, 'Edad: ' + (age_str or ''))
    p.drawString(x2 + 160, y, 'Sexo: ' + (gender or ''))
    y -= 18

    draw_label_value('Domicilio:', address, x1, x2)
    y -= 18
    draw_label_value('Teléfono:', phone, x1, x2)
    p.drawString(x2 + 130, y, 'Nacionalidad: ' + (nationality or ''))
    p.drawString(x2 + 250, y, 'D.N.I: ' + (dni or ''))
    y -= 18

    draw_label_value('Ocupación:', '', x1, x2)
    p.drawString(x2 + 250, y, 'Estado civil:')
    y -= 22

    # Datos de graduación (fila más compacta para que entren las tres etiquetas)
    p.setFont('Helvetica', 10)
    p.drawString(x1, y, 'Solicita Grad.:')
    # Pequeña línea para completar
    p.drawString(x1 + 90, y, '________________')
    p.drawString(x1 + 220, y, 'Actual graduación:')
    p.drawString(x1 + 360, y, 'Tiempo de práctica:')
    y -= 18

    draw_label_value('Escuela base:', 'INSTITUTO MONTEROS DE TAEKWONDO', x1, x2)
    y -= 28

    # Instructores
    p.setFont('Helvetica-Bold', 10)
    p.drawString(x1, y, 'INSTRUCTORES')
    p.drawString(x1 + 220, y, 'Instructores auxiliares')
    y -= 14

    p.setFont('Helvetica', 10)
    p.drawString(x1, y, '- Arabia, Sirio Facundo. IV DAN')
    p.drawString(x1 + 220, y, '- Cornejo, Tomás Felipe. III DAN')
    y -= 14
    p.drawString(x1, y, '- Arabia, Farid Ignacio. IV DAN')
    p.drawString(x1 + 220, y, '- Monteros, María de los Angeles. III DAN')
    y -= 14
    p.drawString(x1, y, '- Arabia, Salma Sofia. II DAN')
    y -= 24

    # Tabla de evaluación simplificada (líneas para completar)
    p.setFont('Helvetica', 10)
    p.drawString(x1, y, 'Formas Básicas: ____________________   Téc. Patadas: ____________________')
    y -= 14
    p.drawString(x1, y, 'Sambo Matsoki: ____________________   Bolsa: ____________________')
    y -= 14
    p.drawString(x1, y, 'Ibo Matsoki:   ____________________   Bolsa: ____________________')
    y -= 14
    p.drawString(x1, y, 'Ilbo Matsoki:  ____________________   Bolsa: ____________________')
    y -= 14
    p.drawString(x1, y, 'Tul:           ____________________   Bolsa: ____________________')
    y -= 18

    p.drawString(x1, y, 'Matsoki: _____________________________________________________________')
    y -= 14
    p.drawString(x1, y, 'Defensa Personal: ____________________________________________________')
    y -= 22

    p.drawString(x1, y, 'Postura: __________  Vista: __________  Concentración: __________')
    y -= 14
    p.drawString(x1, y, 'Respiración: ______  Equilibrio: ______  Flexibilidad: ______')
    y -= 14
    p.drawString(x1, y, 'Velocidad: ________  Fuerza: ________  Agilidad: ________')
    y -= 14
    p.drawString(x1, y, 'Potencia: _________  Relajación: _________')
    y -= 18

    p.drawString(x1, y, 'Conocimiento en Oral: _______________________________________________')
    y -= 14
    p.drawString(x1, y, 'Disciplina: _______________    Teoría: ______________________________')
    y -= 18

    p.drawString(x1, y, 'Observaciones: _________________________________________________')
    y -= 28

    # Firmas (más abajo para dar aire al contenido)
    p.drawString(x1, y, 'Evaluador:')
    y -= 45
    p.line(x1, y, x1 + 200, y)
    p.drawString(x1, y - 14, 'Nombre y Firma')

    # Frase en el fondo
    p.setFont('Helvetica-Oblique', 10)
    p.drawCentredString(width / 2, margin + 20, '"No falten y no lleguen tarde…" - Master VII DAN Fernando A. Monteros')

    # Logos (si existen)
    logo_arabia_path = os.path.join(app.static_folder, 'img', 'logo.jpg')
    if os.path.exists(logo_arabia_path):
        try:
            logo = ImageReader(logo_arabia_path)
            # Esquina superior derecha dentro del marco
            logo_size = 60
            p.drawImage(
                logo,
                width - margin - logo_size,
                height - margin - logo_size,
                width=logo_size,
                height=logo_size,
                mask='auto',
            )
        except Exception:
            pass

    logo_monteros_path = os.path.join(app.static_folder, 'img', 'logo_monteros.png')
    if os.path.exists(logo_monteros_path):
        try:
            logo2 = ImageReader(logo_monteros_path)
            p.drawImage(logo2, width - margin - 90, height - 170, width=80, height=80, mask='auto')
        except Exception:
            pass

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"evaluacion_examen_{event_id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
