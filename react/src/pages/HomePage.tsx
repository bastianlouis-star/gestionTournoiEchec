import { useEffect, useState } from "react"
import { Chip, CircularProgress, Paper } from "@mui/material"
import axiosInstance from "../api/axios-instance"
import { CATEGORY_BY_VALUE, type Category } from "../categories"

type Status = 'en_attente_de_joueurs' | 'en_cours' | 'termine'

interface Tournament {
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
}

const STATUS_LABELS: Record<Status, string> = {
    en_attente_de_joueurs: 'En attente de joueurs',
    en_cours: 'En cours',
    termine: 'Terminé',
}

const STATUS_COLORS: Record<Status, 'success' | 'warning' | 'default'> = {
    en_attente_de_joueurs: 'success',
    en_cours: 'warning',
    termine: 'default',
}

const formatDate = (date: string) => new Date(date).toLocaleDateString('fr-FR')

function formatElo(min: number | null, max: number | null) {
    if (min === null && max === null) return 'Tous niveaux'
    if (min === null) return `Elo jusqu'à ${max}`
    if (max === null) return `Elo à partir de ${min}`
    return `Elo : ${min} – ${max}`
}

function HomePage() {
    const [tournaments, setTournaments] = useState<Tournament[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        axiosInstance.get<Tournament[]>('/tournaments')
            .then((result) => setTournaments(result.data))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false))
    }, [])

    return <div className="home-page">
        <h2>Tournois</h2>
        {loading && <CircularProgress />}
        {error && <p className="field-error">{error}</p>}
        {!loading && !error && tournaments.length === 0 && <p>Aucun tournoi pour le moment.</p>}
        <div className="tournament-list">
            {tournaments.map((tournament) => (
                <Paper className="tournament-card" elevation={3} key={tournament.id}>
                    <h3>{tournament.name}</h3>
                    <p>{tournament.location ?? 'Lieu à définir'}</p>
                    <p>{tournament.minPlayers} à {tournament.maxPlayers} joueurs</p>
                    <p>{formatElo(tournament.minElo, tournament.maxElo)}</p>
                    {tournament.status === 'en_attente_de_joueurs' && (
                        <p>Inscriptions jusqu'au {formatDate(tournament.registrationEndDate)}</p>
                    )}
                    {tournament.status === 'en_cours' && <p>Ronde {tournament.currentRound}</p>}
                    <div className="tournament-tags">
                        <Chip
                            size="small"
                            label={STATUS_LABELS[tournament.status]}
                            color={STATUS_COLORS[tournament.status]}
                        />
                        {tournament.categories.map((category) => (
                            <Chip
                                key={category}
                                size="small"
                                label={CATEGORY_BY_VALUE[category].label}
                                sx={{ backgroundColor: CATEGORY_BY_VALUE[category].color, color: '#fff' }}
                            />
                        ))}
                        {tournament.womenOnly && <Chip size="small" label="Femmes uniquement" color="secondary" />}
                    </div>
                </Paper>
            ))}
        </div>
    </div>
}

export default HomePage
