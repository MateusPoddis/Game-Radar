import { useNavigate } from "react-router-dom";
import logo from "../assets/control.png"; // Ajuste o caminho da imagem se precisar
import "./Sidebar.css";

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <aside className="sidebar-container">
      {/* Imagem do Radar */}
      <img src={logo} alt="Game-Radar Logo" className="sidebar-logo" />
      
      {/* Botão para iniciar nova recomendação */}
      <button 
        className="btn-novo-chat"
        onClick={() => navigate("/form")}
      >
        + Novo Chat
      </button>
    </aside>
  );
}