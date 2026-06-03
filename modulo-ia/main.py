from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. MODELOS DE ENTRADA (FastAPI)
# ==========================================
class FaixaValor(BaseModel):
    min: float
    max: float

class Faixas(BaseModel):
    preco: FaixaValor
    ano: FaixaValor

class RequisicaoRecomendacao(BaseModel):
    tags: Dict[str, List[str]]
    faixa: Faixas
    descricaoLivre: str

app = FastAPI(title="Orquestrador Game-Radar - Gemma 2")

# ==========================================
# 2. FERRAMENTAS DO AGENTE (Tools)
# As docstrings ("""...""") são cruciais. É nelas que o Gemma 2 lê o que a ferramenta faz!
# ==========================================
@tool
def buscar_jogos_banco_local(descricao: str) -> str:
    """Use esta ferramenta PRIMEIRO para buscar jogos no banco de dados local com base na descrição, história ou características solicitadas pelo usuário."""
    print(f"🔧 [Tool Executada] RAG: Buscando por '{descricao}'")
    # Aqui vai a integração real com o ChromaDB/FAISS no futuro
    return "Encontrei 'The Witcher 3' e 'Stardew Valley' no banco de dados que combinam com a descrição."

@tool
def consultar_mcp_externo(nome_jogo: str) -> str:
    """Use esta ferramenta APENAS para buscar dados ao vivo em APIs externas, como o preço atualizado de um jogo específico na Steam."""
    print(f"🔧 [Tool Executada] MCP: Consultando dados vivos de '{nome_jogo}'")
    # Aqui vai o request.get() para o seu servidor MCP no futuro
    return f"O preço atual de {nome_jogo} é R$ 150,00."

# Agrupa as ferramentas que o Agente pode usar
ferramentas = [buscar_jogos_banco_local, consultar_mcp_externo]

# ==========================================
# 3. CONFIGURAÇÃO DO LLM E DO AGENTE
# ==========================================
# Aponta para o container do Ollama na rede interna do Docker (porta 11434)
llm = ChatOllama(model="gemma2", base_url="http://ollama:11434")

# Prompt que ensina o Agente a se comportar
prompt_agente = ChatPromptTemplate.from_messages([
    ("system", "Você é o Game-Radar, um assistente especializado em recomendar jogos. Use as ferramentas disponíveis para buscar informações antes de responder."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"), # Espaço onde a IA anota os resultados das ferramentas
])

# Cria o "motor" do Agente e o executor que roda o loop de chamadas
agente = create_tool_calling_agent(llm, ferramentas, prompt_agente)
executor_agente = AgentExecutor(agent=agente, tools=ferramentas, verbose=True)

# ==========================================
# 4. ROTA PRINCIPAL DA API
# ==========================================
@app.post("/api/chat")
async def orquestrar_chat(req: RequisicaoRecomendacao):
    try:
        print("\n--- Iniciando Raciocínio do Gemma 2 ---")
        
        # Junta a descrição livre com as tags para formar a pergunta completa
        pergunta_completa = f"O usuário pediu: {req.descricaoLivre}. Tags aplicadas: {req.tags}"
        
        # O executor invoca o Gemma 2. A IA vai decidir sozinha quais @tools rodar!
        resposta = executor_agente.invoke({"input": pergunta_completa})
        
        return {
            "remetente": "ia",
            "texto": resposta["output"]
        }
        
    except Exception as e:
        print(f"Erro Crítico: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro no raciocínio da IA.")