import { apiClient } from "./apiClient";

const localFallbackBases = ["http://127.0.0.1:8000", "http://localhost:8000"];

function normalizeBase(base) {
  return (base || "").replace(/\/+$/, "");
}

function activeBase() {
  return normalizeBase(apiClient.defaults.baseURL);
}

async function isHealthy(baseURL) {
  if (!baseURL) {
    return false;
  }
  try {
    const response = await apiClient.get(`${baseURL}/healthz`, {
      timeout: 6000,
      headers: { "ngrok-skip-browser-warning": "69420" },
    });
    if (response.status !== 200) {
      return false;
    }
    const payload = response.data || {};
    if (typeof payload !== "object") {
      return false;
    }
    return payload.runtime_probe === true;
  } catch {
    return false;
  }
}

async function ensureReachableBackend() {
  const current = activeBase();
  if (await isHealthy(current)) {
    return current;
  }

  for (const fallback of localFallbackBases) {
    if (fallback === current) {
      continue;
    }
    if (await isHealthy(fallback)) {
      apiClient.defaults.baseURL = fallback;
      return fallback;
    }
  }

  return current;
}

function mapAxiosError(error, action) {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  const base = activeBase() || "<unset-base-url>";

  if (status === 404) {
    return `${action} failed (404) at ${base}. Verify VITE_API_BASE_URL and backend /healthz.`;
  }
  if (status === 405) {
    return `${action} failed (405). Endpoint exists but method is wrong.`;
  }
  if (status === 502 || status === 503 || status === 504) {
    return `${action} failed (${status}). Tunnel/backend may be offline.`;
  }
  return detail || error?.message || `${action} failed at ${base}`;
}

function staleBackendError() {
  const base = activeBase() || "<unset-base-url>";
  return `Backend at ${base} is reachable but outdated. Restart backend from latest code. /healthz must include runtime_probe=true.`;
}

export async function fetchRuntimeProbe() {
  const resolved = await ensureReachableBackend();
  if (!(await isHealthy(resolved))) {
    throw new Error(staleBackendError());
  }
  try {
    const { data } = await apiClient.get("/debug/runtime");
    return data;
  } catch (error) {
    const status = error?.response?.status;
    if (status === 404) {
      throw new Error(
        "Backend /debug/runtime is missing (404). You are likely running an older backend build that can produce placeholder sphere output. Restart backend from the latest project files."
      );
    }
    throw new Error(mapAxiosError(error, "Runtime probe"));
  }
}

export async function submitGeneration(payload) {
  await ensureReachableBackend();

  const formData = new FormData();
  formData.append("profile", payload.profile || "balanced");

  if (payload.mode === "video") {
    formData.append("video", payload.files[0]);
  } else {
    payload.files.forEach((file) => formData.append("images", file));
    if (payload.viewLabels && Object.keys(payload.viewLabels).length > 0) {
      formData.append("view_labels", JSON.stringify(payload.viewLabels));
    }
  }

  try {
    const { data } = await apiClient.post("/generate", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error) {
    throw new Error(mapAxiosError(error, "Generate request"));
  }
}

export async function fetchStatus(jobId) {
  await ensureReachableBackend();
  try {
    const { data } = await apiClient.get(`/status/${jobId}`);
    return data;
  } catch (error) {
    throw new Error(mapAxiosError(error, "Status polling"));
  }
}

export function getDownloadUrl(jobId) {
  return `${activeBase()}/download/${jobId}`;
}

export async function fetchModelBlob(jobId) {
  await ensureReachableBackend();
  try {
    const { data } = await apiClient.get(`/download/${jobId}`, {
      responseType: "blob",
    });
    return URL.createObjectURL(data);
  } catch (error) {
    throw new Error(mapAxiosError(error, "Model preview"));
  }
}

export async function downloadModelFile(jobId) {
  await ensureReachableBackend();
  try {
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
  } catch (error) {
    throw new Error(mapAxiosError(error, "Download"));
  }
}

export { mapAxiosError, ensureReachableBackend };
