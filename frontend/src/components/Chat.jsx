import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "./Chat.css"

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
    <div className="chat-container">
      {/* Caixa de mensagens */}
      <div className="chat-mensagens">
        <h2 style={{ textAlign: "center", marginBottom: "20px" }}>Chat de Recomendação</h2>
        
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
                background: msg.remetente === "usuario" ? "#28a745" : "#f4f3ec",
                color: msg.remetente === "usuario" ? "white" : "black",
                padding: "12px 18px",
                borderRadius: "20px", // Balões de conversa suaves
                display: "inline-block",
                maxWidth: "80%",
                boxShadow: "0 2px 5px rgba(0,0,0,0.05)", // Uma sombra quase invisível
              }}
            >
              {msg.texto}
            </span>
          </div>
        ))}
      </div>

      {/* Input de digitação na base */}
      <form onSubmit={enviarMensagem} className="chat-input-area">
        <input
          type="text"
          value={inputUsuario}
          onChange={(e) => setInputUsuario(e.target.value)}
          placeholder="Diga o que achou da recomendação..."
          className="input"
        />
        <button type="submit" className="submit">
          Enviar
        </button>
      </form>
    </div>
  );
}
