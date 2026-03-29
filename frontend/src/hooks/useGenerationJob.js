import { useCallback, useEffect, useMemo, useState } from "react";

import {
  downloadModelFile,
  fetchRuntimeProbe,
  fetchHealth,
  fetchModelBlob,
  fetchStatus,
  getDownloadUrl,
  submitGeneration,
} from "../services/generationApi";
import { usePolling } from "./usePolling";

const initialState = {
  phase: "idle",
  progress: 0,
  stage: "queued",
  message: "Upload a video or image set to begin.",
  error: null,
  jobId: null,
  downloadUrl: null,
  modelUrl: null,
  profile: "balanced",
  engineTier: null,
  warnings: [],
  failureCode: null,
  stageTimings: {},
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
        profile: status.profile || prev.profile,
        engineTier: status.engine_tier || prev.engineTier,
        warnings: status.warnings || [],
        failureCode: status.failure_code || null,
        stageTimings: status.stage_timings || {},
        error: status.error || null,
        downloadUrl:
          status.status === "complete" ? getDownloadUrl(status.job_id) : prev.downloadUrl,
      }));

    } catch (error) {
      setState((prev) => ({
        ...prev,
        phase: "failed",
        error: error.message || "Status polling failed",
      }));
    }
  }, [state.jobId]);

  usePolling(poll, isPolling);

  const startJob = useCallback(async (payload) => {
    setState({
      ...initialState,
      phase: "queued",
      message: "Running backend preflight checks (/healthz + /debug/runtime)",
      profile: payload.profile || "balanced",
    });
    try {
      const health = await fetchHealth();
      if (health?.cuda_available === false) {
        throw new Error(
          "Backend is running without CUDA GPU. Switch notebook to Colab GPU runtime or set LUMINA_REQUIRE_CUDA=0 only for debugging."
        );
      }

      const probe = await fetchRuntimeProbe();
      const checks = probe?.module_checks || {};
      const shapeOk = String(checks["hy3dgen.shapegen"] || "").startsWith("ok");
      const tex20Ok = String(checks["hy3dgen.texgen"] || "").startsWith("ok");
      const tex21Ok = String(checks["hy3dpaint.textureGenPipeline"] || "").startsWith("ok");

      if (!shapeOk) {
        throw new Error(
          `Backend runtime not ready: hy3dgen.shapegen -> ${checks["hy3dgen.shapegen"] || "missing"}`
        );
      }

      if (!tex20Ok && !tex21Ok) {
        throw new Error(
          `Backend runtime not ready for texturing: hy3dpaint.textureGenPipeline -> ${checks["hy3dpaint.textureGenPipeline"] || "missing"}; hy3dgen.texgen -> ${checks["hy3dgen.texgen"] || "missing"}`
        );
      }

      if (!tex21Ok && tex20Ok) {
        const cacheInfo = probe?.cache_info || {};
        const warmupHint = cacheInfo.hunyuan2mv_present
          ? ""
          : "First run is downloading Hunyuan3D-2mv weights. This can take several minutes.";
        setState((prev) => ({
          ...prev,
          warnings: [
            ...(prev.warnings || []),
            "Hunyuan3D-2.1 paint is unavailable. Backend will fallback to hunyuan20_paint tier.",
            ...(warmupHint ? [warmupHint] : []),
          ],
        }));
      }

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

  const hydrateModelPreview = useCallback(async () => {
    if (!state.jobId || state.phase !== "complete" || state.modelUrl) {
      return;
    }
    try {
      const blobUrl = await fetchModelBlob(state.jobId);
      setState((prev) => ({ ...prev, modelUrl: blobUrl }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error.message || "Could not load generated model preview",
      }));
    }
  }, [state.jobId, state.modelUrl, state.phase]);

  useEffect(() => {
    hydrateModelPreview();
  }, [hydrateModelPreview]);

  const download = useCallback(async () => {
    if (!state.jobId) {
      return;
    }
    try {
      await downloadModelFile(state.jobId);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error.message || "Download failed",
      }));
    }
  }, [state.jobId]);

  const reset = useCallback(() => {
    setState((prev) => {
      if (prev.modelUrl && prev.modelUrl.startsWith("blob:")) {
        URL.revokeObjectURL(prev.modelUrl);
      }
      return initialState;
    });
  }, []);

  return { state, startJob, reset, hydrateModelPreview, download };
}
