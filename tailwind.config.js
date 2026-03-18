module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#2C2A4A", surface: "#1E1C35", card: "#252341" },
        primary: { DEFAULT: "#7FDEFF", hover: "#60C8E8", light: "#A8EEFF" },
        accent: { DEFAULT: "#7FDEFF", light: "#A8EEFF", muted: "#907AD6" },
        danger: { DEFAULT: "#F72585", hover: "#B5179E" },
        gold: "#FBBF24",
        text: { DEFAULT: "#7FDEFF", muted: "#907AD6" },
      },
      zIndex: {
        60: "60",
        70: "70",
      },
    },
  },
  plugins: [],
};
