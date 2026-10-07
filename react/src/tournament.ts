import type { Category } from "./categories"

export type Status = 'en_attente_de_joueurs' | 'en_cours' | 'termine'

export interface Tournament {
    id: number
    name: string
    location: string | null
    minPlayers: number
    maxPlayers: number
    minElo: number | null
    maxElo: number | null
    categories: Category[]
    status: Status
    currentRound: number
    womenOnly: boolean
    registrationEndDate: string
    createdAt: string
    updatedAt: string
}

export interface TournamentListItem extends Tournament {
    registeredPlayers: number
}

export interface TournamentPage {
    items: TournamentListItem[]
    total: number
    page: number
    pageSize: number
    pages: number
}

export interface Player {
    id: number
    username: string
    elo: number
}

export interface RegistrationStatus {
    canRegister: boolean
    isRegistered: boolean
    isFull: boolean
    registeredPlayers: number
    reasons: string[]
}

export const STATUS_LABELS: Record<Status, string> = {
    en_attente_de_joueurs: 'En attente de joueurs',
    en_cours: 'En cours',
    termine: 'Terminé',
}

export const STATUS_COLORS: Record<Status, 'success' | 'warning' | 'default'> = {
    en_attente_de_joueurs: 'success',
    en_cours: 'warning',
    termine: 'default',
}

export const formatDate = (date: string) => new Date(date).toLocaleDateString('fr-FR')

export function formatElo(min: number | null, max: number | null) {
    if (min === null && max === null) return 'Tous niveaux'
    if (min === null) return `Elo jusqu'à ${max}`
    if (max === null) return `Elo à partir de ${min}`
    return `Elo : ${min} – ${max}`
}
