import axios from "axios";

const rawBaseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const baseURL = rawBaseURL
  .trim()
  .replace(/^['"]+|['"]+$/g, "")
  .replace(/\/+$/, "");

export const apiClient = axios.create({
  baseURL,
  timeout: 120000,
  headers: {
    "ngrok-skip-browser-warning": "69420",
  },
});
