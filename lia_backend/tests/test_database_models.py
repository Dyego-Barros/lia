import unittest

from app.infrastructure.database.models.models import (
    ConsumoMaterialModel,
    ProcedimentoMaterialModel,
)


class DatabaseModelTest(unittest.TestCase):
    def test_inventory_primary_keys_support_batched_inserts(self):
        """Regression: SQLAlchemy insertmanyvalues requires a non-null sentinel."""
        for model in (ProcedimentoMaterialModel, ConsumoMaterialModel):
            primary_key = model.__table__.c.id
            self.assertFalse(primary_key.nullable)
            self.assertTrue(primary_key.autoincrement)
            # Accessing this property reproduces the production validation that
            # raised InvalidRequestError before an INSERT was emitted.
            characteristics = model.__table__._sentinel_column_characteristics
            self.assertEqual(characteristics.columns, (primary_key,))


if __name__ == "__main__":
    unittest.main()
