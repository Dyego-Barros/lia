from .agendamentos import router as agendamentos_router
from .clientes import router as clientes_router
from .procedimentos import router as procedimentos_router
from .atendimento import router as atendimento_router
from .agente import router as agente_router
from .whatsapp import router as whatsapp_router
from .ultramsg import router as ultramsg_router
from .auth import router as auth_router
from .relatorios import router as relatorios_router
from .operacoes import router as operacoes_router
from .configuracoes import router as configuracoes_router
from .integracoes import router as integracoes_router, webhook_router as integracoes_webhook_router
