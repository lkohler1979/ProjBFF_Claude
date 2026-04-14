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

    Utilizada como dependência FastAPI nos endpoints protegidos. A chave
    esperada é lida da variável de ambiente ``API_KEY`` na inicialização.

    Args:
        api_key: Valor extraído automaticamente do header ``X-API-Key``
            pelo ``APIKeyHeader``. Será ``None`` se o header estiver ausente.

    Returns:
        str: A própria chave de API, caso seja válida.

    Raises:
        HTTPException 401: Se o header estiver ausente ou o valor não
            corresponder à chave configurada em ``API_KEY``.
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
    """Realiza uma requisição GET à API DummyJSON e retorna o corpo como dicionário.

    Função auxiliar compartilhada por todos os endpoints. Cria um
    ``httpx.AsyncClient`` com timeout de 10 s por requisição.

    Args:
        endpoint: Caminho do recurso relativo à base ``https://dummyjson.com``,
            ex: ``/recipes/search`` ou ``/recipes/42``.
        params: Dicionário de parâmetros de query string a serem anexados à
            URL. Use ``None`` (padrão) quando não houver parâmetros.

    Returns:
        dict: Corpo da resposta HTTP deserializado como dicionário Python,
            conforme retornado pelo DummyJSON sem nenhuma transformação.

    Raises:
        HTTPException: Com o mesmo status HTTP retornado pelo DummyJSON em
            caso de erro 4xx ou 5xx no upstream.
        HTTPException 502: Quando ocorre falha de rede, timeout ou qualquer
            ``httpx.RequestError`` ao tentar alcançar o DummyJSON.
        HTTPException 500: Para qualquer outra exceção inesperada.
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

    Repassa os parâmetros diretamente ao endpoint ``/recipes/search`` do
    DummyJSON e devolve o JSON resultante sem transformações.

    Args:
        q: Termo de busca (mínimo 2 caracteres). Pesquisado pelo DummyJSON
            nos campos nome e ingredientes das receitas.
        limit: Quantidade máxima de resultados a retornar por página.
            Aceita valores de 1 a 50; padrão é 10.
        skip: Número de registros a pular, usado para paginação. Por exemplo,
            ``skip=10`` com ``limit=10`` retorna a segunda página.

    Returns:
        dict: Objeto JSON do DummyJSON contendo as chaves ``recipes``
            (lista de receitas encontradas), ``total``, ``skip`` e ``limit``.
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

    Repassa a requisição ao endpoint ``/recipes/{id}`` do DummyJSON e devolve
    o JSON resultante sem transformações.

    Args:
        recipe_id: Identificador inteiro da receita (mínimo 1). A base
            DummyJSON contém receitas com IDs de 1 a 50; IDs fora desse
            intervalo resultarão em 404 retornado pelo upstream.

    Returns:
        dict: Objeto JSON completo da receita, incluindo campos como
            ``id``, ``name``, ``ingredients``, ``instructions``,
            ``prepTimeMinutes``, ``cookTimeMinutes``, ``servings``,
            ``difficulty``, ``cuisine``, ``caloriesPerServing``, ``tags``,
            ``rating`` e ``image``.
    """
    data = await dummyjson_get(f"/recipes/{recipe_id}")
    return data