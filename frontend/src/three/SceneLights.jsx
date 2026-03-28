import { Environment } from "@react-three/drei";

export default function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 8, 4]} intensity={1.1} color="#f3f7ff" />
      <Environment preset="studio" />
    </>
  );
}
