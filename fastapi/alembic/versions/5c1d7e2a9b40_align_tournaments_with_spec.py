"""align tournaments with spec

Revision ID: 5c1d7e2a9b40
Revises: 08bcf3322045
Create Date: 2026-10-07 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c1d7e2a9b40'
down_revision: Union[str, Sequence[str], None] = '08bcf3322045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # anciennes contraintes
    op.drop_constraint('elo_range', 'tournaments', type_='check')
    op.drop_constraint('dates_order', 'tournaments', type_='check')
    op.drop_constraint('rounds_min', 'tournaments', type_='check')

    # statut "inscriptions" -> "en attente de joueurs"
    op.execute("ALTER TYPE tournamentstatus RENAME VALUE 'INSCRIPTIONS' TO 'EN_ATTENTE_DE_JOUEURS'")

    op.alter_column('tournaments', 'girlsOnly', new_column_name='womenOnly')

    # elo optionnels
    op.alter_column('tournaments', 'minElo', nullable=True, server_default=None)
    op.alter_column('tournaments', 'maxElo', nullable=True, server_default=None)

    # nouvelles colonnes (valeurs par défaut temporaires pour les lignes existantes)
    op.add_column('tournaments', sa.Column('minPlayers', sa.Integer(), server_default='2', nullable=False))
    op.add_column('tournaments', sa.Column('maxPlayers', sa.Integer(), server_default='32', nullable=False))
    op.add_column('tournaments', sa.Column(
        'categories', sa.ARRAY(sa.String()),
        server_default=sa.text("ARRAY['junior','senior','veteran']::varchar[]"), nullable=False,
    ))
    op.add_column('tournaments', sa.Column('currentRound', sa.Integer(), server_default='0', nullable=False))
    op.add_column('tournaments', sa.Column('registrationEndDate', sa.Date(), nullable=True))
    op.add_column('tournaments', sa.Column(
        'createdAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('tournaments', sa.Column(
        'updatedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # la fin des inscriptions reprend l'ancienne date de début
    op.execute('UPDATE tournaments SET "registrationEndDate" = "startDate"')
    op.alter_column('tournaments', 'registrationEndDate', nullable=False)

    op.alter_column('tournaments', 'minPlayers', server_default=None)
    op.alter_column('tournaments', 'maxPlayers', server_default=None)
    op.alter_column('tournaments', 'categories', server_default=None)

    # colonnes supprimées
    op.drop_column('tournaments', 'startDate')
    op.drop_column('tournaments', 'endDate')
    op.drop_column('tournaments', 'rounds')

    # nouvelles contraintes
    op.create_check_constraint('min_players_range', 'tournaments', '"minPlayers" BETWEEN 2 AND 32')
    op.create_check_constraint('max_players_range', 'tournaments', '"maxPlayers" BETWEEN 2 AND 32')
    op.create_check_constraint('players_order', 'tournaments', '"minPlayers" <= "maxPlayers"')
    op.create_check_constraint('min_elo_range', 'tournaments', '"minElo" BETWEEN 0 AND 3000')
    op.create_check_constraint('max_elo_range', 'tournaments', '"maxElo" BETWEEN 0 AND 3000')
    op.create_check_constraint('elo_order', 'tournaments', '"minElo" <= "maxElo"')
    op.create_check_constraint(
        'categories_valid', 'tournaments',
        "cardinality(categories) >= 1 AND categories <@ CAST(ARRAY['junior','senior','veteran'] AS varchar[])",
    )
    op.create_check_constraint('current_round_min', 'tournaments', '"currentRound" >= 0')


def downgrade() -> None:
    """Downgrade schema."""
    for name in ('current_round_min', 'categories_valid', 'elo_order', 'max_elo_range',
                 'min_elo_range', 'players_order', 'max_players_range', 'min_players_range'):
        op.drop_constraint(name, 'tournaments', type_='check')

    op.add_column('tournaments', sa.Column('rounds', sa.Integer(), server_default='5', nullable=False))
    op.add_column('tournaments', sa.Column('endDate', sa.Date(), nullable=True))
    op.add_column('tournaments', sa.Column('startDate', sa.Date(), nullable=True))
    op.execute('UPDATE tournaments SET "startDate" = "registrationEndDate", "endDate" = "registrationEndDate"')
    op.alter_column('tournaments', 'startDate', nullable=False)
    op.alter_column('tournaments', 'endDate', nullable=False)
    op.alter_column('tournaments', 'rounds', server_default=None)

    op.drop_column('tournaments', 'updatedAt')
    op.drop_column('tournaments', 'createdAt')
    op.drop_column('tournaments', 'registrationEndDate')
    op.drop_column('tournaments', 'currentRound')
    op.drop_column('tournaments', 'categories')
    op.drop_column('tournaments', 'maxPlayers')
    op.drop_column('tournaments', 'minPlayers')

    op.execute('UPDATE tournaments SET "minElo" = COALESCE("minElo", 0), "maxElo" = COALESCE("maxElo", 3000)')
    op.alter_column('tournaments', 'minElo', nullable=False, server_default='0')
    op.alter_column('tournaments', 'maxElo', nullable=False, server_default='3000')

    op.alter_column('tournaments', 'womenOnly', new_column_name='girlsOnly')
    op.execute("ALTER TYPE tournamentstatus RENAME VALUE 'EN_ATTENTE_DE_JOUEURS' TO 'INSCRIPTIONS'")

    op.create_check_constraint('rounds_min', 'tournaments', 'rounds >= 1')
    op.create_check_constraint('dates_order', 'tournaments', '"endDate" >= "startDate"')
    op.create_check_constraint(
        'elo_range', 'tournaments',
        '"minElo" >= 0 AND "maxElo" <= 3000 AND "minElo" <= "maxElo"',
    )
