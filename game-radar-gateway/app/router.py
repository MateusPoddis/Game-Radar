import os
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

# VARIÁVEIS DE AMBIENTE
# Apontando para o container onde roda o seu Agente LangChain (main.py)
IA_SERVICE_URL = os.getenv("IA_SERVICE_URL", "http://127.0.0.1:8002")

# ==========================================
# ROTA PRINCIPAL (React -> Gateway -> IA)
# ==========================================
@router.post("/api/v1/recomendacao")
async def obter_recomendacao(dados_do_front: dict):
    """
    Endpoint que recebe os filtros do React, valida e 
    repassa os dados para o microsserviço de IA (Gemma 2).
    """
    try:
        # Usamos httpx assíncrono para não bloquear o servidor enquanto a IA raciocina
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Chama a rota '/api/chat' que definimos no main.py
            response = await client.post(f"{IA_SERVICE_URL}/api/chat", json=dados_do_front)
            
            # Se o serviço de IA retornar erro (ex: 500), lança uma exceção
            response.raise_for_status() 
            
            # Retorna a resposta gerada pelo Gemma 2 e LangChain direto para o React
            return response.json()
            
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Serviço de IA está offline ou inatingível na rede.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="A IA demorou muito para responder (Timeout).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Erro interno no serviço de IA.")