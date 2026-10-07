from datetime import date, timedelta


def check_player_range(min_players: int, max_players: int) -> None:
    if min_players > max_players:
        raise ValueError("Le nombre minimum de joueurs ne peut pas dépasser le nombre maximum.")


def check_elo_range(min_elo: int | None, max_elo: int | None) -> None:
    if min_elo is not None and max_elo is not None and min_elo > max_elo:
        raise ValueError("L'elo minimum ne peut pas dépasser l'elo maximum.")


def check_registration_end(registration_end: date, min_players: int) -> None:
    """La fin des inscriptions doit être strictement postérieure à aujourd'hui + nb min de joueurs (en jours)."""
    limit = date.today() + timedelta(days=min_players)
    if registration_end <= limit:
        raise ValueError(
            f"La date de fin des inscriptions doit être postérieure au {limit.strftime('%d/%m/%Y')} "
            "(date du jour + nombre minimum de joueurs)."
        )
