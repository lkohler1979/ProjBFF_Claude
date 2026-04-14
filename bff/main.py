import os
from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.security import APIKeyHeader
import httpx
from typing import Optional

app = FastAPI(
    title="API de Receitas (DummyJSON Proxy)",
    description="Busca e detalhamento de receitas usando a API DummyJSON como backend",
    version="1.0.0"
)

# ─── Configuração de Autenticação (API Key no Header) ──────────────────────────────
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

API_KEY = os.getenv("API_KEY") 

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Valida a chave de API informada no header X-API-Key.

    Levanta HTTPException 401 caso a chave esteja ausente ou seja inválida.
    """
    if api_key is None or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave API inválida ou ausente. Use o header X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


# ─── Cliente HTTP reutilizável  ────────────────────────────────────
async def dummyjson_get(endpoint: str, params: Optional[dict] = None) -> dict:
    """Realiza uma requisição GET autenticada à API DummyJSON.

    Args:
        endpoint: Caminho do recurso, ex: ``/recipes/search``.
        params: Parâmetros de query string opcionais.

    Returns:
        Corpo da resposta deserializado como dicionário.

    Raises:
        HTTPException 4xx/5xx: Repassa o status retornado pelo upstream.
        HTTPException 502: Falha de conexão ou timeout com o upstream.
        HTTPException 500: Qualquer outra exceção inesperada.
    """
    url = f"https://dummyjson.com{endpoint}"
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Erro na API DummyJSON: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erro de conexão com DummyJSON: {str(exc)}"
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno: {str(exc)}")


# ─── Endpoints ─────────────────────────────────────────────────────────────────────
@app.get(
    "/recipes/search",
    summary="Busca receitas por termo",
    dependencies=[Depends(get_api_key)]
)
async def search_recipes(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(10, ge=1, le=50, description="Resultados por página"),
    skip: int = Query(0, ge=0, description="Paginação: quantos pular")
):
    """Busca receitas pelo termo informado, com suporte a paginação.

    Repassa a busca ao endpoint ``/recipes/search`` do DummyJSON e retorna
    o JSON resultante sem transformações.
    """
    data = await dummyjson_get(
        "/recipes/search",
        params={"q": q, "limit": limit, "skip": skip}
    )
    return data


@app.get(
    "/recipes/{recipe_id}",
    summary="Obtém detalhes de uma receita pelo ID",
    dependencies=[Depends(get_api_key)]
)
async def get_recipe_by_id(
    recipe_id: int = Path(..., ge=1, description="ID da receita (1 a 50 na base DummyJSON)")
):
    """Retorna os detalhes completos de uma receita pelo seu ID.

    Repassa a requisição ao endpoint ``/recipes/{id}`` do DummyJSON e retorna
    o JSON resultante sem transformações. IDs válidos vão de 1 a 50.
    """
    data = await dummyjson_get(f"/recipes/{recipe_id}")
    return data