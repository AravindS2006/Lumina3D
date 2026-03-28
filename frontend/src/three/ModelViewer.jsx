import { ContactShadows, OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense, useMemo } from "react";

import SceneLights from "./SceneLights";

function Model({ modelUrl }) {
  const scene = useGLTF(modelUrl).scene;
  const cloned = useMemo(() => scene.clone(), [scene]);
  return <primitive object={cloned} />;
}

function Placeholder() {
  return (
    <mesh>
      <icosahedronGeometry args={[0.8, 1]} />
      <meshStandardMaterial color="#8db8ff" roughness={0.55} metalness={0.2} />
    </mesh>
  );
}

export default function ModelViewer({ modelUrl }) {
  return (
    <Canvas
      camera={{ position: [2.3, 1.6, 2.6], fov: 50 }}
      shadows
      dpr={[1, 1.8]}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={["#090d12"]} />
      <fog attach="fog" args={["#090d12", 4, 12]} />
      <SceneLights />
      <Suspense fallback={<Placeholder />}>
        {modelUrl ? <Model key={modelUrl} modelUrl={modelUrl} /> : <Placeholder />}
      </Suspense>
      <ContactShadows position={[0, -1.1, 0]} opacity={0.55} scale={7} blur={2.6} far={4.2} />
      <OrbitControls
        enableDamping
        makeDefault
        minDistance={1.4}
        maxDistance={6.5}
        maxPolarAngle={Math.PI * 0.75}
        enablePan={false}
      />
    </Canvas>
  );
}
