from dataclasses import dataclass
from typing import Iterable

from app.models.match import Match, MatchResult
from app.models.user import User

WIN_POINTS = 1.0
DRAW_POINTS = 0.5


@dataclass
class Standing:
    player_id: int
    username: str
    played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    rank: int = 0

    @property
    def score(self) -> float:
        return self.wins * WIN_POINTS + self.draws * DRAW_POINTS


def compute_scoreboard(players: Iterable[User], matches: Iterable[Match]) -> list[Standing]:
    """Classement des joueurs d'après les rencontres déjà jouées (les autres sont ignorées).

    Tri : score décroissant, puis nombre de victoires décroissant, puis nom. Les joueurs à égalité
    de score partagent le même rang (1, 2, 2, 4...). Tous les joueurs sont listés, même sans rencontre jouée.
    """
    standings = {player.id: Standing(player_id=player.id, username=player.username) for player in players}

    for match in matches:
        if match.result == MatchResult.NOT_PLAYED:
            continue
        white, black = standings.get(match.whiteId), standings.get(match.blackId)
        if white is None or black is None:
            continue
        white.played += 1
        black.played += 1
        if match.result == MatchResult.WHITE:
            white.wins += 1
            black.losses += 1
        elif match.result == MatchResult.BLACK:
            black.wins += 1
            white.losses += 1
        else:
            white.draws += 1
            black.draws += 1

    ordered = sorted(standings.values(), key=lambda s: (-s.score, -s.wins, s.username.lower()))
    for standing in ordered:
        standing.rank = 1 + sum(1 for other in ordered if other.score > standing.score)
    return ordered
