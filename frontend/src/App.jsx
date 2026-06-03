import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import Form from "./components/Form";
import Chat from "./components/Chat";
import Sidebar from "./components/Sidebar";

function App() {
  return (
    <BrowserRouter>
      {/* A Sidebar fica parada aqui, persistente em todas as telas */}
      <Sidebar />

      {/* Esta <main> é a área da direita, que vai exibir as telas dinâmicas */}
      <main style={{ flexGrow: 1, height: "100vh", overflowY: "auto" }}>
        <Routes>
          <Route path="/" element={<Navigate to="/form" replace />} />
          <Route path="/form" element={<Form />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
