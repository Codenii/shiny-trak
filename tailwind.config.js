module.exports = {
    content: ["./templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                bg: { DEFAULT: '#0D0B1A', surface: '#130D28', card: '#1A1035' },
                primary: { DEFAULT: '#7209B7', hover: '#560BAD', light: '#B5179E' },
                accent: { DEFUALT: '#4361EE', light: '#4895EF', muted: '#4CC9F0' },
                danger: { DEFAULT: '#F72585', hover: '#B5179E' },
                gold: '#FBBF24'
            }
        }
    },
    plugins: []
}