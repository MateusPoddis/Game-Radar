import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "./Chat.css";

export default function Chat() {
  const location = useLocation();

  // Resgata os filtros que vieram da tela do formulário
  const filtros = location.state?.filtrosIniciais;

  // Histórico da conversa no Chat
  const [mensagens, setMensagens] = useState([]);
  const [inputUsuario, setInputUsuario] = useState("");

  // 1. Efeito disparado assim que a tela abre (Envia os filtros do formulário)
  useEffect(() => {
    if (filtros) {
      const reinforcementMensagem = {
        remetente: "ia",
        texto: "Recebi seus filtros! Buscando jogos para recomendar...",
      };
      setMensagens([reinforcementMensagem]);

      // CHAMADA PARA O API GATEWAY (Utiliza o IP local estável para Linux)
      fetch("http://127.0.0.1:8080/api/v1/recomendacao", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(filtros),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Erro ao falar com o Gateway");
          return res.json();
        })
        .then((data) => {
          let respostaFormatada = "Aqui estão os jogos que recomendo para você:\n\n";
          
          if (data.recomendacoes && data.recomendacoes.length > 0) {
            data.recomendacoes.forEach((jogo) => {
              respostaFormatada += `🎮 ${jogo.titulo} \n💰 Preço: ${jogo.preco_cheapshark} \n📍 Plataforma: ${jogo.plataforma}\n\n`;
            });
          } else {
            respostaFormatada = "Não encontrei nenhuma recomendação para esses filtros.";
          }

          setMensagens((prev) => [
            ...prev,
            { remetente: "ia", texto: respostaFormatada },
          ]);
        })
        .catch((err) => {
          setMensagens((prev) => [
            ...prev,
            { remetente: "ia", texto: `Erro de conexão: ${err.message}` },
          ]);
        });
    }
  }, [filtros]);

  // 2. Função disparada ao digitar mensagens extras no chat
  const enviarMensagem = async (e) => {
    e.preventDefault();
    if (!inputUsuario.trim()) return;

    const novaMensagemUsuario = { remetente: "usuario", texto: inputUsuario };
    setMensagens((prev) => [...prev, novaMensagemUsuario]);
    
    const textoDigitado = inputUsuario;
    setInputUsuario("");

    try {
      const res = await fetch("http://127.0.0.1:8080/api/v1/recomendacao", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tags: {},
          faixa: { preco: { min: 0, max: 9999 }, ano: { min: 1980, max: 2026 } },
          descricaoLivre: textoDigitado,
        }),
      });

      const data = await res.json();
      
      let respostaFormatada = `Entendi o seu comentário! Baseado em "${textoDigitado}", aqui estão novas opções:\n\n`;
      if (data.recomendacoes) {
        data.recomendacoes.forEach((jogo) => {
          respostaFormatada += `🎮 ${jogo.titulo} (${jogo.preco_cheapshark})\n`;
        });
      }

      setMensagens((prev) => [
        ...prev,
        { remetente: "ia", texto: respostaFormatada },
      ]);
    } catch (err) {
      setMensagens((prev) => [
        ...prev,
        { remetente: "ia", texto: "Ih, me perdi na conexão com o Gateway." },
      ]);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-mensagens">
        <h2 style={{ textAlign: "center", marginBottom: "20px" }}>Chat de Recomendação</h2>
        
        {mensagens.map((msg, index) => (
          <div
            key={index}
            style={{
              textAlign: msg.remetente === "usuario" ? "right" : "left",
              margin: "10px 0",
              whiteSpace: "pre-line"
            }}
          >
            <span
              style={{
                background: msg.remetente === "usuario" ? "#28a745" : "#f4f3ec",
                color: msg.remetente === "usuario" ? "white" : "black",
                padding: "12px 18px",
                borderRadius: "20px",
                display: "inline-block",
                maxWidth: "80%",
                boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
              }}
            >
              {msg.texto}
            </span>
          </div>
        ))}
      </div>

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