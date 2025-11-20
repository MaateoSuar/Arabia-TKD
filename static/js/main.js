// Navegación entre secciones
const sections = document.querySelectorAll('.section');
const navButtons = document.querySelectorAll('.bottom-nav-item');

navButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const targetId = btn.getAttribute('data-target');
    if (!targetId) return;

    sections.forEach((s) => s.classList.remove('section-active'));
    document.getElementById(targetId)?.classList.add('section-active');

    navButtons.forEach((b) => b.classList.remove('bottom-nav-item-active'));
    btn.classList.add('bottom-nav-item-active');
  });
});

// Helpers API
async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Error GET ' + url);
  return res.json();
}

function renderGenericCalendar(targetCalendarEl, selectedDateRef, ymRef, onSelect) {
  if (!targetCalendarEl) return;
  const { year, month } = ymRef.value;
  const firstDay = new Date(year, month, 1);
  const startWeekday = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const monthNames = [
    'Enero','Febrero','Marzo','Abril','Mayo','Junio',
    'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre',
  ];

  const wrapper = document.createElement('div');
  const header = document.createElement('div');
  header.className = 'exam-inline-calendar-header';

  const prevBtn = document.createElement('button');
  prevBtn.type = 'button';
  prevBtn.className = 'btn-icon';
  prevBtn.textContent = '<';
  prevBtn.addEventListener('click', () => {
    ymRef.value.month -= 1;
    if (ymRef.value.month < 0) {
      ymRef.value.month = 11;
      ymRef.value.year -= 1;
    }
    renderGenericCalendar(targetCalendarEl, selectedDateRef, ymRef, onSelect);
  });

  const label = document.createElement('div');
  label.className = 'exam-inline-calendar-month';
  label.textContent = `${monthNames[month]} ${year}`;

  const nextBtn = document.createElement('button');
  nextBtn.type = 'button';
  nextBtn.className = 'btn-icon';
  nextBtn.textContent = '>';
  nextBtn.addEventListener('click', () => {
    ymRef.value.month += 1;
    if (ymRef.value.month > 11) {
      ymRef.value.month = 0;
      ymRef.value.year += 1;
    }
    renderGenericCalendar(targetCalendarEl, selectedDateRef, ymRef, onSelect);
  });

  header.appendChild(prevBtn);
  header.appendChild(label);
  header.appendChild(nextBtn);

  const grid = document.createElement('div');
  grid.className = 'exam-inline-calendar-grid';

  ['D', 'L', 'M', 'M', 'J', 'V', 'S'].forEach((d) => {
    const cell = document.createElement('div');
    cell.className = 'exam-inline-calendar-cell exam-inline-header';
    cell.textContent = d;
    grid.appendChild(cell);
  });

  for (let i = 0; i < startWeekday; i++) {
    const empty = document.createElement('div');
    empty.className = 'exam-inline-calendar-cell';
    grid.appendChild(empty);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const cellDate = new Date(year, month, day);
    const dateStr = cellDate.toISOString().slice(0, 10);
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
      today.getDate(),
    ).padStart(2, '0')}`;
    const cell = document.createElement('div');
    cell.className = 'exam-inline-calendar-cell exam-inline-day';
    cell.textContent = String(day);

    if (dateStr < todayStr) {
      cell.classList.add('exam-inline-day-disabled');
    }

    if (selectedDateRef.value === dateStr) {
      cell.classList.add('exam-inline-selected');
    }

    cell.addEventListener('click', () => {
      if (dateStr < todayStr) return; // no permitir seleccionar fechas pasadas
      selectedDateRef.value = dateStr;
      onSelect(dateStr);
      renderGenericCalendar(targetCalendarEl, selectedDateRef, ymRef, onSelect);
    });

    grid.appendChild(cell);
  }

  wrapper.appendChild(header);
  wrapper.appendChild(grid);

  targetCalendarEl.innerHTML = '';
  targetCalendarEl.appendChild(wrapper);
}

async function apiSend(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error('Error ' + method + ' ' + url);
  return res.status === 204 ? null : res.json();
}

// --- Alumnos ---

let studentsCache = [];

const studentsTbody = document.getElementById('students-tbody');
const studentsEmptyState = document.getElementById('students-empty-state');
const studentsBeltFilter = document.getElementById('students-belt-filter');
const btnOpenCreateStudent = document.getElementById('btn-open-create-student');
const modalStudent = document.getElementById('modal-student');
const btnCloseStudent = document.getElementById('btn-close-student');
const btnCancelStudent = document.getElementById('btn-cancel-student');
const studentForm = document.getElementById('student-form');
const studentIdInput = document.getElementById('student-id');
const modalStudentTitle = document.getElementById('modal-student-title');

function openStudentModal(editData) {
  modalStudent?.classList.remove('hidden');
  if (editData) {
    modalStudentTitle.textContent = 'Editar Alumno';
    studentIdInput.value = editData.id;
    document.getElementById('student-full-name').value = editData.full_name || '';
    document.getElementById('student-dni').value = editData.dni || '';
    document.getElementById('student-gender').value = editData.gender || '';
    document.getElementById('student-birthdate').value = editData.birthdate || '';
    document.getElementById('student-blood').value = editData.blood || '';
    document.getElementById('student-nationality').value = editData.nationality || '';
    document.getElementById('student-province').value = editData.province || '';
    document.getElementById('student-country').value = editData.country || '';
    document.getElementById('student-city').value = editData.city || '';
    document.getElementById('student-address').value = editData.address || '';
    document.getElementById('student-zip').value = editData.zip || '';
    document.getElementById('student-school').value = editData.school || '';
    document.getElementById('student-belt').value = editData.belt || '';
    document.getElementById('student-father-name').value = editData.father_name || '';
    document.getElementById('student-mother-name').value = editData.mother_name || '';
    document.getElementById('student-father-phone').value = editData.father_phone || '';
    document.getElementById('student-mother-phone').value = editData.mother_phone || '';
    document.getElementById('student-parent-email').value = editData.parent_email || '';
  } else {
    modalStudentTitle.textContent = 'Crear Alumno';
    studentIdInput.value = '';
    studentForm.reset();
    if (document.getElementById('student-belt')) {
      document.getElementById('student-belt').value = '';
    }
  }
}

studentsBeltFilter?.addEventListener('change', () => {
  loadStudents();
});

function closeStudentModal() {
  modalStudent?.classList.add('hidden');
}

btnOpenCreateStudent?.addEventListener('click', () => openStudentModal());
btnCloseStudent?.addEventListener('click', closeStudentModal);
btnCancelStudent?.addEventListener('click', closeStudentModal);

async function loadStudents() {
  try {
    const list = await apiGet('/api/students');
    studentsCache = list;
    if (!studentsTbody) return;
    studentsTbody.innerHTML = '';

    if (studentsEmptyState) {
      studentsEmptyState.style.display = list.length === 0 ? 'block' : 'none';
    }

    const selectedBelt = studentsBeltFilter ? studentsBeltFilter.value : '';

    const filtered = selectedBelt ? list.filter((s) => (s.belt || '') === selectedBelt) : list;

    filtered.forEach((st) => {
      const tr = document.createElement('tr');
      const age = st.birthdate ? calcAge(st.birthdate) : '';
      const belt = st.belt || '';
      const beltLabel = belt ? belt.charAt(0).toUpperCase() + belt.slice(1) : '';

      tr.innerHTML = `
        <td>${st.last_name || ''}</td>
        <td>${st.first_name || ''}</td>
        <td>${age}</td>
        <td>
          ${belt ? `<span class="belt-pill belt-${belt}">${beltLabel}</span>` : ''}
        </td>
        <td>${st.father_name || ''}</td>
        <td>${st.father_phone || ''}</td>
        <td class="students-actions">
          <button class="students-menu-btn" data-id="${st.id}">⋮</button>
        </td>
      `;

      const menuBtn = tr.querySelector('.students-menu-btn');
      menuBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        const action = window.prompt(
          'Acción para el alumno:\n1 - Ver legajo (placeholder)\n2 - Editar\n3 - Eliminar',
          '2'
        );
        if (!action) return;
        if (action === '1') {
          window.alert('Legajo completo: esta vista se implementará más adelante.');
        } else if (action === '2') {
          openStudentModal({ ...st, full_name: st.full_name });
        } else if (action === '3') {
          if (window.confirm('¿Seguro que querés eliminar este alumno?')) {
            apiSend(`/api/students/${st.id}`, 'DELETE').then(loadStudents).catch(console.error);
          }
        }
      });

      studentsTbody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
  }
}

function formatDniWithDots(value) {
  const digits = value.replace(/\D/g, '');
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return digits.replace(/(\d{2})(\d+)/, '$1.$2');
  return digits.replace(/(\d{2})(\d{3})(\d+)/, '$1.$2.$3');
}

const studentDniInput = document.getElementById('student-dni');
if (studentDniInput) {
  studentDniInput.addEventListener('input', (e) => {
    const target = e.target;
    target.value = formatDniWithDots(target.value);
  });
}

studentForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = studentIdInput.value;
  const fullName = document.getElementById('student-full-name').value.trim();
  const [lastName, ...rest] = fullName.split(' ');
  const firstName = rest.join(' ');

  const payload = {
    full_name: fullName,
    last_name: lastName,
    first_name: firstName,
    dni: document.getElementById('student-dni').value,
    gender: document.getElementById('student-gender').value,
    birthdate: document.getElementById('student-birthdate').value,
    blood: document.getElementById('student-blood').value,
    nationality: document.getElementById('student-nationality').value,
    province: document.getElementById('student-province').value,
    country: document.getElementById('student-country').value,
    city: document.getElementById('student-city').value,
    address: document.getElementById('student-address').value,
    zip: document.getElementById('student-zip').value,
    school: document.getElementById('student-school').value,
    belt: document.getElementById('student-belt').value,
    father_name: document.getElementById('student-father-name').value,
    mother_name: document.getElementById('student-mother-name').value,
    father_phone: document.getElementById('student-father-phone').value,
    mother_phone: document.getElementById('student-mother-phone').value,
    parent_email: document.getElementById('student-parent-email').value,
  };

  try {
    if (id) {
      await apiSend(`/api/students/${id}`, 'PUT', payload);
    } else {
      await apiSend('/api/students', 'POST', payload);
    }
    closeStudentModal();
    loadStudents();
  } catch (err) {
    console.error(err);
  }
});

function calcAge(dateStr) {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return '';
  const today = new Date();
  let age = today.getFullYear() - d.getFullYear();
  const m = today.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < d.getDate())) {
    age--;
  }
  return age;
}

// --- Calendario ---

const calendarGrid = document.getElementById('calendar-grid');
const calendarMonthLabel = document.getElementById('calendar-month-label');
const calendarPrev = document.getElementById('calendar-prev');
const calendarNext = document.getElementById('calendar-next');
const calendarDetailsBody = document.getElementById('calendar-details-body');

let currentYearMonth = (() => {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() };
})();

let eventsCache = [];

function renderCalendar() {
  if (!calendarGrid || !calendarMonthLabel) return;
  const { year, month } = currentYearMonth;
  const firstDay = new Date(year, month, 1);
  const startWeekday = firstDay.getDay(); // 0=Domingo
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const monthNames = [
    'Enero',
    'Febrero',
    'Marzo',
    'Abril',
    'Mayo',
    'Junio',
    'Julio',
    'Agosto',
    'Septiembre',
    'Octubre',
    'Noviembre',
    'Diciembre',
  ];
  calendarMonthLabel.textContent = `${monthNames[month]} ${year}`;

  calendarGrid.innerHTML = '';

  // Encabezados días
  ['D', 'L', 'M', 'M', 'J', 'V', 'S'].forEach((d) => {
    const head = document.createElement('div');
    head.className = 'calendar-cell calendar-cell-head';
    head.style.fontWeight = '600';
    head.textContent = d;
    calendarGrid.appendChild(head);
  });

  // Celdas vacías antes del 1
  for (let i = 0; i < startWeekday; i++) {
    const cell = document.createElement('div');
    cell.className = 'calendar-cell';
    cell.style.visibility = 'hidden';
    calendarGrid.appendChild(cell);
  }

  const today = new Date();
  for (let day = 1; day <= daysInMonth; day++) {
    const cellDate = new Date(year, month, day);
    const cell = document.createElement('div');
    cell.className = 'calendar-cell';

    if (
      cellDate.getFullYear() === today.getFullYear() &&
      cellDate.getMonth() === today.getMonth() &&
      cellDate.getDate() === today.getDate()
    ) {
      cell.classList.add('calendar-cell-today');
    }

    const header = document.createElement('div');
    header.className = 'calendar-cell-header';
    const daySpan = document.createElement('span');
    daySpan.textContent = String(day);
    header.appendChild(daySpan);

    const evDot = document.createElement('span');
    const dateStr = cellDate.toISOString().slice(0, 10);
    const hasExam = eventsCache.some((e) => e.date === dateStr && e.type === 'exam');
    const hasEvent = eventsCache.some((e) => e.date === dateStr);

    // Cumpleaños: comparar solo mes/día en base a las cadenas 'YYYY-MM-DD'
    const [yStr, mStr, dStr] = dateStr.split('-');
    const cellMonth = Number(mStr);
    const cellDay = Number(dStr);
    const hasBirthday = studentsCache.some((s) => {
      if (!s.birthdate) return false;
      const parts = String(s.birthdate).split('-');
      if (parts.length !== 3) return false;
      const bdMonth = Number(parts[1]);
      const bdDay = Number(parts[2]);
      return bdMonth === cellMonth && bdDay === cellDay;
    });

    if (hasEvent) {
      evDot.className = hasBirthday ? 'calendar-event-dot calendar-birthday-dot' : 'calendar-event-dot';
      if (hasExam) cell.classList.add('calendar-cell-exam');
    } else if (hasBirthday) {
      evDot.className = 'calendar-event-dot calendar-birthday-dot';
      cell.classList.add('calendar-cell-birthday');
    }
    header.appendChild(evDot);

    cell.appendChild(header);

    cell.addEventListener('click', () => showDayEvents(dateStr));

    calendarGrid.appendChild(cell);
  }
}

function showDayEvents(dateStr) {
  if (!calendarDetailsBody) return;
  const dayEvents = eventsCache.filter((e) => e.date === dateStr);
  const [, mStr, dStr] = dateStr.split('-');
  const cellMonth = Number(mStr);
  const cellDay = Number(dStr);

  const birthdays = studentsCache.filter((s) => {
    if (!s.birthdate) return false;
    const parts = String(s.birthdate).split('-');
    if (parts.length !== 3) return false;
    const bdMonth = Number(parts[1]);
    const bdDay = Number(parts[2]);
    return bdMonth === cellMonth && bdDay === cellDay;
  });

  if (!dayEvents.length && !birthdays.length) {
    calendarDetailsBody.textContent = 'Sin eventos para este día.';
    return;
  }

  const list = document.createElement('ul');
  list.style.listStyle = 'none';
  list.style.padding = '0';
  list.style.margin = '0';

  dayEvents.forEach((ev) => {
    const li = document.createElement('li');
    li.style.marginBottom = '4px';
    const typeLabel = ev.type === 'exam' ? '[Examen]' : '[Actividad]';
    const levelPart = ev.type === 'exam' && ev.level ? ` - ${ev.level}` : '';
    li.textContent = `${typeLabel} ${ev.title || ''} - ${ev.time || ''}${levelPart} ${ev.notes || ''}`;
    list.appendChild(li);
  });

  birthdays.forEach((s) => {
    const li = document.createElement('li');
    li.style.marginBottom = '4px';
    const name = s.full_name || `${s.last_name || ''} ${s.first_name || ''}`;
    li.textContent = `[Cumpleaños] ${name}`;
    list.appendChild(li);
  });

  calendarDetailsBody.innerHTML = '';
  calendarDetailsBody.appendChild(list);
}

calendarPrev?.addEventListener('click', () => {
  currentYearMonth.month -= 1;
  if (currentYearMonth.month < 0) {
    currentYearMonth.month = 11;
    currentYearMonth.year -= 1;
  }
  renderCalendar();
});

calendarNext?.addEventListener('click', () => {
  currentYearMonth.month += 1;
  if (currentYearMonth.month > 11) {
    currentYearMonth.month = 0;
    currentYearMonth.year += 1;
  }
  renderCalendar();
});

async function loadEvents() {
  try {
    eventsCache = await apiGet('/api/events');
    renderCalendar();
    renderExamsFromEvents();
  } catch (err) {
    console.error(err);
  }
}

// --- Exámenes ---

const examForm = document.getElementById('exam-form');
const examsList = document.getElementById('exams-list');
const examPdfBox = document.getElementById('exam-pdf-box');
const btnGenerateExamPdf = document.getElementById('btn-generate-exam-pdf');
const examStudentIdInput = document.getElementById('exam-student-id');
const examDateDisplay = document.getElementById('exam-date-display');
const examDatePopover = document.getElementById('exam-date-popover');
const examDateCalendar = document.getElementById('exam-date-calendar');
const examTimeDisplay = document.getElementById('exam-time-display');
const examTimePopover = document.getElementById('exam-time-popover');

let examSelectedDate = '';
let examCalendarYearMonth = (() => {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() };
})();

// Estado separado para Fecha de pago (Cuotas)
let feesSelectedDate = '';
let feesCalendarYearMonth = (() => {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() };
})();

function formatDateForDisplay(value) {
  if (!value) return 'Seleccionar fecha';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return 'Seleccionar fecha';
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatTimeForDisplay(value) {
  if (!value) return '';
  return value.slice(0, 5);
}

function renderExamCalendar() {
  if (!examDateCalendar) return;

  renderGenericCalendar(
    examDateCalendar,
    { get value() { return examSelectedDate; }, set value(v) { examSelectedDate = v; } },
    { get value() { return examCalendarYearMonth; }, set value(v) { examCalendarYearMonth = v; } },
    (dateStr) => {
      const hiddenInput = document.getElementById('exam-date');
      hiddenInput.value = dateStr;
      examDateDisplay.textContent = formatDateForDisplay(dateStr);
    },
  );
}

examDateDisplay?.addEventListener('click', () => {
  if (!examDatePopover) return;
  const currentValue = document.getElementById('exam-date').value;
  if (currentValue) {
    examSelectedDate = currentValue;
    const d = new Date(currentValue);
    if (!Number.isNaN(d.getTime())) {
      examCalendarYearMonth = { year: d.getFullYear(), month: d.getMonth() };
    }
  }
  renderExamCalendar();
  examDatePopover.classList.remove('hidden');
});

examDatePopover?.addEventListener('click', (e) => {
  const target = e.target;
  if (target.dataset?.picker === 'date-cancel') {
    examDatePopover.classList.add('hidden');
  } else if (target.dataset?.picker === 'date-apply') {
    const input = document.getElementById('exam-date');
    examDateDisplay.textContent = formatDateForDisplay(input.value || examSelectedDate);
    examDatePopover.classList.add('hidden');
  }
});
// --- Selector de horario (HH/MM en popover) ---

examTimeDisplay?.addEventListener('click', () => {
  if (!examTimePopover) return;
  const hidden = document.getElementById('exam-time');
  const hourInput = document.getElementById('exam-time-hour');
  const minuteInput = document.getElementById('exam-time-minute');
  if (hidden.value) {
    const [h, m] = hidden.value.split(':');
    hourInput.value = h || '';
    minuteInput.value = m || '';
  }
  examTimePopover.classList.remove('hidden');
});

examTimePopover?.addEventListener('click', (e) => {
  const target = e.target;
  if (target.dataset?.picker === 'time-cancel') {
    examTimePopover.classList.add('hidden');
  } else if (target.dataset?.picker === 'time-apply') {
    const hidden = document.getElementById('exam-time');
    const hourInput = document.getElementById('exam-time-hour');
    const minuteInput = document.getElementById('exam-time-minute');

    let hh = (hourInput.value || '').trim();
    let mm = (minuteInput.value || '').trim();

    if (!hh || !mm || isNaN(Number(hh)) || isNaN(Number(mm))) {
      alert('Ingresá una hora válida en formato 24 hs (ej: 18:30).');
      return;
    }

    hh = String(Math.floor(Number(hh))).padStart(2, '0');
    mm = String(Math.floor(Number(mm))).padStart(2, '0');

    const hNum = Number(hh);
    const mNum = Number(mm);
    if (hNum < 0 || hNum > 23 || mNum < 0 || mNum > 59) {
      alert('Hora fuera de rango. Usá 00-23 para horas y 00-59 para minutos.');
      return;
    }

    hidden.value = `${hh}:${mm}`;
    examTimeDisplay.textContent = formatTimeForDisplay(hidden.value);
    examTimePopover.classList.add('hidden');
  }
});

examForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    type: 'exam',
    date: document.getElementById('exam-date').value,
    time: document.getElementById('exam-time').value,
    level: document.getElementById('exam-level').value,
    place: document.getElementById('exam-place').value,
    notes: document.getElementById('exam-notes').value,
    title: 'Examen',
  };

  try {
    await apiSend('/api/events', 'POST', payload);
    examForm.reset();
    loadEvents();
  } catch (err) {
    console.error(err);
  }
});

function renderExamsFromEvents() {
  if (!examsList) return;
  examsList.innerHTML = '';
  const today = new Date();

  const exams = eventsCache
    .filter((e) => e.type === 'exam')
    .filter((e) => {
      // Filtrar sólo exámenes cuya fecha no haya pasado
      if (!e.date) return true;
      const d = new Date(e.date);
      if (Number.isNaN(d.getTime())) return true;
      // mantener exámenes de hoy o a futuro
      return d >= new Date(today.getFullYear(), today.getMonth(), today.getDate());
    })
    .sort((a, b) => {
      const da = new Date(a.date || '9999-12-31');
      const db = new Date(b.date || '9999-12-31');
      if (da.getTime() !== db.getTime()) return da - db;
      return String(a.time || '').localeCompare(String(b.time || ''));
    });

  exams.forEach((ev) => {
    const li = document.createElement('li');
    li.className = 'exams-list-item';
    li.innerHTML = `
      <div class="exam-item-inner">
        <span class="exam-checkbox"></span>
        <span>${ev.date || ''} ${ev.time || ''} - ${ev.level || ''} - ${ev.place || ''}</span>
      </div>
    `;
    li.addEventListener('click', () => selectExam(ev.id, li));
    examsList.appendChild(li);
  });
}

function selectExam(eventId, liElement) {
  if (!examPdfBox || !btnGenerateExamPdf) return;
  examPdfBox.setAttribute('data-event-id', String(eventId));

  const children = examsList?.querySelectorAll('.exams-list-item') || [];
  children.forEach((li) => li.classList.remove('exams-list-item-selected'));
  if (liElement) {
    liElement.classList.add('exams-list-item-selected');
  }

  btnGenerateExamPdf.disabled = false;
}

btnGenerateExamPdf?.addEventListener('click', () => {
  if (!examPdfBox) return;
  const eventId = examPdfBox.getAttribute('data-event-id');
  const studentIdValue = examStudentIdInput?.value || '';
  if (!eventId) {
    alert('Primero seleccioná un examen de la lista.');
    return;
  }
  if (!studentIdValue) {
    alert('Seleccioná un Alumno para generar el PDF.');
    return;
  }

  const url = `/api/exams/${eventId}/inscription-pdf`;

  // Usamos fetch para POST y luego creamos un enlace de descarga
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: Number(studentIdValue) }),
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error('No se pudo generar el PDF (código ' + res.status + ').');
      }
      return res.blob();
    })
    .then((blob) => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'inscripcion_examen.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
    })
    .catch((err) => console.error(err));
});

// --- Cuotas ---

const feesForm = document.getElementById('fees-form');
const feesStatusBody = document.getElementById('fees-status-body');
const btnLoadFees = document.getElementById('btn-load-fees');
const feesStudentNameInput = document.getElementById('fees-student-name');
const feesStudentIdInput = document.getElementById('fees-student-id');
const feesStudentSuggestions = document.getElementById('fees-student-suggestions');
const feesDateDisplay = document.getElementById('fees-date-display');
const feesDatePopover = document.getElementById('fees-date-popover');
const feesDateCalendarEl = document.getElementById('fees-date-calendar');

const examStudentNameInput = document.getElementById('exam-student-name');

function setupStudentNameAutocomplete(inputEl, hiddenEl, suggestionsEl) {
  if (!inputEl || !hiddenEl || !suggestionsEl) return;

  inputEl.addEventListener('input', () => {
    const query = inputEl.value.toLowerCase().trim();
    suggestionsEl.innerHTML = '';
    if (!query || !studentsCache.length) return;

    const matches = studentsCache.filter((s) => (s.full_name || '').toLowerCase().includes(query)).slice(0, 8);
    matches.forEach((s) => {
      const div = document.createElement('div');
      div.className = 'student-suggestion-item';
      const label = s.full_name || `${s.last_name || ''} ${s.first_name || ''}`;
      const belt = s.belt ? ` • ${s.belt.toUpperCase()}` : '';
      div.textContent = `${label}${belt}`;
      div.addEventListener('click', () => {
        inputEl.value = label;
        hiddenEl.value = s.id;
        suggestionsEl.innerHTML = '';
      });
      suggestionsEl.appendChild(div);
    });
  });

  document.addEventListener('click', (e) => {
    if (!suggestionsEl.contains(e.target) && e.target !== inputEl) {
      suggestionsEl.innerHTML = '';
    }
  });
}

async function loadFeesForStudent(studentId) {
  try {
    const data = await apiGet(`/api/fees/${studentId}`);
    if (!feesStatusBody) return;

    const statusText = document.createElement('div');
    const pill = document.createElement('span');
    pill.className = 'status-pill';
    if (data.status === 'al_dia') {
      pill.classList.add('status-pill-ok');
      pill.textContent = 'Al día';
    } else if (data.status === 'sin_registro') {
      pill.classList.add('status-pill-debt');
      pill.textContent = 'Sin registro';
    } else {
      pill.classList.add('status-pill-debt');
      pill.textContent = 'Adeuda';
    }

    statusText.append('Estado: ', pill);

    const last = document.createElement('div');
    last.className = 'text-muted';
    last.textContent = `Último pago: ${data.last_payment || '-'} `;

    const historyTitle = document.createElement('div');
    historyTitle.textContent = 'Historial de pagos:';

    const historyList = document.createElement('ul');
    historyList.className = 'fees-history-list';
    (data.history || []).forEach((h) => {
      const li = document.createElement('li');
      li.textContent = `${h.date} - $${h.amount}`;
      historyList.appendChild(li);
    });

    feesStatusBody.innerHTML = '';
    feesStatusBody.appendChild(statusText);
    feesStatusBody.appendChild(last);
    feesStatusBody.appendChild(historyTitle);
    feesStatusBody.appendChild(historyList);
  } catch (err) {
    console.error(err);
  }
}

btnLoadFees?.addEventListener('click', () => {
  const id = feesStudentIdInput?.value;
  if (!id) return;
  loadFeesForStudent(Number(id));
});

feesForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = feesStudentIdInput?.value;
  if (!id) return;

  const payload = {
    payment_date: document.getElementById('fees-payment-date').value || undefined,
    amount: Number(document.getElementById('fees-amount').value || 0),
  };

  try {
    await apiSend(`/api/fees/${id}`, 'POST', payload);
    loadFeesForStudent(Number(id));
  } catch (err) {
    console.error(err);
  }
});

// Calendario de Fecha de pago (Cuotas)

feesDateDisplay?.addEventListener('click', () => {
  if (!feesDatePopover || !feesDateCalendarEl) return;
  const hidden = document.getElementById('fees-payment-date');
  const currentValue = hidden.value;
  if (currentValue) {
    feesSelectedDate = currentValue;
    const d = new Date(currentValue);
    if (!Number.isNaN(d.getTime())) {
      feesCalendarYearMonth = { year: d.getFullYear(), month: d.getMonth() };
    }
  }

  // Usamos el calendario genérico
  renderGenericCalendar(
    feesDateCalendarEl,
    { get value() { return feesSelectedDate; }, set value(v) { feesSelectedDate = v; } },
    { get value() { return feesCalendarYearMonth; }, set value(v) { feesCalendarYearMonth = v; } },
    (dateStr) => {
      hidden.value = dateStr;
      feesDateDisplay.textContent = formatDateForDisplay(dateStr);
    },
  );

  feesDatePopover.classList.remove('hidden');
});

feesDatePopover?.addEventListener('click', (e) => {
  const target = e.target;
  if (target.dataset?.picker === 'fees-date-cancel') {
    feesDatePopover.classList.add('hidden');
  } else if (target.dataset?.picker === 'fees-date-apply') {
    feesDatePopover.classList.add('hidden');
  }
});

// Carga inicial
loadStudents();
loadEvents();

// Inicializar autocompletados una vez que haya alumnos
setupStudentNameAutocomplete(feesStudentNameInput, feesStudentIdInput, feesStudentSuggestions);
setupStudentNameAutocomplete(examStudentNameInput, examStudentIdInput, document.getElementById('exam-student-suggestions'));
