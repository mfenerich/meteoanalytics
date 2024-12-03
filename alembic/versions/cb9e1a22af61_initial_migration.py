"""Initial migration

Revision ID: cb9e1a22af61
Revises: 

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb9e1a22af61'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
    'weather_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('identificacion', sa.String(), nullable=False),
    sa.Column('fhora', sa.TIMESTAMP(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('identificacion', 'fhora', name='uq_identificacion_fhora')
    )
    op.create_index('idx_identificacion_fhora', 'weather_data', ['identificacion', 'fhora'], unique=False)
    op.create_index(op.f('ix_weather_data_fhora'), 'weather_data', ['fhora'], unique=False)
    op.create_index(op.f('ix_weather_data_id'), 'weather_data', ['id'], unique=False)
    op.create_index(op.f('ix_weather_data_identificacion'), 'weather_data', ['identificacion'], unique=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_weather_data_identificacion'), table_name='weather_data')
    op.drop_index(op.f('ix_weather_data_id'), table_name='weather_data')
    op.drop_index(op.f('ix_weather_data_fhora'), table_name='weather_data')
    op.drop_index('idx_identificacion_fhora', table_name='weather_data')
    op.drop_table('weather_data')
    # ### end Alembic commands ###