import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Form.css"; // Importando o CSS!

export default function Form() {
  const navigate = useNavigate();

  const opcoesFiltros = {
    generos: [
      "FPS",
      "Battle Royale",
      "FPA",
      "PVP",
      "RTS",
      "MOBA",
      "RPG",
      "MMORPG",
      "Ação",
      "Aventura",
      "Estratégia",
      "Esportes",
      "Simulação",
      "Puzzle",
      "Luta",
      "Stealth",
      "Sobrevivência",
      "Corrida",
    ].sort(),
    plataformas: ["PC", "PlayStation", "XBOX", "Nintendo Switch"].sort(),
    processadores: [
      "Intel Core i3",
      "Intel Core i5",
      "Intel Core i7",
      "AMD Ryzen 3",
      "AMD Ryzen 5",
      "AMD Ryzen 7",
    ].sort(),
    memoria: ["2GB", "4GB", "8GB", "16GB", "32GB", "64GB"],
    placas: [
      "Nvidia GTX 1650",
      "Nvidia RTX 3060",
      "Nvidia RTX 4060",
      "AMD RX 6600",
      "AMD RX 7600",
    ].sort(),
  };

  const [opcoesSelecionadas, setOpcoesSelecionadas] = useState({
    generos: [],
    plataformas: [],
    processadores: [],
    memoria: [],
    placas: [],
  });

  const [inputs, setInputs] = useState({
    generos: "",
    plataformas: "",
    processadores: "",
    memoria: "",
    placas: "",
  });

  const [erro, setErro] = useState("");

  const adicionarTag = (campo, valor) => {
    const listaDisponivel = opcoesFiltros[campo];
    const jaSelecionados = opcoesSelecionadas[campo];

    if (listaDisponivel.includes(valor) && !jaSelecionados.includes(valor)) {
      setOpcoesSelecionadas({
        ...opcoesSelecionadas,
        [campo]: [...jaSelecionados, valor],
      });
      setInputs({ ...inputs, [campo]: "" });
    }
  };

  const removerTag = (campo, valorParaRemover) => {
    setOpcoesSelecionadas({
      ...opcoesSelecionadas,
      [campo]: opcoesSelecionadas[campo].filter(
        (item) => item !== valorParaRemover,
      ),
    });
  };

  // LÓGICA DE EXIBIÇÃO: Só renderiza campos de hardware se "PC" estiver selecionado
  const camposParaRenderizar = Object.keys(opcoesFiltros).filter((campo) => {
    const camposDeHardware = ["processadores", "memoria", "placas"];

    // Se for um campo de hardware, verifica se a plataforma "PC" foi escolhida
    if (camposDeHardware.includes(campo)) {
      return opcoesSelecionadas.plataformas.includes("PC");
    }

    // Se não for campo de hardware (ex: gêneros e plataformas), exibe sempre
    return true;
  });

  const descricoes = [
    "Estou em um mundo aberto, posso explorar o mapa procurando itens ou materiais para melhora-los",
    "Seleciono um carro e exploro o mundo, participando de eventos e corridas",
    "Compro ou ganho cartas para montar um deck e enfrentar uma batalha",
    "Preciso desvendar enigmas para avançar a próxima fase",
  ];

  
  const obterDescricaoAleatoria = (() => {
    const indice = Math.floor(Math.random() * descricoes.length);
    descricoes[indice];
  }); 


  const [placeholderDesc] = useState(() => obterDescricaoAleatoria());

  const [faixas, setFaixas] = useState({
    precoMin: "",
    precoMax: "",
    anoLancamentoMin: "",
    anoLancamentoMax: "",
  });

  // Função simples para atualizar as faixas
  const lidarComMudancaFaixa = (campo, valor) => {
    setFaixas({
      ...faixas,
      [campo]: valor,
    });
  };

  {
    /* Captura a descricao */
  }
  const [descricao, setDescricao] = useState("");

  const lidarComEnvio = (e) => {
    e.preventDefault();
    if (
      opcoesSelecionadas.plataformas.length === 0 &&
      opcoesSelecionadas.generos.length === 0
    ) {
      setErro(
        "Por favor, selecione pelo menos uma Plataforma ou um Gênero para podermos te recomendar algo!",
      );
      return;
    }

    const dadosEnvio = {
      tags: opcoesSelecionadas || {},
      faixa: {
        preco: {
          min: faixas.precoMin ? Number(faixas.precoMin) : 0,
          max: faixas.precoMax ? Number(faixas.precoMax) : 9999,
        },
        ano: {
          min: faixas.anoLancamentoMin ? Number(faixas.anoLancamentoMin) : 1980,
          max: faixas.anoLancamentoMax ? Number(faixas.anoLancamentoMax) : new Date().getFullYear,
        },
      } || {},
      descricaoLivre: descricao || "",
    };

    console.log("Dados prontos para a API:", dadosEnvio);
    navigate("/chat", { state: { filtrosIniciais: dadosEnvio } });
  };

  return (
    <form onSubmit={lidarComEnvio} className="formulario-container">
      <h2 className="formulario-titulo">Formulário de Jogos</h2>

      {camposParaRenderizar.map((campo) => (
        <div key={campo} className="campo-filtro">
          <label className="label-filtro">{campo}:</label>

          <div className="tags-container">
            {opcoesSelecionadas[campo].map((item) => (
              <span key={item} className="tag-item">
                {item}
                <button
                  type="button"
                  onClick={() => removerTag(campo, item)}
                  className="btn-remover-tag"
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <input
            type="text"
            list={`lista-${campo}`}
            value={inputs[campo]}
            placeholder={`Filtrar por ${campo}...`}
            onChange={(e) => {
              setInputs({ ...inputs, [campo]: e.target.value });
              adicionarTag(campo, e.target.value);
            }}
            className="input-filtro"
          />

          <datalist id={`lista-${campo}`}>
            {opcoesFiltros[campo]
              .filter((opcao) => !opcoesSelecionadas[campo].includes(opcao))
              .map((opcao) => (
                <option key={opcao} value={opcao} />
              ))}
          </datalist>
        </div>
      ))}

      {/* Faixa de Preço */}
      <div className="campo-filtro">
        <label className="label-filtro">Faixa de Preço (R$):</label>
        <div className="input-faixa">
          <input
            type="number"
            min="0"
            placeholder="Mínimo (ex: 0)"
            className="input-filtro"
            value={faixas.precoMin}
            onChange={(e) => lidarComMudancaFaixa("precoMin", e.target.value)}
          />
        </div>
        <span className="entre-faixa">até</span>
        <div className="input-faixa">
          <input
            type="number"
            min="0"
            placeholder="Máximo (ex: 200)"
            className="input-filtro"
            value={faixas.precoMax}
            onChange={(e) => lidarComMudancaFaixa("precoMax", e.target.value)}
          />
        </div>
      </div>

      {/* Faixa de Lançamento */}
      <div className="campo-filtro">
        <label className="label-filtro">Faixa de Lançamento (Ano):</label>
        <div className="input-faixa">
          <input
            type="number"
            min="1980"
            max="2026"
            placeholder="Mínimo (ex: 2010)"
            className="input-filtro"
            value={faixas.anoLancamentoMin}
            onChange={(e) =>
              lidarComMudancaFaixa("anoLancamentoMin", e.target.value)
            }
          />
        </div>
        <span className="entre-faixa">até</span>
        <div className="input-faixa">
          <input
            type="number"
            min="1980"
            max="2026"
            placeholder="Mínimo (ex: 2020)"
            className="input-filtro"
            value={faixas.anoLancamentoMax}
            onChange={(e) =>
              lidarComMudancaFaixa("anoLancamentoMax", e.target.value)
            }
          />
        </div>
      </div>

      {/* Descrição par buscar um jogo. */}
      <div className="campo-filtro">
        <label className="label-filtro">Descrição do jogo:</label>

        <input
          type="text"
          placeholder={`Ex: ${placeholderDesc}`}
          className="input-filtro"
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
        />
      </div>

      {/* Exibe a mensagem de erro se ela existir */}
      {erro && <p className="mensagem-erro">{erro}</p>}

      <button type="submit" className="btn-submit">
        Buscar Jogos
      </button>
    </form>
  );
}
