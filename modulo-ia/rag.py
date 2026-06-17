"""
rag.py — Módulo de Busca Semântica (RAG)

Expõe a função `buscar_jogos_rag` que é importada e registrada
como uma Tool do LangChain no main.py do Orquestrador.

Fluxo:
    1. Recebe a descrição livre do usuário
    2. Gera o embedding da descrição (via Ollama)
    3. Busca os N jogos mais similares no ChromaDB
    4. Retorna um texto formatado para o LLM interpretar
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# ─────────────────────────────────────────────
# CONFIGURAÇÕES (mesmas do ingest.py)
# ─────────────────────────────────────────────
CHROMA_HOST      = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT      = int(os.getenv("CHROMA_PORT", 8005))
COLLECTION_NAME  = "games"
OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL  = "nomic-embed-text"

# ─────────────────────────────────────────────
# CONEXÃO COM CHROMADB (singleton para não reconectar a cada busca)
# ─────────────────────────────────────────────
_collection = None

def _get_collection():
    """Retorna a collection do ChromaDB, criando a conexão uma única vez."""
    global _collection
    if _collection is None:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        embed_fn = embedding_functions.OllamaEmbeddingFunction(
            url=f"{OLLAMA_BASE_URL}/api/embeddings",
            model_name=EMBEDDING_MODEL,
        )
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn,
        )
    return _collection


# ─────────────────────────────────────────────
# FUNÇÃO PRINCIPAL DE BUSCA
# ─────────────────────────────────────────────
def buscar_jogos_rag(
    descricao: str,
    n_resultados: int = 5,
    filtros: dict | None = None,
) -> str:
    """
    Busca jogos no banco vetorial por similaridade semântica.

    Args:
        descricao:    Texto livre descrevendo o jogo desejado pelo usuário.
                      Ex: "jogo relaxante com foco em narrativa, sem combate intenso"
        n_resultados: Quantidade de jogos a retornar (padrão: 5).
        filtros:      Filtros opcionais de metadados para restringir a busca.
                      Ex: {"platforms": {"$contains": "PC"}}
                      Ex: {"release_year": {"$gte": 2015}}

    Returns:
        String formatada com os jogos encontrados, pronta para ser
        enviada ao LLM como contexto.
    """
    print(f"🔍 [RAG] Buscando por: '{descricao[:80]}...'")

    try:
        collection = _get_collection()

        kwargs = {
            "query_texts":  [descricao],
            "n_results":    n_resultados,
            "include":      ["documents", "metadatas", "distances"],
        }

        # Aplica filtros de metadados se fornecidos
        if filtros:
            kwargs["where"] = filtros

        results = collection.query(**kwargs)

        # Sem resultados
        if not results["documents"] or not results["documents"][0]:
            return "Nenhum jogo encontrado no banco de dados para a descrição fornecida."

        # ─── Formata a resposta para o LLM ───
        jogos_encontrados = []
        documentos = results["documents"][0]
        metadados  = results["metadatas"][0]
        distancias = results["distances"][0]

        for i, (doc, meta, dist) in enumerate(zip(documentos, metadados, distancias), 1):
            # Converte distância cosseno em score de similaridade (0-100%)
            similaridade = round((1 - dist) * 100, 1)

            jogo_str = (
                f"--- Jogo {i} (Similaridade: {similaridade}%) ---\n"
                f"{doc}\n"
            )
            jogos_encontrados.append(jogo_str)

        contexto = (
            f"Encontrei {len(jogos_encontrados)} jogos relevantes no banco de dados:\n\n"
            + "\n".join(jogos_encontrados)
        )

        print(f"✅ [RAG] {len(jogos_encontrados)} jogos retornados.")
        return contexto

    except Exception as e:
        erro = f"Erro ao consultar o banco vetorial: {str(e)}"
        print(f"❌ [RAG] {erro}")
        return erro


# ─────────────────────────────────────────────
# FUNÇÃO DE BUSCA COM FILTROS DE FORMULÁRIO
# ─────────────────────────────────────────────
def buscar_com_filtros_formulario(
    descricao_livre: str,
    tags: dict,
    faixa_ano: dict | None = None,
) -> str:
    """
    Versão que aceita os dados direto do formulário React.
    Combina a busca semântica com filtros opcionais de metadados.

    Args:
        descricao_livre: Campo de texto livre do formulário.
        tags:            Dict com listas de tags do formulário.
                         Ex: {"genero": ["RPG", "Aventura"], "plataforma": ["PC"]}
        faixa_ano:       Faixa de anos. Ex: {"min": 2015, "max": 2024}
    """
    # Enriquece a descrição com as tags para melhorar a busca semântica
    descricao_enriquecida = descricao_livre

    if tags:
        todas_tags = []
        for categoria, valores in tags.items():
            if valores:
                todas_tags.extend(valores)
        if todas_tags:
            descricao_enriquecida += f". Gêneros/temas preferidos: {', '.join(todas_tags)}"

    # Monta filtros de metadados (ChromaDB usa sintaxe própria)
    filtros = None
    if faixa_ano and faixa_ano.get("min") and faixa_ano.get("max"):
        filtros = {
            "$and": [
                {"release_year": {"$gte": int(faixa_ano["min"])}},
                {"release_year": {"$lte": int(faixa_ano["max"])}},
            ]
        }

    return buscar_jogos_rag(
        descricao=descricao_enriquecida,
        n_resultados=5,
        filtros=filtros,
    )
