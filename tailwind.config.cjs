/ /** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx,jsx,js}'],
  theme: {
    extend: {
      colors: {
        tkdRed: '#C62828',
        tkdBlue: '#0D47A1',
        tkdBlack: '#000000',
        tkdWhite: '#FFFFFF',
      },
      fontFamily: {
        tkd: ['"Ruslan Display"', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        martial: '0 0 0 3px rgba(0,0,0,1)',
      },
      borderRadius: {
        martial: '0.25rem',
      },
      backgroundImage: {
        'brush-red': 'linear-gradient(120deg, rgba(198,40,40,0.25), transparent)',
        'brush-blue': 'linear-gradient(240deg, rgba(13,71,161,0.25), transparent)',
      },
    },
  },
  plugins: [],
};
