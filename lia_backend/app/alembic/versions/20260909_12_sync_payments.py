"""backfill and synchronize appointment payments"""
from alembic import op

revision = "20260909_12"
down_revision = "20260909_11"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("DELETE FROM pagamentos a USING pagamentos b WHERE a.agendamento_id = b.agendamento_id AND a.id < b.id")
    op.create_unique_constraint("uq_pagamento_agendamento", "pagamentos", ["agendamento_id"])
    op.execute("""INSERT INTO pagamentos (agendamento_id, valor, forma, status, pago_em)
        SELECT a.id, a.valor_cobrado, a.forma_pagamento, 'pago', COALESCE(a.data_atualizacao, CURRENT_TIMESTAMP)
        FROM agendamentos a
        WHERE a.status_pagamento = 'pago' AND a.valor_cobrado IS NOT NULL AND a.forma_pagamento IS NOT NULL
        ON CONFLICT (agendamento_id) DO UPDATE SET valor = EXCLUDED.valor, forma = EXCLUDED.forma, status = 'pago'""")

def downgrade() -> None:
    op.drop_constraint("uq_pagamento_agendamento", "pagamentos", type_="unique")
