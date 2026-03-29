import { apiClient } from "./apiClient";

const localFallbackBases = ["http://127.0.0.1:8000", "http://localhost:8000"];

function normalizeBase(base) {
  return (base || "").replace(/\/+$/, "");
}

function isLoopbackBase(base) {
  if (!base) {
    return true;
  }

  try {
    const { hostname } = new URL(base);
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
  } catch {
    return false;
  }
}

function isNgrokBase(base) {
  if (!base) {
    return false;
  }

  try {
    const { hostname } = new URL(base);
    return hostname.toLowerCase().includes("ngrok");
  } catch {
    return false;
  }
}

function activeBase() {
  return normalizeBase(apiClient.defaults.baseURL);
}

export async function ensureReachableBackend() {
  const current = activeBase();

  if (!isLoopbackBase(current)) {
    return current;
  }

  for (const fallback of localFallbackBases) {
    if (fallback === current) {
      continue;
    }
    try {
      const response = await apiClient.get(`${fallback}/healthz`, {
        timeout: 4000,
        headers: { "ngrok-skip-browser-warning": "69420" },
      });
      if (response.status === 200 && response.data?.runtime_probe === true) {
        apiClient.defaults.baseURL = fallback;
        return fallback;
      }
    } catch {
      // not reachable
    }
  }

  return current;
}

export async function fetchHealth() {
  await ensureReachableBackend();
  const base = activeBase();
  try {
    const { data } = await apiClient.get(`${base}/healthz`, {
      headers: { "ngrok-skip-browser-warning": "69420" },
      timeout: 8000,
    });
    if (data?.runtime_probe !== true) {
      throw new Error(staleBackendError(base));
    }
    return data;
  } catch (error) {
    if (error instanceof Error && error.message.includes("runtime_probe=true")) {
      throw error;
    }
    throw new Error(mapAxiosError(error, "Health check"));
  }
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
    if (isNgrokBase(base)) {
      return `${action} failed (${status}) at ${base}. Backend worker likely crashed under high RAM during model download (check job warnings and Colab logs). Restart runtime, rerun notebook cells, and keep RAM below 95% before generation.`;
    }
    return `${action} failed (${status}) at ${base}. Backend may be offline.`;
  }

  const networkCode = error?.code;
  const networkMessage = String(error?.message || "").toLowerCase();
  if (!status && (networkCode === "ERR_NETWORK" || networkMessage.includes("network error"))) {
    if (isNgrokBase(base)) {
      return [
        `${action} could not reach ${base}.`,
        "",
        "Fix steps:",
        "1) In Colab, check RAM usage and uvicorn logs for worker restart/OOM.",
        "2) Restart runtime if RAM was above 95% during download.",
        "3) Re-run notebook cells to recreate backend and tunnel.",
        "4) Update frontend/.env with fresh URL and restart `npm run dev`.",
      ].join("\n");
    }
    return `${action} could not reach backend at ${base}. Start FastAPI on port 8000.`;
  }
  return detail || error?.message || `${action} failed at ${base}`;
}

function staleBackendError(base = activeBase() || "<unset-base-url>") {
  return `Backend at ${base} is reachable but outdated. Restart backend from latest code. /healthz must include runtime_probe=true.`;
}

export async function fetchRuntimeProbe() {
  await ensureReachableBackend();
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

export { mapAxiosError };
