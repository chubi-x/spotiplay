module.exports = {
  content: ['./src/**/*.{html,js}'],  // adjust to your project paths
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
    // etc.
  ],
}
