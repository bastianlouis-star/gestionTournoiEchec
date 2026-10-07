from typing import NamedTuple


class Pairing(NamedTuple):
    round: int
    white: int
    black: int


def double_round_robin(player_ids: list[int]) -> list[Pairing]:
    """Calendrier « toutes rondes » aller-retour (méthode des tables de Berger / du cercle).

    Chaque joueur affronte tous les autres deux fois, une fois avec les blancs et une fois avec les noirs.
    Au retour, les mêmes rondes sont rejouées couleurs inversées. Avec un nombre impair de joueurs,
    un joueur est exempt à chaque ronde.
    Nombre de rondes : 2 × (n - 1) pour n pair, 2 × n pour n impair.
    """
    if len(player_ids) < 2:
        return []
    if len(set(player_ids)) != len(player_ids):
        raise ValueError("Un joueur ne peut apparaître qu'une fois.")

    slots: list[int | None] = list(player_ids)
    if len(slots) % 2:
        slots.append(None)  # exempt
    size = len(slots)
    rounds_per_leg = size - 1

    first_leg: list[tuple[int, int, int]] = []  # (ronde, blanc, noir)
    rotating = slots[1:]
    for round_index in range(rounds_per_leg):
        arrangement = [slots[0]] + rotating
        for i in range(size // 2):
            a, b = arrangement[i], arrangement[size - 1 - i]
            if a is None or b is None:
                continue
            # couleurs : le joueur fixe alterne à chaque ronde, les autres selon la parité de leur table.
            # Un joueur qui tourne change de table (donc de parité) à chaque ronde : il alterne aussi.
            # Écart blancs/noirs par leg : <= 1 pour n pair, <= 2 pour n impair.
            a_is_white = round_index % 2 == 0 if i == 0 else i % 2 == 0
            white, black = (a, b) if a_is_white else (b, a)
            first_leg.append((round_index + 1, white, black))
        rotating = rotating[-1:] + rotating[:-1]

    second_leg = [(round_ + rounds_per_leg, black, white) for round_, white, black in first_leg]
    return [Pairing(*pairing) for pairing in first_leg + second_leg]
