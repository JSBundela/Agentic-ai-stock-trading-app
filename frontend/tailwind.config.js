/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                obsidian: {
                    950: '#08080A',
                    900: '#0C0D11',
                    800: '#16171D',
                    700: '#23252E',
                },
                glass: {
                    DEFAULT: 'rgba(255, 255, 255, 0.03)',
                    surface: 'rgba(23, 26, 33, 0.6)',
                    border: 'rgba(255, 255, 255, 0.08)',
                    hover: 'rgba(255, 255, 255, 0.05)',
                },
                trading: {
                    profit: '#00FF9D',
                    loss: '#FF3D71',
                    neutral: '#3D7BFF',
                },
                brand: {
                    DEFAULT: '#6366F1',
                    glow: 'rgba(99, 102, 241, 0.3)',
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            borderRadius: {
                'xl': '12px',
                '2xl': '20px',
                '3xl': '32px',
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
        },
    },
    plugins: [],
}
