import { useState } from "react";
import Dashboard from "./screens/Dashboard";

export default function App() {
  const [apiBase, setApiBase] = useState("http://localhost:8000");

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#f5f7f5" }}>
      <header
        style={{
          background: "#1b5e20",
          color: "white",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>🌾</span>
          <strong style={{ fontSize: 18 }}>KisanGuard AI — Agricultural Intelligence Station</strong>
        </div>
        <label style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
          <span>API Endpoint:</span>
          <input
            value={apiBase}
            placeholder="http://localhost:8000"
            onChange={(e) => setApiBase(e.target.value)}
            style={{
              padding: "5px 10px",
              borderRadius: 4,
              border: "1px solid rgba(255, 255, 255, 0.4)",
              background: "rgba(255, 255, 255, 0.15)",
              color: "white",
              width: 220,
              fontSize: 13,
            }}
          />
        </label>
      </header>
      <main style={{ padding: 24 }}>
        <Dashboard apiBase={apiBase} />
      </main>
    </div>
  );
}
