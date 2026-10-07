import { useCallback, useEffect, useState } from "react"
import {
    Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, MenuItem,
    Paper, Select, Table, TableBody, TableCell, TableHead, TableRow,
} from "@mui/material"
import { Link, useNavigate, useParams } from "react-router-dom"
import { useAtomValue } from "jotai"
import axiosInstance from "../api/axios-instance"
import sessionState from "../store/session.state"
import { CATEGORY_BY_VALUE } from "../categories"
import {
    MATCH_RESULT_LABELS, STATUS_COLORS, STATUS_LABELS, formatDate, formatElo, formatScore,
    type Match, type MatchResult, type Player, type RegistrationStatus, type Scoreboard, type TournamentListItem,
} from "../tournament"

type AdminAction = 'start' | 'delete' | 'next'

const errorMessage = (err: any) => err.response?.data?.detail ?? err.message

function TournamentDetailPage() {
    const { id } = useParams()
    const nav = useNavigate()
    const session = useAtomValue(sessionState)
    const isAdmin = session.role === 'admin'
    const authHeaders = { Authorization: `Bearer ${session.token}` }

    const [tournament, setTournament] = useState<TournamentListItem | null>(null)
    const [players, setPlayers] = useState<Player[]>([])
    const [matches, setMatches] = useState<Match[]>([])
    const [scoreboard, setScoreboard] = useState<Scoreboard | null>(null)
    const [scoreRound, setScoreRound] = useState<number | null>(null) // null = ronde courante
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
            axiosInstance.get<Match[]>(`/tournaments/${id}/matches`).then((r) => setMatches(r.data)),
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

    // classement : se recharge quand on change de ronde affichée, ou quand un résultat / la ronde courante change
    const status = tournament?.status
    const currentRound = tournament?.currentRound
    const playedCount = matches.filter((match) => match.result !== 'pas_encore_joue').length
    useEffect(() => {
        if (!status || status === 'en_attente_de_joueurs') {
            setScoreboard(null)
            return
        }
        let cancelled = false
        axiosInstance.get<Scoreboard>(`/tournaments/${id}/scoreboard`, { params: scoreRound ? { round: scoreRound } : undefined })
            .then((r) => { if (!cancelled) setScoreboard(r.data) })
            .catch(() => { if (!cancelled) setScoreboard(null) })
        return () => { cancelled = true }
    }, [id, status, currentRound, scoreRound, playedCount])

    function changeRegistration(method: 'post' | 'delete') {
        setRegistering(true)
        setActionError(null)
        axiosInstance.request({ url: `/tournaments/${id}/registration`, method, headers: authHeaders })
            .then(() => refresh())
            .catch((err) => setActionError(errorMessage(err)))
            .finally(() => setRegistering(false))
    }

    function setResult(match: Match, result: MatchResult) {
        setActionError(null)
        axiosInstance.patch(`/tournaments/${id}/matches/${match.id}`, { result }, { headers: authHeaders })
            .then(() => refresh())
            .catch((err) => setActionError(errorMessage(err)))
    }

    function confirmAction() {
        const request = pendingAction === 'delete'
            ? axiosInstance.delete(`/tournaments/${id}`, { headers: authHeaders }).then(() => nav('/'))
            : axiosInstance
                .post(`/tournaments/${id}/${pendingAction === 'next' ? 'next-round' : 'start'}`, null, { headers: authHeaders })
                .then(() => refresh())

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
    const running = tournament.status === 'en_cours'
    const lastRound = Math.max(0, ...matches.map((match) => match.round))
    const isLastRound = tournament.currentRound >= lastRound
    const unplayedInCurrentRound = matches.filter(
        (match) => match.round === tournament.currentRound && match.result === 'pas_encore_joue'
    ).length

    // rencontres regroupées par ronde
    const matchesByRound = new Map<number, Match[]>()
    for (const match of matches) {
        matchesByRound.set(match.round, [...(matchesByRound.get(match.round) ?? []), match])
    }

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
                {running && (
                    <div className="admin-actions">
                        <Button
                            variant="contained"
                            color="success"
                            disabled={unplayedInCurrentRound > 0}
                            onClick={() => setPendingAction('next')}
                        >
                            {isLastRound ? 'Terminer le tournoi' : 'Passer à la ronde suivante'}
                        </Button>
                        {unplayedInCurrentRound > 0 && (
                            <span className="admin-hint">
                                {unplayedInCurrentRound} rencontre{unplayedInCurrentRound > 1 ? 's' : ''} à jouer dans la ronde {tournament.currentRound}
                            </span>
                        )}
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

            {scoreboard && <>
                <div className="scoreboard-header">
                    <h3 className="players-title">Classement</h3>
                    <Select
                        size="small"
                        value={scoreRound ?? scoreboard.round}
                        onChange={(event) => {
                            const round = Number(event.target.value)
                            setScoreRound(round === tournament.currentRound ? null : round)
                        }}
                    >
                        {Array.from({ length: scoreboard.lastRound }, (_, index) => index + 1).map((round) => (
                            <MenuItem key={round} value={round}>
                                Après la ronde {round}{round === tournament.currentRound ? ' (courante)' : ''}
                            </MenuItem>
                        ))}
                    </Select>
                </div>
                <Table size="small" className="scoreboard">
                    <TableHead>
                        <TableRow>
                            <TableCell>#</TableCell>
                            <TableCell>Joueur</TableCell>
                            <TableCell align="right" title="Rencontres jouées">J</TableCell>
                            <TableCell align="right" title="Victoires">V</TableCell>
                            <TableCell align="right" title="Défaites">D</TableCell>
                            <TableCell align="right" title="Égalités">N</TableCell>
                            <TableCell align="right">Score</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {scoreboard.rows.map((row) => (
                            <TableRow key={row.playerId}>
                                <TableCell>{row.rank}</TableCell>
                                <TableCell>{row.username}</TableCell>
                                <TableCell align="right">{row.played}</TableCell>
                                <TableCell align="right">{row.wins}</TableCell>
                                <TableCell align="right">{row.losses}</TableCell>
                                <TableCell align="right">{row.draws}</TableCell>
                                <TableCell align="right"><strong>{formatScore(row.score)}</strong></TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </>}

            {matches.length > 0 && <>
                <h3 className="players-title">Rencontres ({matches.length})</h3>
                {[...matchesByRound.entries()].map(([round, roundMatches]) => (
                    <div key={round} className={`round-block${round === tournament.currentRound ? ' round-current' : ''}`}>
                        <h4>
                            Ronde {round}
                            {round === tournament.currentRound && <Chip size="small" color="warning" label="En cours" sx={{ ml: 1 }} />}
                        </h4>
                        <ul className="match-list">
                            {roundMatches.map((match) => (
                                <li key={match.id}>
                                    <span className="match-white">⬜ {match.whiteUsername ?? `#${match.whiteId}`}</span>
                                    {isAdmin && running && match.round === tournament.currentRound
                                        ? <Select
                                            size="small"
                                            className="match-result-select"
                                            value={match.result}
                                            onChange={(event) => setResult(match, event.target.value as MatchResult)}
                                        >
                                            {Object.entries(MATCH_RESULT_LABELS).map(([value, label]) => (
                                                <MenuItem key={value} value={value}>{label}</MenuItem>
                                            ))}
                                        </Select>
                                        : <span className="match-result">{MATCH_RESULT_LABELS[match.result]}</span>}
                                    <span className="match-black">{match.blackUsername ?? `#${match.blackId}`} ⬛</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </>}
        </Paper>

        <Dialog open={pendingAction !== null} onClose={() => setPendingAction(null)}>
            <DialogTitle>
                {pendingAction === 'delete' && 'Supprimer le tournoi ?'}
                {pendingAction === 'start' && 'Commencer le tournoi ?'}
                {pendingAction === 'next' && (isLastRound ? 'Terminer le tournoi ?' : 'Passer à la ronde suivante ?')}
            </DialogTitle>
            <DialogContent>
                <DialogContentText>
                    {pendingAction === 'delete' &&
                        `« ${tournament.name} » sera supprimé définitivement et les joueurs inscrits seront prévenus par mail.`}
                    {pendingAction === 'start' &&
                        `« ${tournament.name} » passera en cours : les rencontres seront générées, les inscriptions closes et le tournoi ne pourra plus être modifié.`}
                    {pendingAction === 'next' && (isLastRound
                        ? `La dernière ronde est terminée : « ${tournament.name} » passera au statut terminé et plus aucun résultat ne pourra être modifié.`
                        : `La ronde ${tournament.currentRound} sera close : ses résultats ne pourront plus être modifiés.`)}
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setPendingAction(null)}>Annuler</Button>
                <Button
                    onClick={confirmAction}
                    color={pendingAction === 'delete' ? 'error' : 'success'}
                    variant="contained"
                >
                    {pendingAction === 'delete' && 'Supprimer'}
                    {pendingAction === 'start' && 'Commencer'}
                    {pendingAction === 'next' && (isLastRound ? 'Terminer' : 'Passer à la suite')}
                </Button>
            </DialogActions>
        </Dialog>
    </div>
}

export default TournamentDetailPage
