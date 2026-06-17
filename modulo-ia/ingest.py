"""
ingest.py — Populador do Banco Vetorial (RAG)

Este script busca jogos na API da Twitch (IGDB), transforma cada jogo
em um "documento de texto rico" e grava os embeddings no ChromaDB.

Execute uma única vez (ou sempre que quiser atualizar o catálogo):
    python ingest.py

Variáveis de ambiente necessárias (.env):
    TWITCH_CLIENT_ID
    TWITCH_CLIENT_SECRET
"""

import os
import time
import requests
from dotenv import load_dotenv
import chromadb

load_dotenv()

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÕES
# ─────────────────────────────────────────────
TWITCH_CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
IGDB_API_URL         = "https://api.igdb.com/v4"

CHROMA_HOST     = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT     = int(os.getenv("CHROMA_PORT", 8005))
COLLECTION_NAME = "games"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL = "nomic-embed-text"

BATCH_SIZE  = 100
TOTAL_GAMES = 500


# ─────────────────────────────────────────────
# 2. AUTENTICAÇÃO NA TWITCH / IGDB
# ─────────────────────────────────────────────
def get_twitch_token() -> str:
    print("🔑 Obtendo token da Twitch...")
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id":     TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type":    "client_credentials",
        },
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("✅ Token obtido com sucesso.")
    return token


# ─────────────────────────────────────────────
# 3. BUSCA DE JOGOS NA IGDB
# ─────────────────────────────────────────────
def fetch_games_batch(token: str, offset: int) -> list[dict]:
    headers = {
        "Client-ID":     TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    query = f"""
        fields 
            name, 
            summary, 
            storyline,
            genres.name, 
            themes.name,
            game_modes.name,
            player_perspectives.name,
            rating,
            rating_count,
            first_release_date,
            platforms.name,
            involved_companies.company.name,
            involved_companies.developer,
            keywords.name;
        where rating > 60 
            & rating_count > 20 
            & summary != null
            & version_parent = null;
        sort rating_count desc;
        limit {BATCH_SIZE};
        offset {offset};
    """

    resp = requests.post(f"{IGDB_API_URL}/games", headers=headers, data=query)
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────────────────────
# 4. TRANSFORMAÇÃO: JOGO → DOCUMENTO DE TEXTO
# ─────────────────────────────────────────────
def game_to_document(game: dict) -> str:
    name      = game.get("name", "Desconhecido")
    summary   = game.get("summary", "")
    storyline = game.get("storyline", "")

    genres       = ", ".join(g.get("name", "") for g in game.get("genres", []) if isinstance(g, dict))
    themes       = ", ".join(t.get("name", "") for t in game.get("themes", []) if isinstance(t, dict))
    modes        = ", ".join(m.get("name", "") for m in game.get("game_modes", []) if isinstance(m, dict))
    keywords     = ", ".join(k.get("name", "") for k in game.get("keywords", [])[:15] if isinstance(k, dict))
    platforms    = ", ".join(p.get("name", "") for p in game.get("platforms", []) if isinstance(p, dict))
    perspectives = ", ".join(p.get("name", "") for p in game.get("player_perspectives", []) if isinstance(p, dict))

    devs = [
        c["company"]["name"]
        for c in game.get("involved_companies", [])
        if isinstance(c, dict) and isinstance(c.get("company"), dict) and c.get("developer")
    ]
    developer = ", ".join(devs) if devs else "Desconhecido"

    rating       = game.get("rating", 0)
    rating_str   = f"{rating:.1f}/100" if rating else "Sem avaliação"
    release_ts   = game.get("first_release_date")
    release_year = str(time.gmtime(release_ts).tm_year) if release_ts else ""

    doc = f"""Jogo: {name}

Descrição: {summary}

{f'História: {storyline}' if storyline else ''}

Gêneros: {genres or 'Não informado'}
Temas: {themes or 'Não informado'}
Modos de jogo: {modes or 'Não informado'}
Perspectiva do jogador: {perspectives or 'Não informado'}
Palavras-chave: {keywords or 'Não informado'}
Plataformas: {platforms or 'Não informado'}
Desenvolvedor: {developer}
Ano de lançamento: {release_year or 'Não informado'}
Avaliação: {rating_str}
"""
    return doc.strip()


def game_to_metadata(game: dict) -> dict:
    rating       = game.get("rating", 0) or 0
    release_ts   = game.get("first_release_date")
    release_year = time.gmtime(release_ts).tm_year if release_ts else 0

    return {
        "name":         game.get("name", ""),
        "rating":       round(float(rating), 1),
        "release_year": int(release_year),
        "genres":       ", ".join(g.get("name", "") for g in game.get("genres", []) if isinstance(g, dict)),
        "platforms":    ", ".join(p.get("name", "") for p in game.get("platforms", []) if isinstance(p, dict)),
        "themes":       ", ".join(t.get("name", "") for t in game.get("themes", []) if isinstance(t, dict)),
    }


# ─────────────────────────────────────────────
# 5. GERAÇÃO DE EMBEDDINGS VIA OLLAMA
# ─────────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    """
    Gera o embedding de um texto chamando o Ollama diretamente via HTTP.
    Tenta o endpoint novo (/api/embed) e cai no antigo (/api/embeddings) se falhar.
    """
    # Endpoint novo (Ollama >= 0.1.26)
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("embeddings"):
            return data["embeddings"][0]
    except Exception:
        pass

    # Fallback: endpoint antigo
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Gera embeddings para uma lista de textos, um por um."""
    embeddings = []
    for i, text in enumerate(texts):
        print(f"   Embedding {i + 1}/{len(texts)}...", end="\r")
        embeddings.append(get_embedding(text))
    print()  # quebra de linha após o progresso
    return embeddings


# ─────────────────────────────────────────────
# 6. GRAVAÇÃO NO CHROMADB
# ─────────────────────────────────────────────
def get_chroma_collection():
    """Conecta ao ChromaDB e retorna (ou cria) a collection de jogos."""
    print(f"🗄️  Conectando ao ChromaDB em {CHROMA_HOST}:{CHROMA_PORT}...")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # Sem embedding_function — embeddings gerados manualmente via Ollama
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"✅ Collection '{COLLECTION_NAME}' pronta. Itens atuais: {collection.count()}")
    return collection


def upsert_games(collection, games: list[dict]):
    """Gera embeddings e insere os jogos no ChromaDB."""
    ids       = []
    documents = []
    metadatas = []

    for game in games:
        ids.append(str(game["id"]))
        documents.append(game_to_document(game))
        metadatas.append(game_to_metadata(game))

    print(f"   ⚙️  Gerando embeddings para {len(documents)} jogos...")
    embeddings = get_embeddings(documents)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


# ─────────────────────────────────────────────
# 7. FLUXO PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print("🚀 Iniciando ingestão de jogos para o banco vetorial RAG\n")

    token      = get_twitch_token()
    collection = get_chroma_collection()

    total_inseridos = 0
    offset = 0

    while total_inseridos < TOTAL_GAMES:
        print(f"\n📦 Buscando lote: offset={offset}, batch={BATCH_SIZE}...")
        try:
            games = fetch_games_batch(token, offset)
        except requests.HTTPError as e:
            print(f"❌ Erro na API da IGDB: {e}")
            break

        if not games:
            print("ℹ️  Sem mais jogos para buscar.")
            break

        upsert_games(collection, games)
        total_inseridos += len(games)
        offset          += BATCH_SIZE

        print(f"   ✅ {len(games)} jogos inseridos. Total acumulado: {total_inseridos}")
        time.sleep(0.3)

    print(f"\n🎮 Ingestão concluída! {total_inseridos} jogos no banco vetorial.")
    print(f"   Total na collection: {collection.count()} documentos.")


if __name__ == "__main__":
    main()