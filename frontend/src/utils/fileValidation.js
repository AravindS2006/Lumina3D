const IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"];
const VIDEO_TYPES = ["video/mp4"];

export function classifyFiles(fileList) {
  const files = Array.from(fileList ?? []);
  const videos = files.filter((file) => VIDEO_TYPES.includes(file.type));
  const images = files.filter((file) => IMAGE_TYPES.includes(file.type));

  if (videos.length > 1) {
    return { ok: false, message: "Please upload only one MP4 file." };
  }

  if (videos.length === 1 && images.length > 0) {
    return { ok: false, message: "Upload either one MP4 or multiple images." };
  }

  if (videos.length === 0 && images.length < 2) {
    return { ok: false, message: "Upload one MP4 or at least two images." };
  }

  if (videos.length === 1) {
    return { ok: true, mode: "video", files: [videos[0]] };
  }

  return { ok: true, mode: "images", files: images };
}
