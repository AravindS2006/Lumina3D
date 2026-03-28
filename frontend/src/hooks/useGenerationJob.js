import { useCallback, useMemo, useState } from "react";

import { fetchStatus, getDownloadUrl, submitGeneration } from "../services/generationApi";
import { usePolling } from "./usePolling";

const initialState = {
  phase: "idle",
  progress: 0,
  stage: "queued",
  message: "Upload a video or image set to begin.",
  error: null,
  jobId: null,
  downloadUrl: null,
};

export function useGenerationJob() {
  const [state, setState] = useState(initialState);

  const isPolling = useMemo(() => {
    return !!state.jobId && !["complete", "failed"].includes(state.phase);
  }, [state.jobId, state.phase]);

  const poll = useCallback(async () => {
    if (!state.jobId) {
      return;
    }
    try {
      const status = await fetchStatus(state.jobId);
      setState((prev) => ({
        ...prev,
        phase: status.status,
        progress: status.progress,
        stage: status.stage,
        message: status.message,
        error: status.error || null,
        downloadUrl:
          status.status === "complete" ? getDownloadUrl(status.job_id) : prev.downloadUrl,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        phase: "failed",
        error: error.message || "Polling failed",
      }));
    }
  }, [state.jobId]);

  usePolling(poll, isPolling);

  const startJob = useCallback(async (payload) => {
    setState({
      ...initialState,
      phase: "queued",
      message: "Submitting generation request",
    });
    try {
      const data = await submitGeneration(payload);
      setState((prev) => ({ ...prev, phase: data.status, jobId: data.job_id }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        phase: "failed",
        error: error.message || "Failed to start generation job",
      }));
    }
  }, []);

  const reset = useCallback(() => setState(initialState), []);

  return { state, startJob, reset };
}
