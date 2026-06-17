from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import router  # Importa o arquivo de rotas distribuídas

app = FastAPI(title="Game-Radar API Gateway", version="1.0.0")

# Configuração de CORS corrigida - Aberta para suportar requisições do Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas do gateway
app.include_router(router)