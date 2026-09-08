from enum import Enum

class StatusAgendamento(Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    CONCLUIDO = "concluido"
    NAO_COMPARECEU = "nao_compareceu"