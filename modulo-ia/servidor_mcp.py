import os
import asyncio  
import httpx
from mcp.server.fastmcp import FastMCP

# 1. Instância do Servidor MCP
mcp = FastMCP("mcp-gateway-controller")

# URL do seu API Gateway (ajuste conforme necessário)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gateway:8080")
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))

# 2. Definição das Ferramentas (Tools)

@mcp.tool()
async def check_services_health() -> str:
    """
    Verifica o status de todos os serviços e workers registrados no API Gateway.
    """
    try:
        # Exemplo de chamada real usando httpx:
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"{GATEWAY_URL}/health")
        #     return response.text
        
        # Mock para testes
        mock_health_status = {
            "gateway": "UP",
            "auth_service": "UP",
            "optimization_worker": "UP",
            "payment_service": "DOWN"
        }
        return str(mock_health_status)
    
    except Exception as e:
        return f"Erro ao contatar Gateway: {str(e)}"

@mcp.tool()
async def get_kafka_status(topic: str = "default_topic") -> str:
    """
    Obtém o status do broker de eventos (Kafka), verificando lag e partições ativas de um tópico.
    
    Args:
        topic: Nome do tópico do Kafka para inspecionar.
    """
    # Aqui entraria a lógica para conectar ao cluster Kafka ou consultar uma API de métricas
    return f"Status do Kafka para o tópico '{topic}': 3 partições ativas, Lag tolerável (dentro da margem de 500ms)."

@mcp.tool()
async def query_postgres_metrics(service_name: str) -> str:
    """
    Consulta métricas de carga e conexões ativas no banco de dados PostgreSQL associado a um microsserviço.
    
    Args:
        service_name: Nome do microsserviço associado ao banco (ex: 'auth', 'optimization').
    """
    # Aqui entraria a lógica de consulta (usando psycopg2, asyncpg ou SQLAlchemy)
    return f"Métricas do PostgreSQL para '{service_name}': 12 conexões ativas, tempo médio de query 45ms."


if __name__ == "__main__":
    mcp.run(transport="sse", host=HOST, port=PORT)