import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import DashboardV2 from "./DashboardV2.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <DashboardV2 />
  </StrictMode>
);
