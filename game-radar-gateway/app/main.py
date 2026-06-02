from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt

app = FastAPI(title="Game-Radar API Gateway")
security = HTTPBearer()

SECRET_KEY = "sua_chave_secreta_compartilhada"

# URLs internas da rede do Docker
AUTH_SERVICE_URL = "http://game-radar-auth:8001"
IA_SERVICE_URL = "http://game-radar-ia:8002"

def verificar_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

# ROTA DE LOGIN TEMPORÁRIA (MOCK)
@app.post("/api/v1/auth/login")
async def proxy_login(request: Request):
    # Simula que o banco validou e retorna um token falso para o Front
    return {
        "access_token": "token_falso_do_heitor_123",
        "token_type": "bearer"
    }

# ROTA DE RECOMENDAÇÃO TEMPORÁRIA (MOCK)
@app.post("/api/v1/recomendacao")
async def proxy_recomendacao(request: Request):
    # Simula a resposta da IA
    return {
        "recomendacoes": [
            {"titulo": "The Witcher 3", "preco_cheapshark": "R$ 29,90", "plataforma": "Steam"},
            {"titulo": "Hades", "preco_cheapshark": "Disponível no Game Pass", "plataforma": "Xbox/PC"}
        ]
    }