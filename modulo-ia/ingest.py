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
from chromadb.utils import embedding_functions

load_dotenv()

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÕES
# ─────────────────────────────────────────────
TWITCH_CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
IGDB_API_URL         = "https://api.igdb.com/v4"

# ChromaDB rodando em container separado (ver docker-compose.yml)
CHROMA_HOST          = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT          = int(os.getenv("CHROMA_PORT", 8005))
COLLECTION_NAME      = "games"

# Modelo de embedding local via Ollama (mesmo container já existente no projeto)
OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL      = "nomic-embed-text"  # leve e eficiente para português/inglês

# Quantos jogos buscar por requisição (máx 500 na IGDB)
BATCH_SIZE  = 100
# Total de jogos a indexar (ajuste conforme necessidade)
TOTAL_GAMES = 500


# ─────────────────────────────────────────────
# 2. AUTENTICAÇÃO NA TWITCH / IGDB
# ─────────────────────────────────────────────
def get_twitch_token() -> str:
    """Obtém o token OAuth2 da Twitch para usar a IGDB."""
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
    """
    Busca um lote de jogos na IGDB.
    Filtra jogos com rating relevante e campos essenciais preenchidos.
    """
    headers = {
        "Client-ID":     TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    # Linguagem de query proprietária da IGDB (Apicalypse)
    # Buscamos campos ricos para gerar embeddings com contexto semântico real
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

    resp = requests.post(
        f"{IGDB_API_URL}/games",
        headers=headers,
        data=query,
    )
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────────────────────
# 4. TRANSFORMAÇÃO: JOGO → DOCUMENTO DE TEXTO
# ─────────────────────────────────────────────
def game_to_document(game: dict) -> str:
    """
    Transforma um objeto de jogo da IGDB em um texto descritivo rico.

    A qualidade do embedding depende diretamente da qualidade deste texto.
    Quanto mais contexto semântico, melhor a busca por similaridade.
    """
    name     = game.get("name", "Desconhecido")
    summary  = game.get("summary", "")
    storyline = game.get("storyline", "")

    # Extrai listas de campos aninhados
    genres   = ", ".join(g["name"] for g in game.get("genres", []))
    themes   = ", ".join(t["name"] for t in game.get("themes", []))
    modes    = ", ".join(m["name"] for m in game.get("game_modes", []))
    keywords = ", ".join(k["name"] for k in game.get("keywords", [])[:15])  # limita keywords
    platforms = ", ".join(p["name"] for p in game.get("platforms", []))
    perspectives = ", ".join(p["name"] for p in game.get("player_perspectives", []))

    # Desenvolvedores
    devs = [
        c["company"]["name"]
        for c in game.get("involved_companies", [])
        if c.get("developer") and "company" in c
    ]
    developer = ", ".join(devs) if devs else "Desconhecido"

    # Rating
    rating = game.get("rating", 0)
    rating_str = f"{rating:.1f}/100" if rating else "Sem avaliação"

    # Ano de lançamento
    release_ts = game.get("first_release_date")
    release_year = ""
    if release_ts:
        release_year = str(time.gmtime(release_ts).tm_year)

    # Monta o documento — formato de prosa para embeddings semânticos
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
    """
    Metadados estruturados gravados junto ao embedding.
    Permitem filtros adicionais no momento da busca (ex: filtrar por plataforma).
    """
    rating = game.get("rating", 0)
    release_ts = game.get("first_release_date")
    release_year = time.gmtime(release_ts).tm_year if release_ts else 0

    return {
        "name":         game.get("name", ""),
        "rating":       round(rating, 1),
        "release_year": release_year,
        "genres":       ", ".join(g["name"] for g in game.get("genres", [])),
        "platforms":    ", ".join(p["name"] for p in game.get("platforms", [])),
        "themes":       ", ".join(t["name"] for t in game.get("themes", [])),
    }


def get_chroma_collection():
    print(f"🗄️  Conectando ao ChromaDB em {CHROMA_HOST}:{CHROMA_PORT}...")

    # Vamos garantir que o endpoint do ollama esteja correto
    # Se o host for 'localhost' dentro do container, ele pode não achar o ollama
    print(f"🧠 Usando Ollama em: {OLLAMA_BASE_URL}")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # Função de embedding ajustada
    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        url=f"{OLLAMA_BASE_URL}/api/embeddings",
        model_name=EMBEDDING_MODEL,
    )

    # Testa se o Ollama responde antes de criar a coleção
    try:
        test_embed = embed_fn(["teste"])
        print(f"✅ Conexão com Ollama OK. Dimensão do embedding: {len(test_embed[0])}")
    except Exception as e:
        print(f"❌ Erro ao conectar no Ollama: {e}")
        print("💡 DICA: Verifique se o container 'ollama' está rodando e se você baixou o modelo com: docker exec -it ollama ollama pull nomic-embed-text")
        exit(1)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def upsert_games(collection, games: list[dict]):
    """Insere ou atualiza jogos no ChromaDB (upsert evita duplicatas)."""
    sucesso = 0
    falhas  = 0

    for game in games:
        game_id = str(game["id"])
        doc     = game_to_document(game)
        meta    = game_to_metadata(game)

        # Ignora documentos vazios — causam IndexError no ChromaDB/Ollama
        if not doc or not doc.strip():
            print(f"  ⚠️  Jogo {game_id} ({game.get('name')}) gerou documento vazio, pulando.")
            falhas += 1
            continue

        try:
            collection.upsert(
                ids=[game_id],
                documents=[doc],
                metadatas=[meta],
            )
            sucesso += 1
        except Exception as e:
            print(f"  ❌ Erro ao inserir jogo {game_id} ({game.get('name')}): {e}")
            falhas += 1

    if falhas:
        print(f"  ⚠️  {falhas} jogos pulados/com erro neste lote.")


# ─────────────────────────────────────────────
# 6. FLUXO PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print(" Iniciando ingestão de jogos para o banco vetorial RAG\n")

    token      = get_twitch_token()
    collection = get_chroma_collection()

    total_inseridos = 0
    offset = 0

    while total_inseridos < TOTAL_GAMES:
        print(f"Buscando lote: offset={offset}, batch={BATCH_SIZE}...")
        try:
            games = fetch_games_batch(token, offset)
        except requests.HTTPError as e:
            print(f"Erro na API da IGDB: {e}")
            break

        if not games:
            print(" Sem mais jogos para buscar.")
            break

        upsert_games(collection, games)
        total_inseridos += len(games)
        offset          += BATCH_SIZE

        print(f"   {len(games)} jogos inseridos. Total: {total_inseridos}")

        # Respeita o rate limit da IGDB (4 req/s no plano gratuito)
        time.sleep(0.3)

    print(f"\n🎮 Ingestão concluída! {total_inseridos} jogos no banco vetorial.")
    print(f"   Total na collection: {collection.count()} documentos.")


if __name__ == "__main__":
    main()
