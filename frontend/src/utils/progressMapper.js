const stageOrder = [
  "waiting_gpu",
  "preparing",
  "extracting_frames",
  "loading_geometry",
  "generating_geometry",
  "cleanup_geometry",
  "loading_texture",
  "applying_pbr",
  "complete",
  "failed",
];

export function stageState(currentStage, stageKey) {
  const currentIndex = stageOrder.indexOf(currentStage);
  const targetIndex = stageOrder.indexOf(stageKey);

  if (currentStage === "failed") {
    return stageKey === "failed" ? "active" : "done";
  }

  if (currentIndex === -1 || targetIndex === -1) {
    return "pending";
  }
  if (targetIndex < currentIndex) {
    return "done";
  }
  if (targetIndex === currentIndex) {
    return "active";
  }
  return "pending";
}
