import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AskProvider } from "./context/AskContext";
import { AuthProvider } from "./context/AuthContext";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AskProvider>
          <App />
        </AskProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
