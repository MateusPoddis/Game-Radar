import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import Form from "./components/Form";
import Chat from "./components/Chat";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rota inicial: Faz o redirecionamento */}
        <Route path="/" element={<Navigate to="/form" replace />} />

        {/* Rota de formulário: Mostra o formulário */}
        <Route path="/form" element={<Form />} />

        {/* Rota do chat: Mostra a conversa pós recomendação */}
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
