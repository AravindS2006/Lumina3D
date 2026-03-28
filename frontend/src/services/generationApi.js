import { apiClient } from "./apiClient";

export async function submitGeneration(payload) {
  const formData = new FormData();

  if (payload.mode === "video") {
    formData.append("video", payload.files[0]);
  } else {
    payload.files.forEach((file) => formData.append("images", file));
  }

  const { data } = await apiClient.post("/generate", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchStatus(jobId) {
  const { data } = await apiClient.get(`/status/${jobId}`);
  return data;
}

export function getDownloadUrl(jobId) {
  return `${apiClient.defaults.baseURL}/download/${jobId}`;
}
