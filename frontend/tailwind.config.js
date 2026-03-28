/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        shell: "#090d12",
        frost: "rgba(255,255,255,0.12)",
      },
      boxShadow: {
        glass: "0 18px 50px rgba(0,0,0,0.3)",
      },
      backgroundImage: {
        mesh:
          "radial-gradient(40rem 28rem at 15% 20%, rgba(55, 125, 255, 0.24), transparent 70%), radial-gradient(38rem 26rem at 85% 80%, rgba(42, 216, 183, 0.22), transparent 70%), radial-gradient(30rem 20rem at 50% 45%, rgba(240, 190, 78, 0.16), transparent 70%)",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"],
      },
    },
  },
  plugins: [],
};
