from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from auth_routes import auth_router
from familia_routes import familia_router
from gold import GrupoInexistente
from origem_routes import origem_router
from radar_routes import radar_router
from regional_routes import regional_router

app = FastAPI(title="Radar ENEM")

@app.get('/')
async def read_root():
    return {"Facilita ENEM"}

MENSAGENS = {
    "missing": "é obrigatório",
    "float_parsing": "precisa ser um número",
    "int_parsing": "precisa ser um número inteiro",
    "less_than_equal": "deve ser no máximo {le:g}",
    "greater_than_equal": "deve ser no mínimo {ge:g}",
    "enum": "não é válido; use um destes: {expected}",
}

@app.exception_handler(RequestValidationError)
async def entrada_invalida(request: Request, erro: RequestValidationError):
    """Mesmo formato de erro das outras rotas, em português e por campo."""
    campos = {}
    for problema in erro.errors():
        campo = problema["loc"][-1]
        modelo = MENSAGENS.get(problema["type"], "não é válido")
        campos[campo] = modelo.format(**problema.get("ctx", {}))
    detalhe = "; ".join(f"{campo}: {mensagem}" for campo, mensagem in campos.items())
    return JSONResponse(status_code=422, content={"detail": detalhe, "campos": campos})

@app.exception_handler(GrupoInexistente)
async def grupo_inexistente(request: Request, erro: GrupoInexistente):
    return JSONResponse(status_code=404, content={"detail": str(erro)})

app.include_router(auth_router)
app.include_router(radar_router)
app.include_router(regional_router)
app.include_router(origem_router)
app.include_router(familia_router)
