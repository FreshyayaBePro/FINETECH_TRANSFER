module.exports = {
  content: [
    '../templates/**/*.html',
    '../../templates/**/*.html',
    '../../**/templates/**/*.html',
    '../../**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#667eea',
          dark: '#764ba2',
        },
        success: {
          light: '#10b981',
          dark: '#059669',
        },
        danger: {
          light: '#ef4444',
          dark: '#dc2626',
        },
      },
    },
  },
  plugins: [],
}