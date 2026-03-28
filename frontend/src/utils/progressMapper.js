const stageOrder = ["extracting_frames", "generating_geometry", "applying_pbr"];

export function stageState(currentStage, stageKey) {
  const currentIndex = stageOrder.indexOf(currentStage);
  const targetIndex = stageOrder.indexOf(stageKey);

  if (currentIndex === -1) {
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
