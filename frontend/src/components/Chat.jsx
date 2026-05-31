import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

export default function Chat() {
  const location = useLocation();

  // Resgata os filtros que vieram da tela anterior
  const filtros = location.state?.filtrosIniciais;

  // O "Cérebro" da tela: um array que guarda o histórico da conversa
  const [mensagens, setMensagens] = useState([]);
  const [inputUsuario, setInputUsuario] = useState("");

  // Efeito disparado assim que a tela abre
  useEffect(() => {
    if (filtros) {
      // Cria a primeira mensagem do sistema confirmando o recebimento
      const mensagemInicial = {
        remetente: "ia",
        texto: "Recebi seus filtros! Buscando jogos para recomendar ...",
      };
      setMensagens([mensagemInicial]);

      // AQUI entrará a sua chamada (fetch/axios) para o FastAPI!
      // Você enviará os filtros e receberá a recomendação do Ollama.
    }
  }, [filtros]);

  const enviarMensagem = (e) => {
    e.preventDefault();
    if (!inputUsuario.trim()) return;

    //  Adiciona a mensagem do usuário na tela
    const novaMensagemUsuario = { remetente: "usuario", texto: inputUsuario };
    setMensagens((prev) => [...prev, novaMensagemUsuario]);

    // Limpa o campo
    setInputUsuario("");

    // 3. AQUI você enviará 'inputUsuario' para a IA e adicionará a resposta dela depois.
  };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h2>Chat de Recomendação</h2>

      {/* Caixa de mensagens */}
      <div
        style={{
          height: "400px",
          border: "1px solid #ccc",
          overflowY: "auto",
          padding: "10px",
          marginBottom: "10px",
        }}
      >
        {mensagens.map((msg, index) => (
          <div
            key={index}
            style={{
              textAlign: msg.remetente === "usuario" ? "right" : "left",
              margin: "10px 0",
            }}
          >
            <span
              style={{
                background: msg.remetente === "usuario" ? "#007bff" : "#e9ecef",
                color: msg.remetente === "usuario" ? "white" : "black",
                padding: "8px 12px",
                borderRadius: "15px",
                display: "inline-block",
                maxWidth: "80%",
              }}
            >
              {msg.texto}
            </span>
          </div>
        ))}
      </div>

      {/* Input de digitação */}
      <form onSubmit={enviarMensagem} style={{ display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={inputUsuario}
          onChange={(e) => setInputUsuario(e.target.value)}
          placeholder="Diga o que achou da recomendação..."
          style={{ flex: 1, padding: "10px" }}
        />
        <button type="submit" style={{ padding: "10px 20px" }}>
          Enviar
        </button>
      </form>
    </div>
  );
}
