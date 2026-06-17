"""
main_merged.py — Orquestrador de IA (Game-Radar)

Versão mesclada: RAG real (rag.py + ChromaDB) + MCP robusto com variáveis de ambiente.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Importações do Cliente MCP
from mcp import ClientSession
from mcp.client.sse import sse_client

# Importa as funções do módulo RAG real
from rag import buscar_com_filtros_formulario, buscar_jogos_rag


# ─────────────────────────────────────────────
# 1. MODELOS DE ENTRADA (FastAPI)
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# 2. FERRAMENTAS DO AGENTE (Tools)
# ─────────────────────────────────────────────

# Estado global para passar os dados do formulário para dentro das tools
_contexto_requisicao: RequisicaoRecomendacao | None = None


@tool
def buscar_jogos_banco_local(descricao: str) -> str:
    """
    Use esta ferramenta PRIMEIRO para buscar jogos no banco de dados local
    com base na descrição, história, gênero ou características solicitadas.
    Retorna os jogos mais relevantes encontrados semanticamente.
    """
    print(f"🔧 [Tool] RAG: Buscando por '{descricao[:60]}...'")

    global _contexto_requisicao

    # Se temos o contexto completo do formulário, usamos os filtros também
    if _contexto_requisicao:
        return buscar_com_filtros_formulario(
            descricao_livre=descricao,
            tags=_contexto_requisicao.tags,
            faixa_ano={
                "min": _contexto_requisicao.faixa.ano.min,
                "max": _contexto_requisicao.faixa.ano.max,
            },
        )

    # Fallback: busca simples por descrição
    return buscar_jogos_rag(descricao=descricao, n_resultados=5)


@tool
async def consultar_mcp_externo(nome_jogo: str) -> str:
    """
    Use esta ferramenta APÓS buscar no banco local para obter dados ao vivo
    de APIs externas, como preço atual na Steam e disponibilidade em serviços
    de assinatura (Game Pass, PS Plus). Recebe o nome exato do jogo.
    """
    print(f"🔧 [Tool] MCP: Consultando dados vivos de '{nome_jogo}'")

    # Usa variável de ambiente com fallback (vindo do main.py)
    url_mcp = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8000/sse")

    try:
        async with sse_client(url_mcp) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                resultado = await session.call_tool("check_services_health", {})
                return resultado.content[0].text

    except Exception as e:
        return f"Aviso: Não foi possível obter dados ao vivo via MCP. Erro: {str(e)}"


ferramentas = [buscar_jogos_banco_local, consultar_mcp_externo]


# ─────────────────────────────────────────────
# 3. CONFIGURAÇÃO DO LLM E DO AGENTE
# ─────────────────────────────────────────────

# Usa variáveis de ambiente com fallback (vindo do main.py)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        """Você é o Game-Radar, um assistente especializado em recomendar jogos eletrônicos.

Seu fluxo de raciocínio OBRIGATÓRIO:
1. SEMPRE use a ferramenta 'buscar_jogos_banco_local' primeiro para encontrar jogos relevantes.
2. Para cada jogo promissor, use 'consultar_mcp_externo' para verificar preços e disponibilidade.
3. Com base em todos os dados coletados, elabore uma recomendação personalizada e humanizada.

Na sua resposta final:
- Recomende os 2 ou 3 jogos mais adequados ao perfil do usuário
- Explique por que cada jogo combina com o pedido dele
- Informe o preço atual e onde o jogo está disponível (assinaturas, plataformas)
- Use um tom amigável e entusiasmado, como um amigo gamer dando dicas
- Responda em português brasileiro
""",
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agente = create_tool_calling_agent(llm, ferramentas, prompt_agente)
executor_agente = AgentExecutor(
    agent=agente,
    tools=ferramentas,
    verbose=True,
    handle_parsing_errors="Tente novamente com o formato correto, ou retorne Final Answer imediatamente.",
    max_iterations=4,
    early_stopping_method="force",
)


# ─────────────────────────────────────────────
# 4. ROTA PRINCIPAL DA API
# ─────────────────────────────────────────────
@app.post("/api/chat")
async def orquestrar_chat(req: RequisicaoRecomendacao):
    global _contexto_requisicao

    try:
        print("\n─── Iniciando Raciocínio do Gemma 2 ───")

        # Salva o contexto para as tools acessarem os filtros do formulário
        _contexto_requisicao = req

        # Limpa e monta as tags (vindo do main.py)
        tags_limpas = [f"{chave}: {', '.join(valores)}" for chave, valores in req.tags.items() if valores]
        texto_tags = " | ".join(tags_limpas) if tags_limpas else "Nenhuma tag específica"

        # Monta a pergunta com todos os dados do formulário
        pergunta_completa = (
            f"O usuário está procurando um jogo com a seguinte descrição: '{req.descricaoLivre}'. "
            f"Tags/preferências aplicadas: {texto_tags}. "
            f"Faixa de preço desejada: R${req.faixa.preco.min:.0f} a R${req.faixa.preco.max:.0f}. "
            f"Faixa de lançamento: {req.faixa.ano.min:.0f} a {req.faixa.ano.max:.0f}. "
            f"Recomende os melhores jogos para este perfil."
        )

        print(f"Enviando para a IA: {pergunta_completa}")

        # ainvoke assíncrono — permite que a tool MCP rode corretamente
        resposta = await executor_agente.ainvoke({"input": pergunta_completa})

        return {
            "remetente": "ia",
            "texto": resposta["output"],
        }

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro no raciocínio da IA.")

    finally:
        # Limpa o contexto após cada requisição
        _contexto_requisicao = None