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

export async function fetchModelBlob(jobId) {
  const { data } = await apiClient.get(`/download/${jobId}`, {
    responseType: "blob",
  });
  return URL.createObjectURL(data);
}

export async function downloadModelFile(jobId) {
  const { data } = await apiClient.get(`/download/${jobId}`, {
    responseType: "blob",
  });
  const blobUrl = URL.createObjectURL(data);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = `${jobId}.glb`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
}
