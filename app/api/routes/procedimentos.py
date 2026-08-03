from fastapi import APIRouter, Depends, HTTPException, status
from app.api.routes.dependencies import procedimento_repository
from app.api.schemas.procedimentos import ProcedimentoCreate
from app.application.dto.procedimento import ProcedimentoDto
from app.application.services.procedimento_service import ProcedimentoService
from app.application.use_cases.procedimentos.cadastrar_procedimento import CadastrarProcedimento
from app.application.use_cases.procedimentos.buscar_procedimento import BuscarProcedimento
from app.application.use_cases.procedimentos.listar_procedimentos import ListarProcedimentos
from app.application.use_cases.procedimentos.atualizar_procedimento import AtualizarProcedimento
from app.application.use_cases.procedimentos.excluir_procedimento import ExcluirProcedimento
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository

router = APIRouter(prefix="/procedimentos", tags=["Procedimentos"])

@router.post("/", response_model=ProcedimentoDto, status_code=status.HTTP_201_CREATED)
async def criar(payload: ProcedimentoCreate, repository: ProcedimentoRepository = Depends(procedimento_repository)):
    return await CadastrarProcedimento(ProcedimentoService(repository)).execute(ProcedimentoDto(**payload.model_dump()))

@router.get("/", response_model=list[ProcedimentoDto])
async def listar(repository: ProcedimentoRepository = Depends(procedimento_repository)):
    return await ListarProcedimentos(ProcedimentoService(repository)).execute()

@router.get("/{procedimento_id}", response_model=ProcedimentoDto)
async def buscar(procedimento_id: int, repository: ProcedimentoRepository = Depends(procedimento_repository)):
    try: return await BuscarProcedimento(ProcedimentoService(repository)).execute(procedimento_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.put("/{procedimento_id}", response_model=ProcedimentoDto)
async def atualizar(procedimento_id: int, payload: ProcedimentoCreate, repository: ProcedimentoRepository = Depends(procedimento_repository)):
    try: return await AtualizarProcedimento(ProcedimentoService(repository)).execute(ProcedimentoDto(id=procedimento_id, **payload.model_dump()))
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc

@router.delete("/{procedimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(procedimento_id: int, repository: ProcedimentoRepository = Depends(procedimento_repository)):
    try: await ExcluirProcedimento(ProcedimentoService(repository)).execute(procedimento_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
