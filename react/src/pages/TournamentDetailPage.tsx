import { useCallback, useEffect, useState } from "react"
import {
    Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Paper,
} from "@mui/material"
import { Link, useNavigate, useParams } from "react-router-dom"
import { useAtomValue } from "jotai"
import axiosInstance from "../api/axios-instance"
import sessionState from "../store/session.state"
import { CATEGORY_BY_VALUE } from "../categories"
import {
    STATUS_COLORS, STATUS_LABELS, formatDate, formatElo,
    type Player, type RegistrationStatus, type TournamentListItem,
} from "../tournament"

type AdminAction = 'start' | 'delete'

const errorMessage = (err: any) => err.response?.data?.detail ?? err.message

function TournamentDetailPage() {
    const { id } = useParams()
    const nav = useNavigate()
    const session = useAtomValue(sessionState)
    const isAdmin = session.role === 'admin'
    const authHeaders = { Authorization: `Bearer ${session.token}` }

    const [tournament, setTournament] = useState<TournamentListItem | null>(null)
    const [players, setPlayers] = useState<Player[]>([])
    const [registration, setRegistration] = useState<RegistrationStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [pendingAction, setPendingAction] = useState<AdminAction | null>(null)
    const [actionError, setActionError] = useState<string | null>(null)
    const [registering, setRegistering] = useState(false)

    // tournoi + inscrits (publics) et statut d'inscription (si connecté)
    const refresh = useCallback(() => {
        const requests: Promise<unknown>[] = [
            axiosInstance.get<TournamentListItem>(`/tournaments/${id}`).then((r) => setTournament(r.data)),
            axiosInstance.get<Player[]>(`/tournaments/${id}/players`).then((r) => setPlayers(r.data)),
        ]
        if (session.token) {
            requests.push(
                axiosInstance.get<RegistrationStatus>(`/tournaments/${id}/registration`, {
                    headers: { Authorization: `Bearer ${session.token}` },
                })
                    .then((r) => setRegistration(r.data))
                    .catch(() => setRegistration(null)),
            )
        } else {
            setRegistration(null)
        }
        return Promise.all(requests)
    }, [id, session.token])

    useEffect(() => {
        setLoading(true)
        setError(null)
        refresh()
            .catch((err) => setError(err.response?.status === 404 ? 'Tournoi introuvable.' : err.message))
            .finally(() => setLoading(false))
    }, [refresh])

    function changeRegistration(method: 'post' | 'delete') {
        setRegistering(true)
        setActionError(null)
        axiosInstance.request({ url: `/tournaments/${id}/registration`, method, headers: authHeaders })
            .then(() => refresh())
            .catch((err) => setActionError(errorMessage(err)))
            .finally(() => setRegistering(false))
    }

    function confirmAction() {
        const request = pendingAction === 'delete'
            ? axiosInstance.delete(`/tournaments/${id}`, { headers: authHeaders }).then(() => nav('/'))
            : axiosInstance.post(`/tournaments/${id}/start`, null, { headers: authHeaders }).then(() => refresh())

        request
            .then(() => setActionError(null))
            .catch((err) => setActionError(errorMessage(err)))
            .finally(() => setPendingAction(null))
    }

    if (loading) {
        return <div className="home-page"><CircularProgress /></div>
    }

    if (error || !tournament) {
        return <div className="home-page">
            <p className="field-error">{error ?? 'Tournoi introuvable.'}</p>
            <Link to="/">Retour aux tournois</Link>
        </div>
    }

    const waiting = tournament.status === 'en_attente_de_joueurs'

    return <div className="home-page">
        <Link to="/">← Retour aux tournois</Link>
        <Paper className="tournament-detail" elevation={3}>
            <h2>{tournament.name}</h2>
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

            <dl className="detail-list">
                <dt>Lieu</dt>
                <dd>{tournament.location ?? 'À définir'}</dd>
                <dt>Joueurs</dt>
                <dd>
                    {tournament.registeredPlayers} inscrit{tournament.registeredPlayers > 1 ? 's' : ''}
                    {' '}(min {tournament.minPlayers} · max {tournament.maxPlayers})
                </dd>
                <dt>Niveau</dt>
                <dd>{formatElo(tournament.minElo, tournament.maxElo)}</dd>
                {waiting && <>
                    <dt>Fin des inscriptions</dt>
                    <dd>{formatDate(tournament.registrationEndDate)}</dd>
                </>}
                {!waiting && <>
                    <dt>Ronde actuelle</dt>
                    <dd>{tournament.currentRound}</dd>
                </>}
                <dt>Créé le</dt>
                <dd>{formatDate(tournament.createdAt)}</dd>
                <dt>Mis à jour le</dt>
                <dd>{formatDate(tournament.updatedAt)}</dd>
            </dl>

            {!session.token && waiting && <p>Connectez-vous pour vous inscrire.</p>}
            {registration?.isRegistered && (
                <div className="registration-box">
                    <p className="registered-message">✓ Vous êtes inscrit à ce tournoi.</p>
                    {waiting && (
                        <Button variant="outlined" color="error" disabled={registering}
                                onClick={() => changeRegistration('delete')}>
                            Se désinscrire
                        </Button>
                    )}
                </div>
            )}
            {registration?.canRegister && (
                <Button variant="contained" size="large" disabled={registering}
                        onClick={() => changeRegistration('post')}>
                    S'inscrire
                </Button>
            )}
            {registration && !registration.canRegister && !registration.isRegistered && (
                <div>
                    <p>Vous ne pouvez pas vous inscrire à ce tournoi :</p>
                    <ul className="registration-reasons">
                        {registration.reasons.map((reason) => <li key={reason}>{reason}</li>)}
                    </ul>
                </div>
            )}

            {isAdmin && <>
                {waiting && (
                    <div className="admin-actions">
                        <Button variant="contained" color="success" onClick={() => setPendingAction('start')}>
                            Commencer le tournoi
                        </Button>
                        <Button variant="outlined" color="error" onClick={() => setPendingAction('delete')}>
                            Supprimer le tournoi
                        </Button>
                    </div>
                )}
            </>}
            {actionError && <p className="field-error">{actionError}</p>}

            <h3 className="players-title">Joueurs inscrits ({players.length})</h3>
            {players.length === 0
                ? <p>Aucun joueur inscrit pour le moment.</p>
                : <ol className="players-list">
                    {players.map((player) => (
                        <li key={player.id}>
                            {player.username} <span className="player-elo">({player.elo})</span>
                        </li>
                    ))}
                </ol>}
        </Paper>

        <Dialog open={pendingAction !== null} onClose={() => setPendingAction(null)}>
            <DialogTitle>
                {pendingAction === 'delete' ? 'Supprimer le tournoi ?' : 'Commencer le tournoi ?'}
            </DialogTitle>
            <DialogContent>
                <DialogContentText>
                    {pendingAction === 'delete'
                        ? `« ${tournament.name} » sera supprimé définitivement et les joueurs inscrits seront prévenus par mail.`
                        : `« ${tournament.name} » passera en cours : les inscriptions seront closes et le tournoi ne pourra plus être modifié.`}
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setPendingAction(null)}>Annuler</Button>
                <Button
                    onClick={confirmAction}
                    color={pendingAction === 'delete' ? 'error' : 'success'}
                    variant="contained"
                >
                    {pendingAction === 'delete' ? 'Supprimer' : 'Commencer'}
                </Button>
            </DialogActions>
        </Dialog>
    </div>
}

export default TournamentDetailPage
