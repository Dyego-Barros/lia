from fastapi import APIRouter, Depends, HTTPException, status
from app.api.routes.dependencies import cliente_repository
from app.api.routes.auth import get_current_user
from app.api.schemas.clientes import ClienteCreate, ClienteUpdate
from app.application.dto.cliente import ClienteDto
from app.application.services.cliente_service import ClienteService
from app.application.use_cases.clientes.cadastrar_cliente import CadastrarCliente
from app.application.use_cases.clientes.atualizar_cliente import AtualizarCliente
from app.application.use_cases.clientes.buscar_cliente import BuscarCliente
from app.application.use_cases.clientes.listar_clientes import ListarClientes
from app.application.use_cases.clientes.excluir_cliente import ExcluirCliente
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository

router = APIRouter(prefix="/clientes", tags=["Clientes"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ClienteDto, status_code=status.HTTP_201_CREATED)
async def criar(payload: ClienteCreate, repository: ClienteRepository = Depends(cliente_repository)):
    return await CadastrarCliente(ClienteService(repository)).execute(ClienteDto(**payload.model_dump()))

@router.get("/", response_model=list[ClienteDto])
async def listar(repository: ClienteRepository = Depends(cliente_repository)):
    return await ListarClientes(ClienteService(repository)).execute()

@router.get("/{cliente_id}", response_model=ClienteDto)
async def buscar(cliente_id: int, repository: ClienteRepository = Depends(cliente_repository)):
    try: return await BuscarCliente(ClienteService(repository)).execute(cliente_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.put("/{cliente_id}", response_model=ClienteDto)
async def atualizar(cliente_id: int, payload: ClienteUpdate, repository: ClienteRepository = Depends(cliente_repository)):
    try:
        dto = ClienteDto(id=cliente_id, **payload.model_dump())
        return await AtualizarCliente(ClienteService(repository)).execute(dto)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(cliente_id: int, repository: ClienteRepository = Depends(cliente_repository)):
    try: await ExcluirCliente(ClienteService(repository)).execute(cliente_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
