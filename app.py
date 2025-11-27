from flask import Flask, jsonify, request, render_template, send_file
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2._page import PageObject
from PyPDF2.generic import NameObject, BooleanObject
from datetime import datetime, date
from copy import deepcopy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

# ...
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
            # Intentar agregar columna notes si no existe
            try:
                conn.execute(text("ALTER TABLE students ADD COLUMN notes TEXT"))
            except Exception:
                pass

            # Intentar agregar columna status si no existe
            try:
                conn.execute(text("ALTER TABLE students ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"))
            except Exception:
                pass

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
    status = db.Column(db.String(20), nullable=False, default="active")


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


class ExamInscription(db.Model):
    __tablename__ = "exam_inscriptions"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)


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
                'status': s.status,
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
        status=data.get('status') or 'active',
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
            'status': student.status,
        })

    if request.method == 'PUT':
        data = request.json or {}
        for field in [
            'full_name', 'last_name', 'first_name', 'dni', 'gender', 'blood',
            'nationality', 'province', 'country', 'city', 'address', 'zip',
            'school', 'belt', 'father_name', 'mother_name', 'father_phone',
            'mother_phone', 'parent_email', 'notes', 'status',
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


@app.route('/api/exams/<int:event_id>/students', methods=['GET', 'PUT'])
def api_exam_students(event_id: int):
    """Gestiona la lista de alumnos inscriptos a un examen.

    GET: devuelve la lista de alumnos inscriptos (mismo formato básico que /api/students, pero filtrado).
    PUT: reemplaza la lista de inscriptos con los IDs enviados en JSON: { "student_ids": [1,2,3] }.
    """

    event = Event.query.get(event_id)
    if not event or event.type != 'exam':
        return jsonify({'error': 'Examen no encontrado'}), 404

    if request.method == 'GET':
        inscriptions = ExamInscription.query.filter_by(event_id=event_id).all()
        student_ids = [ins.student_id for ins in inscriptions]

        if not student_ids:
            return jsonify([])

        students = Student.query.filter(Student.id.in_(student_ids)).all()
        result = []
        for s in students:
            result.append({
                'id': s.id,
                'full_name': s.full_name,
                'last_name': s.last_name,
                'first_name': s.first_name,
                'belt': s.belt,
                'status': s.status,
            })
        return jsonify(result)

    # PUT
    data = request.json or {}
    ids = data.get('student_ids') or []

    # Normalizar a enteros, ignorando valores no válidos
    normalized_ids = []
    for raw_id in ids:
        try:
            normalized_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    # Borrar inscripciones anteriores de ese examen
    ExamInscription.query.filter_by(event_id=event_id).delete()

    # Insertar nuevas
    for sid in normalized_ids:
        db.session.add(ExamInscription(event_id=event_id, student_id=sid))

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'No se pudieron guardar las inscripciones'}), 400

    return jsonify({'event_id': event_id, 'student_ids': normalized_ids})


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
            logo_width = 80
            logo_height = 80
            p.drawImage(logo, width - margin - logo_width, height - margin - logo_height, width=logo_width, height=logo_height, mask='auto')
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


@app.route('/api/exams/<int:event_id>/rinde-pdf', methods=['POST'])
def generate_exam_rinde_pdf(event_id: int):
    """Genera un PDF de rendida multi-hoja usando el PDF base de Taekwondo.

    Cada alumno va en una página distinta, partiendo de la primera página del
    archivo 'src/PDF TAEKWONDO segunda edicion.pdf'.
    """

    event = Event.query.get(event_id)
    if not event or event.type != 'exam':
        return jsonify({'error': 'Examen no encontrado'}), 404

    data = request.json or {}
    raw_ids = data.get('student_ids') or []

    # Normalizar a enteros válidos
    student_ids = []
    for raw in raw_ids:
        try:
            student_ids.append(int(raw))
        except (TypeError, ValueError):
            continue

    if not student_ids:
        return jsonify({'error': 'No se recibieron alumnos para el examen'}), 400

    students = Student.query.filter(Student.id.in_(student_ids)).all()
    if not students:
        return jsonify({'error': 'Alumnos no encontrados'}), 404

    # Progresión de cinturones, Gup y Graduación (igual que en el frontend)
    belt_progress = [
        {"belt": "Blanco", "gup": "10º Gup", "graduation": "Primera"},
        {"belt": "Blanco Punta Amarilla", "gup": "9º Gup", "graduation": "Segunda"},
        {"belt": "Amarillo", "gup": "8º Gup", "graduation": "Tercera"},
        {"belt": "Amarillo Punta Verde", "gup": "7º Gup", "graduation": "Cuarta"},
        {"belt": "Verde", "gup": "6º Gup", "graduation": "Quinta"},
        {"belt": "Verde Punta Azul", "gup": "5º Gup", "graduation": "Sexta"},
        {"belt": "Azul", "gup": "4º Gup", "graduation": "Séptima"},
        {"belt": "Azul Punta Roja", "gup": "3º Gup", "graduation": "Octava"},
        {"belt": "Rojo", "gup": "2º Gup", "graduation": "Novena"},
        {"belt": "Rojo Punta Negra", "gup": "1º Gup", "graduation": "Décima"},
        {"belt": "Negro Primer Dan", "gup": "", "graduation": "Primer Dan"},
        {"belt": "Segundo Dan", "gup": "", "graduation": "Segundo Dan"},
    ]

    def get_belt_infos(current_belt: str):
        """Devuelve (info_actual, info_siguiente) según la progresión de cinturones."""
        if not current_belt:
            return None, None
        current = current_belt.strip().lower()
        idx = next((i for i, b in enumerate(belt_progress) if b["belt"].lower() == current), -1)
        if idx == -1:
            return None, None
        current_info = belt_progress[idx]
        next_info = belt_progress[idx + 1] if idx < len(belt_progress) - 1 else None
        return current_info, next_info

    # Cargar PDF base
    template_path = os.path.join('src', 'PDF TAEKWONDO segunda edicion.pdf')
    if not os.path.exists(template_path):
        return jsonify({'error': 'PDF base no encontrado en src'}), 500

    reader = PdfReader(template_path)
    if not reader.pages:
        return jsonify({'error': 'PDF base sin páginas'}), 500

    template_page = reader.pages[0]
    page_width = float(template_page.mediabox.width)
    page_height = float(template_page.mediabox.height)

    writer = PdfWriter()

    for student in students:
        # Datos del alumno
        if student.last_name or student.first_name:
            # Formato "Apellido, Nombre" cuando hay ambos
            if student.last_name and student.first_name:
                full_name = f"{student.last_name}, {student.first_name}"
            else:
                full_name = (student.last_name or student.first_name) or ''
        else:
            full_name = student.full_name or ''
        dni = student.dni or ''
        gender = (student.gender or '').upper()
        belt_current = (student.belt or '').strip()
        current_info, next_info = get_belt_infos(belt_current)
        belt_next = next_info["belt"] if next_info else ''
        gup_current = current_info["gup"] if current_info else ''
        gup_next = next_info["gup"] if next_info else ''

        # Fecha de nacimiento y edad (en años y meses)
        birth_str = ''
        age_str = ''
        if student.birthdate:
            birth_str = student.birthdate.strftime('%d/%m/%Y')
            try:
                exam_date = datetime.strptime(event.date, '%Y-%m-%d').date() if event.date else date.today()
            except ValueError:
                exam_date = date.today()

            years = exam_date.year - student.birthdate.year
            months = exam_date.month - student.birthdate.month
            days = exam_date.day - student.birthdate.day

            # Ajuste por días: si los días son negativos, restamos un mes
            if days < 0:
                months -= 1

            # Ajuste por meses negativos
            if months < 0:
                years -= 1
                months += 12

            if years < 0:
                years = 0
            if months < 0:
                months = 0

            age_str = f"{years} años y {months} meses"

        # Fecha de examen en formato DD/MM/AAAA si es posible
        fecha_examen = ''
        if event.date:
            try:
                _exam_dt = datetime.strptime(event.date, '%Y-%m-%d').date()
                fecha_examen = _exam_dt.strftime('%d/%m/%Y')
            except ValueError:
                fecha_examen = event.date

        # Coordinadas base (similares a las del PDF de debug)
        # x_left ligeramente más a la derecha para ajustar el nombre
        x_left = page_width * 0.265
        # Columna derecha superior (Fecha/DNI/Edad) más a la derecha
        x_right_top = page_width * 0.78
        # Columna derecha media en una posición fija razonable
        x_right_mid = page_width * 0.52

        # y_start_left un poco más arriba para terminar de ajustar la altura del nombre
        y_start_left = page_height - 146
        # Columna derecha superior aún más arriba para la Fecha de examen
        y_start_right_top = page_height - 160
        # Columna derecha media más arriba
        y_start_right_mid = page_height - 200
        step = 14

        # Crear overlay con ReportLab
        overlay_buf = BytesIO()
        c = canvas.Canvas(overlay_buf, pagesize=(page_width, page_height))
        c.setFont('Helvetica', 9)

        # Columna izquierda (Nombre, Sexo, Cinturón actual, GUP actual)
        y = y_start_left
        c.drawString(x_left, y, full_name or '')         # Apellido y Nombre
        y -= step
        # Sexo un poquito más a la izquierda y apenas más arriba
        c.drawString(x_left - 65, y - 1, gender or '')   # Sexo
        y -= step
        # Cinturón actual un poquito más a la izquierda y un poquito más abajo
        c.drawString(x_left - 14, y - 1, belt_current or '')  # Cinturón actual
        y -= step
        # GUP actual un poquito más a la izquierda y un poquito más abajo
        c.drawString(x_left - 34, y - 2, gup_current or '')  # GUP actual

        # Columna derecha superior (Fecha examen, DNI, Edad)
        y_rt = y_start_right_top
        # Fecha de examen un poquito más arriba y un poco más a la izquierda
        c.drawString(x_right_top - 15, y_rt + 44, fecha_examen or '')  # Fecha examen
        y_rt -= step
        # DNI alineado en X con la Fecha de examen, apenas más arriba y un poco más a la izquierda
        c.drawString(x_right_top - 17, y_rt + 27, dni or '')           # DNI
        y_rt -= step
        # Edad alineada en X con DNI, un poquito más abajo y un poquito más a la izquierda
        c.drawString(x_right_top - 18, y_rt + 27, age_str or '')       # Edad

        # Columna derecha media (Fecha nacimiento, Cinturón que rinde, GUP que rinde)
        y_rm = y_start_right_mid
        # Subimos Fecha de nacimiento para que esté a la altura aproximada de Sexo
        # y la movemos muy ligeramente más hacia la izquierda (ajuste muy fino)
        c.drawString(x_right_mid + 31, y_rm + 39, birth_str or '')     # Fecha nacimiento
        y_rm -= step
        # Cinturón que rinde (Solicita cinturón) bastante más a la izquierda dentro de la columna
        c.drawString(x_right_mid + 10, y_rm + 38, belt_next or '')     # Cinturón que rinde
        y_rm -= step
        # GUP que rinde (Solicita GUP) medio punto más arriba y un poquito a la izquierda
        c.drawString(x_right_mid - 5, y_rm + 38, gup_next or '') # GUP que rinde

        c.showPage()
        c.save()

        overlay_buf.seek(0)
        overlay_reader = PdfReader(overlay_buf)
        overlay_page = overlay_reader.pages[0]

        merged_page = PageObject.create_blank_page(
            width=template_page.mediabox.width,
            height=template_page.mediabox.height,
        )
        merged_page.merge_page(template_page)
        merged_page.merge_page(overlay_page)
        writer.add_page(merged_page)

    out_buffer = BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)

    filename = f"rinde_examen_{event_id}.pdf"
    return send_file(out_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/api/exams/template-debug-pdf', methods=['GET'])
def exam_template_debug_pdf():
  """Genera un PDF de calibración con marcadores L1..L12 y R1..R12 sobre la plantilla base.

  Usar este PDF para identificar qué marcador coincide con cada línea amarilla
  del formulario y así ajustar con precisión las coordenadas.
  """

  template_path = os.path.join('src', 'PDF TAEKWONDO segunda edicion.pdf')
  if not os.path.exists(template_path):
      return jsonify({'error': 'PDF base no encontrado en src'}), 500

  reader = PdfReader(template_path)
  if not reader.pages:
      return jsonify({'error': 'PDF base sin páginas'}), 500
  template_page = reader.pages[0]

  writer = PdfWriter()

  # Usamos el tamaño real de la página de la plantilla para que overlay y base coincidan 1:1
  overlay_width = float(template_page.mediabox.width)
  overlay_height = float(template_page.mediabox.height)
  x_left = overlay_width * 0.30
  x_right_top = overlay_width * 0.72
  x_right_mid = overlay_width * 0.63

  buf_overlay = BytesIO()
  c = canvas.Canvas(buf_overlay, pagesize=(overlay_width, overlay_height))
  c.setFont('Helvetica', 8)

  # Marcadores L1..L12 en la columna izquierda.
  # Subimos el bloque para que L1 quede a la altura de "Apellido y Nombre".
  y_start_left = overlay_height - 180
  step = 14
  for i in range(12):
      y = y_start_left - i * step
      c.drawString(x_left, y, f'L{i + 1}')

  # Marcadores R1..R12 en la columna derecha superior (Fecha/DNI/Edad)
  y_start_right_top = overlay_height - 220
  for i in range(12):
      y = y_start_right_top - i * step
      c.drawString(x_right_top, y, f'RT{i + 1}')

  # Marcadores RM1..RM12 en la columna derecha media (Fecha Nac / Solicita cinturón / Solicita GUP)
  y_start_right_mid = overlay_height - 260
  for i in range(12):
      y = y_start_right_mid - i * step
      c.drawString(x_right_mid, y, f'RM{i + 1}')

  c.save()
  buf_overlay.seek(0)

  overlay_reader = PdfReader(buf_overlay)
  overlay_page = overlay_reader.pages[0]

  merged_page = PageObject.create_blank_page(
      width=template_page.mediabox.width,
      height=template_page.mediabox.height,
  )
  merged_page.merge_page(template_page)
  merged_page.merge_page(overlay_page)
  writer.add_page(merged_page)

  out_buffer = BytesIO()
  writer.write(out_buffer)
  out_buffer.seek(0)

  return send_file(out_buffer, as_attachment=True, download_name='debug_examen_template.pdf', mimetype='application/pdf')


@app.route('/api/exams/template-fields', methods=['GET'])
def exam_template_fields():
    """Devuelve los campos de formulario (AcroForm) del PDF base.

    Útil para ver exactamente cómo se llaman los campos de texto que creaste
    en la plantilla editable y poder mapearlos desde el backend.
    """

    template_path = os.path.join('src', 'PDF TAEKWONDO segunda edicion.pdf')
    if not os.path.exists(template_path):
        return jsonify({'error': 'PDF base no encontrado en src'}), 500

    reader = PdfReader(template_path)
    if not reader.pages:
        return jsonify({'error': 'PDF base sin páginas'}), 500

    fields = reader.get_fields() or {}
    # Convertimos los objetos de PyPDF2 a strings simples
    simple = {}
    for name, data in fields.items():
        simple[str(name)] = {
            'name': str(name),
            'type': str(data.get('/FT')) if isinstance(data, dict) else None,
        }

    return jsonify(simple)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
