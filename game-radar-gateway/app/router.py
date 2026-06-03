import os
from fastapi import APIRouter, HTTPException

router = APIRouter()

# VARIÁVEIS DE AMBIENTE: Preparado para a arquitetura distribuída no Docker
# Se rodar fora do Docker, assume o localhost (127.0.0.1) automaticamente.
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
IA_SERVICE_URL = os.getenv("IA_SERVICE_URL", "http://127.0.0.1:8002")

@router.post("/api/v1/recomendacao")
def obter_recomendacao(dados_do_front: dict):
    """
    Endpoint que recebe os filtros do React, valida e futuramente
    repassará os dados para o microsserviço de IA.
    """
    
    # --- FLUXO FUTURO COM O MICROSSERVIÇO DE IA ATIVO ---
    # try:
    #     import requests
    #     response = requests.post(f"{IA_SERVICE_URL}/recomendar", json=dados_do_front)
    #     return response.json()
    # except Exception:
    #     raise HTTPException(status_code=503, detail="Serviço de IA temporariamente indisponível")

    # --- FLUXO ATUAL: Mock estruturado validando a ponte com o Frontend ---
    return {
        "status": "sucesso",
        "mensagem": "Dados processados pelo Gateway com sucesso!",
        "recomendacoes": [
            {
                "id": 1,
                "titulo": "The Witcher 3: Wild Hunt",
                "preco_cheapshark": "R$ 29,99",
                "plataforma": "PC / PlayStation / XBOX"
            },
            {
                "id": 2,
                "titulo": "Hades",
                "preco_cheapshark": "R$ 45,00",
                "plataforma": "PC / Nintendo Switch"
            }
        ]
    }