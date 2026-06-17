"""
main.py — Orquestrador de IA (Game-Radar)

RAG real (rag.py + ChromaDB) com agente ReAct.
Usa create_react_agent (compatível com langchain==0.2.6 + ChatOllama).
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

# Importa as funções do módulo RAG
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
    Use esta ferramenta para buscar jogos no banco de dados local
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


ferramentas = [buscar_jogos_banco_local]


# ─────────────────────────────────────────────
# 3. CONFIGURAÇÃO DO LLM E DO AGENTE
# ─────────────────────────────────────────────

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "gemma2")
llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

template_react = '''Você é o Game-Radar, um assistente especializado em recomendar jogos eletrônicos.
Você tem acesso às seguintes ferramentas:

{tools}

REGRAS IMPORTANTES:
1. Use 'buscar_jogos_banco_local' UMA ÚNICA VEZ para encontrar jogos relevantes.
2. Com os resultados retornados, vá direto para a Final Answer. NÃO repita a busca.

Na Final Answer:
- Recomende os 2 ou 3 jogos mais adequados ao perfil do usuário
- Explique por que cada jogo combina com o pedido
- Use tom amigável e entusiasmado, como um amigo gamer dando dicas
- Responda em português brasileiro

Use o seguinte formato rigorosamente:

Question: a pergunta que você deve responder
Thought: você deve sempre pensar sobre o que fazer a seguir
Action: a ação a tomar, deve ser EXATAMENTE UMA das ferramentas: [{tool_names}]
Action Input: a entrada de dados para a ação
Observation: o resultado da ação
Thought: Eu agora sei a resposta final
Final Answer: a resposta final e amigável para o usuário em português brasileiro

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
    max_iterations=4,
    early_stopping_method="generate",  # gera resposta ao invés de mensagem de erro genérica
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

        # Monta as tags
        tags_limpas = [f"{chave}: {', '.join(valores)}" for chave, valores in req.tags.items() if valores]
        texto_tags  = " | ".join(tags_limpas) if tags_limpas else "Nenhuma tag específica"

        # Monta a pergunta com todos os dados do formulário
        pergunta_completa = (
            f"O usuário está procurando um jogo com a seguinte descrição: '{req.descricaoLivre}'. "
            f"Tags/preferências aplicadas: {texto_tags}. "
            f"Faixa de preço desejada: R${req.faixa.preco.min:.0f} a R${req.faixa.preco.max:.0f}. "
            f"Faixa de lançamento: {req.faixa.ano.min:.0f} a {req.faixa.ano.max:.0f}. "
            f"Recomende os melhores jogos para este perfil."
        )

        print(f"Enviando para a IA: {pergunta_completa}")

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