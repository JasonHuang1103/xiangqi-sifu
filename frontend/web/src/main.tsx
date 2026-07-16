import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

function Bootstrap() {
  return <main>Xiangqi Sifu</main>;
}

const root = document.getElementById("root");

if (root === null) {
  throw new Error("Missing application root");
}

createRoot(root).render(
  <StrictMode>
    <Bootstrap />
  </StrictMode>,
);
