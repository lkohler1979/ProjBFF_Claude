# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com este repositório.

## Visão Geral do Projeto

Serviço educativo de Backend for Frontend (BFF) em Python/FastAPI que faz proxy da API pública [DummyJSON Recipes](https://dummyjson.com/docs/recipes) com autenticação por chave de API. Todos os comentários, mensagens de erro e documentação estão em português brasileiro.

## Configuração

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Crie o arquivo `.env` na raiz do projeto:
```env
API_KEY=SuaChaveSecretaAqui
```

## Execução

```bash
dotenv run fastapi dev bff/main.py
```

O servidor inicia em `http://127.0.0.1:8000`. Documentação interativa disponível em `/docs` e `/redoc`.

**Importante:** A aplicação lê `API_KEY` do ambiente na inicialização via `os.getenv("API_KEY")` — não há `load_dotenv()` no código. Omitir o `dotenv run` fará com que todas as requisições retornem 401.

## Arquitetura

Toda a lógica da aplicação está em um único arquivo: `bff/main.py`. Não há módulos separados de routers, models ou services.

- **Autenticação** — dependência `APIKeyHeader` (header `X-API-Key`). Aplicada globalmente via `dependencies=[Depends(get_api_key)]` em cada endpoint.
- **Helper HTTP** — `dummyjson_get(endpoint, params)` é uma função assíncrona que encapsula o `httpx.AsyncClient` com timeout de 10s. Mapeia erros 4xx/5xx do upstream para o mesmo status, erros de rede para 502, e outras exceções para 500.
- **Endpoints** — duas rotas, ambas repassando o JSON do upstream sem transformações:
  - `GET /recipes/search?q=&limit=&skip=` — faz proxy de `/recipes/search`
  - `GET /recipes/{recipe_id}` — faz proxy de `/recipes/{id}`, IDs de 1 a 50

## Testes

Nenhuma suíte de testes existe ainda. Ao adicionar testes, o padrão FastAPI se aplica:

```bash
pip install pytest pytest-asyncio httpx

# Rodar todos os testes
pytest

# Rodar um único teste
pytest tests/test_main.py::test_search_recipes
```

Use `httpx.AsyncClient` com `transport=ASGITransport(app=app)` para testes assíncronos de endpoints, ou `fastapi.testclient.TestClient` para testes síncronos. Defina a variável de ambiente `API_KEY` antes de importar a aplicação nos testes.

## Linting

Nenhum linter está configurado, mas o `.gitignore` inclui `.ruff_cache/`, indicando que o ruff é o linter pretendido. Para adicioná-lo:

```bash
pip install ruff
ruff check bff/
```
