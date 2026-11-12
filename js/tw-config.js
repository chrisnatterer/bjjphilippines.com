// Shared Tailwind theme for every page except the homepage (which has its own CSS).
// Dark palette that matches the homepage. The colour names are kept from the old
// light theme, but their *values* are now dark-theme roles:
//   bg-ink / bg-ink-2 / bg-night  page, alternate and deep-dark backgrounds
//   bg-surface                    cards
//   text-warm-dark / text-cream   main (light) text
//   text-warm-gray(-light)        muted text
//   border-warm-light             hairlines
//   text-accent                   readable terracotta for text on dark
tailwind.config = {
  theme: {
    extend: {
      colors: {
        ink: '#0b0908',
        'ink-2': '#13100e',
        night: '#070605',
        surface: '#1a1512',
        cream: '#f3eee8',
        'cream-light': '#241d19',
        'warm-dark': '#f3eee8',
        'warm-mid': '#1a1512',
        'warm-light': '#2c2420',
        'warm-gray': '#a3968b',
        'warm-gray-light': '#76695f',
        terracotta: '#c0462b',
        'terracotta-light': '#e0765c',
        accent: '#e0765c',
        gold: '#c89b3c',
        'gold-light': '#dbb44e',
      },
      fontFamily: {
        display: ['Archivo', 'Arial', 'sans-serif'],
        body: ['Barlow', 'system-ui', 'sans-serif'],
        label: ['"Barlow Condensed"', 'system-ui', 'sans-serif'],
      },
    },
  },
};
