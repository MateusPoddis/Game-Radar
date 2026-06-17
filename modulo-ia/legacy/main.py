import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

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
    return "Resultados do banco de dados: 'Fortnite' (Battle Royale ágil com construção), 'Albion Online' (MMORPG focado em economia) e 'The Witcher 3' (Mundo aberto com excelente história)."

@tool
async def consultar_mcp_externo(nome_jogo: str) -> str:
    """Use esta ferramenta APENAS para buscar dados ao vivo em APIs externas, como o preço atualizado de um jogo específico na Steam."""
    print(f"🔧 [Tool Executada] MCP: Consultando dados vivos de '{nome_jogo}'")

    url_mcp = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8000/sse")

    try:
        async with sse_client(url_mcp) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                resultado = await session.call_tool("check_services_health", {})
                return resultado.content[0].text

    except Exception as e:
        return f"Aviso: Não foi possível obter os dados via MCP. Erro: {str(e)}"

ferramentas = [buscar_jogos_banco_local, consultar_mcp_externo]

# ==========================================
# 3. CONFIGURAÇÃO DO LLM E DO AGENTE (ReAct)
# ==========================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

# Deixei as regras mais rígidas para evitar que o Gemma 2 fique em loop
template_react = '''Responda a solicitação do usuário da melhor forma possível. Você é o Game-Radar, um assistente especializado em recomendar jogos.
Você tem acesso às seguintes ferramentas:

{tools}

REGRAS IMPORTANTES:
1. Se a ferramenta 'buscar_jogos_banco_local' retornar jogos, NÃO use a ferramenta novamente para refinar a busca. Use os jogos que ela já retornou.
2. Analise os resultados e, na próxima etapa, forneça a Final Answer imediatamente.

Use o seguinte formato rigorosamente:

Question: a pergunta que você deve responder
Thought: você deve sempre pensar sobre o que fazer a seguir
Action: a ação a tomar, deve ser EXATAMENTE UMA das ferramentas: [{tool_names}]
Action Input: a entrada de dados para a ação
Observation: o resultado da ação
... (este ciclo Thought/Action/Action Input/Observation pode se repetir N vezes)
Thought: Eu agora sei a resposta final
Final Answer: a resposta final e amigável para o usuário

Comece!

Question: {input}
Thought:{agent_scratchpad}'''

prompt_agente = PromptTemplate.from_template(template_react)

agente = create_react_agent(llm, ferramentas, prompt_agente)
executor_agente = AgentExecutor(
    agent=agente, 
    tools=ferramentas, 
    verbose=True, 
    handle_parsing_errors="Tente novamente com o formato correto, ou retorne Final Answer imediatamente.",
    max_iterations=4, # Aumentei de 2 para 4 para não dar Timeout
    early_stopping_method="force" 
)

# ==========================================
# 4. ROTA PRINCIPAL DA API
# ==========================================
@app.post("/api/chat")
async def orquestrar_chat(req: RequisicaoRecomendacao):
    try:
        print("\n--- Iniciando Raciocínio do Gemma 2 ---")
        
        tags_limpas = [f"{chave}: {', '.join(valores)}" for chave, valores in req.tags.items() if valores]
        texto_tags = " | ".join(tags_limpas) if tags_limpas else "Nenhuma tag específica"
        
        pergunta_completa = f"Pedido do usuário: '{req.descricaoLivre}'. Filtros de busca: {texto_tags}."
        print(f"Enviando para a IA: {pergunta_completa}")
        
        resposta = await executor_agente.ainvoke({"input": pergunta_completa})
        
        return {
            "remetente": "ia",
            "texto": resposta["output"]
        }
        
    except Exception as e:
        print(f"Erro Crítico: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro no raciocínio da IA.")