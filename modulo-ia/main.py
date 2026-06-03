from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Importações essenciais do Cliente MCP
from mcp import ClientSession
from mcp.client.sse import sse_client

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
# ==========================================
@tool
def buscar_jogos_banco_local(descricao: str) -> str:
    """Use esta ferramenta PRIMEIRO para buscar jogos no banco de dados local com base na descrição, história ou características solicitadas pelo usuário."""
    print(f"🔧 [Tool Executada] RAG: Buscando por '{descricao}'")
    return "Encontrei 'The Witcher 3' e 'Stardew Valley' no banco de dados que combinam com a descrição."

# Transformamos a tool em assíncrona para não travar o FastAPI
@tool
async def consultar_mcp_externo(nome_jogo: str) -> str:
    """Use esta ferramenta APENAS para buscar dados ao vivo em APIs externas, como o preço atualizado de um jogo específico na Steam."""
    print(f"🔧 [Tool Executada] MCP: Consultando dados vivos de '{nome_jogo}'")
    
    # URL do container MCP (ajuste 'mcp-gateway' para o nome do container no seu Docker/rede)
    url_mcp = "http://mcp-gateway:8000/sse" 
    
    try:
        # Conecta ao servidor MCP via rede
        async with sse_client(url_mcp) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                
                # Chama a ferramenta que configuramos lá no server.py
                # Substitua "check_services_health" pelo nome exato do @mcp.tool() que deseja usar
                resultado = await session.call_tool("check_services_health", {})
                
                # Retorna o texto extraído para o Gemma 2 interpretar
                return resultado.content[0].text
                
    except Exception as e:
        return f"Aviso: Não foi possível obter os dados via MCP. Erro: {str(e)}"

ferramentas = [buscar_jogos_banco_local, consultar_mcp_externo]

# ==========================================
# 3. CONFIGURAÇÃO DO LLM E DO AGENTE
# ==========================================
llm = ChatOllama(model="gemma2", base_url="http://ollama:11434")

prompt_agente = ChatPromptTemplate.from_messages([
    ("system", "Você é o Game-Radar, um assistente especializado em recomendar jogos. Use as ferramentas disponíveis para buscar informações antes de responder."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agente = create_tool_calling_agent(llm, ferramentas, prompt_agente)
executor_agente = AgentExecutor(agent=agente, tools=ferramentas, verbose=True)

# ==========================================
# 4. ROTA PRINCIPAL DA API
# ==========================================
@app.post("/api/chat")
async def orquestrar_chat(req: RequisicaoRecomendacao):
    try:
        print("\n--- Iniciando Raciocínio do Gemma 2 ---")
        
        pergunta_completa = f"O usuário pediu: {req.descricaoLivre}. Tags aplicadas: {req.tags}"
        
        # MUDANÇA CRÍTICA: Usar 'ainvoke' (assíncrono) permite que o LangChain 
        # execute nossa ferramenta consultar_mcp_externo corretamente!
        resposta = await executor_agente.ainvoke({"input": pergunta_completa})
        
        return {
            "remetente": "ia",
            "texto": resposta["output"]
        }
        
    except Exception as e:
        print(f"Erro Crítico: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro no raciocínio da IA.")