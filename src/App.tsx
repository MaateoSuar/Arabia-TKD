import { useEffect, useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { StudentsPage } from './pages/StudentsPage';
import { CalendarPage } from './pages/CalendarPage';
import { ExamsPage } from './pages/ExamsPage';
import { FeesPage } from './pages/FeesPage';

function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window === 'undefined') return 'dark';
    const stored = window.localStorage.getItem('tkd-theme');
    return stored === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    if (typeof document === 'undefined') return;
    const body = document.body;
    body.classList.remove('theme-dark', 'theme-light');
    body.classList.add(theme === 'light' ? 'theme-light' : 'theme-dark');
    window.localStorage.setItem('tkd-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div
      className={`min-h-screen flex flex-col ${
        theme === 'light' ? 'bg-neutral-50 text-neutral-900' : 'bg-neutral-600 text-tkdWhite'
      }`}
    >
      <header className="border-b-4 border-tkdBlack bg-gradient-to-r from-tkdRed/80 via-black to-tkdBlue/80 shadow-martial">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div>
            <h1 className="font-tkd text-2xl sm:text-3xl tracking-widest text-tkdWhite drop-shadow-[0_0_6px_rgba(0,0,0,0.9)] uppercase">
              Escuela de Taekwondo
            </h1>
            <p className="font-body text-xs sm:text-sm text-neutral-200 uppercase tracking-[0.25em]">
              Arabia TKD
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex flex-col items-end text-right">
              <span className="text-[10px] tracking-[0.35em] uppercase text-neutral-300">
                Sobre todo, ser el ejemplo
              </span>
            </span>
            <button
              type="button"
              onClick={toggleTheme}
              className="martial-button text-[10px] py-1 px-3 bg-neutral-900 text-neutral-100 border-neutral-700"
           >
              {theme === 'dark' ? '☀ Modo claro' : '☾ Modo oscuro'}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-3 sm:px-4 py-4 sm:py-6">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/alumnos" element={<StudentsPage />} />
          <Route path="/calendario" element={<CalendarPage />} />
          <Route path="/examenes" element={<ExamsPage />} />
          <Route path="/cuotas" element={<FeesPage />} />
        </Routes>
      </main>

      <nav className="sticky bottom-0 z-20 border-t-4 border-tkdBlack bg-neutral-800/95 backdrop-blur flex sm:justify-center">
        <div className="flex w-full max-w-6xl">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-[10px] uppercase tracking-[0.18em] border-r border-neutral-800 ${
                isActive ? 'text-tkdRed font-semibold bg-neutral-900' : 'text-neutral-300'
              }`
            }
          >
            <span className="text-xs mb-1">🏠</span>
            Hoja
          </NavLink>

          <NavLink
            to="/alumnos"
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-[10px] uppercase tracking-[0.18em] border-r border-neutral-800 ${
                isActive ? 'text-tkdRed font-semibold bg-neutral-900' : 'text-neutral-300'
              }`
            }
          >
            <span className="text-xs mb-1">👨‍🎓</span>
            Alumnos
          </NavLink>

          <NavLink
            to="/calendario"
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-[10px] uppercase tracking-[0.18em] border-r border-neutral-800 ${
                isActive ? 'text-tkdRed font-semibold bg-neutral-900' : 'text-neutral-300'
              }`
            }
          >
            <span className="text-xs mb-1">📅</span>
            Calendario
          </NavLink>

          <NavLink
            to="/examenes"
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-[10px] uppercase tracking-[0.18em] border-r border-neutral-800 ${
                isActive ? 'text-tkdRed font-semibold bg-neutral-900' : 'text-neutral-300'
              }`
            }
          >
            <span className="text-xs mb-1">📝</span>
            Exámenes
          </NavLink>

          <NavLink
            to="/cuotas"
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-[10px] uppercase tracking-[0.18em] ${
                isActive ? 'text-tkdRed font-semibold bg-neutral-900' : 'text-neutral-300'
              }`
            }
          >
            <span className="text-xs mb-1">💸</span>
            Cuotas
          </NavLink>

          <button
            type="button"
            onClick={toggleTheme}
            className="px-3 flex flex-col items-center justify-center text-[10px] uppercase tracking-[0.18em] text-neutral-300 border-l border-neutral-800"
          >
            <span className="text-xs mb-1">{theme === 'dark' ? '☀' : '☾'}</span>
            {theme === 'dark' ? 'Claro' : 'Oscuro'}
          </button>
        </div>
      </nav>
    </div>
  );
}

export default App;
