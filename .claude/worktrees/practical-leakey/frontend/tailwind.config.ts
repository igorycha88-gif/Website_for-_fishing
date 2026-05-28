import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          deepBlue: '#1a3a52',
          sea: '#00b4d8',
        },
        secondary: {
          sand: '#f4a460',
          darkGray: '#2d3436',
        },
        accent: {
          orange: '#ff6b6b',
          green: '#2ecc71',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
export default config;
