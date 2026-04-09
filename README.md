
# BFF para API de Receitas - FastAPI

Este é um Backend for Frontend (BFF) simples, de caráter educativo, que serve como camada de abstração para acessar a API pública de receitas [DummyJSON Recipes](https://dummyjson.com/docs/recipes). O objetivo deste projeto é fornecer um servidor em Python usando **FastAPI** que acessa a API de receitas externa e expõe esses dados de forma organizada para o frontend, com a implementação de autenticação via **chave de API**.

## Requisitos

- Python 3.12+ 
- FastAPI
- Uvicorn (para execução do servidor)
- httpx (para requisições HTTP assíncronas)
- python-dotenv (para carregar variáveis de ambiente de um arquivo `.env`)

## Instalação

1. **Crie um ambiente virtual:**

   Se estiver utilizando `venv`, execute:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Para Linux/Mac
   venv\Scripts\activate     # Para Windows
   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure a chave de API:**

   - **Usando uma variável de ambiente:** Crie um arquivo `.env` na raiz do projeto com a chave de API, como mostrado abaixo:

     ```env
     API_KEY=SuaChaveSecretaAqui
     ```


## Como Executar

1. **Inicie o servidor FastAPI:**

   Para rodar a aplicação com o **Uvicorn**, execute o comando abaixo:

   ```bash
   dotenv run fastapi dev bff/main.py
   ```

   O servidor estará disponível em `http://127.0.0.1:8000`.

