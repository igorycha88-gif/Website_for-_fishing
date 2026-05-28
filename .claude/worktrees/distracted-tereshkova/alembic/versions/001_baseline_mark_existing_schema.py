"""baseline: mark existing schema

Revision ID: 001_baseline
Revises:
Create Date: 2026-02-10

Эта миграция фиксирует текущее состояние БД как отправную точку.
Схема уже создана через database/schema.sql и migration_add_places_fields.sql.
Все последующие миграции будут инкрементальными diff'ами.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Схема уже существует в БД — ничего не делаем.
    # Эта миграция просто записывает версию в alembic_version.
    pass


def downgrade() -> None:
    # Откат baseline невозможен — схема управляется через schema.sql
    pass
