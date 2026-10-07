import { useEffect, useState } from "react"
import axios from "axios"
import {
    Button, Checkbox, Chip, CircularProgress, FormControl, FormControlLabel, InputLabel, MenuItem, Pagination,
    Paper, Select, TextField,
} from "@mui/material"
import { Link, useSearchParams } from "react-router-dom"
import { useAtomValue } from "jotai"
import axiosInstance from "../api/axios-instance"
import sessionState from "../store/session.state"
import { CATEGORIES, CATEGORY_BY_VALUE } from "../categories"
import { STATUS_COLORS, STATUS_LABELS, formatDate, type TournamentPage } from "../tournament"

const SEARCH_DEBOUNCE_MS = 300

function HomePage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const session = useAtomValue(sessionState)
    const loggedIn = Boolean(session.token)

    // les filtres vivent dans l'URL : on les retrouve en revenant d'une fiche tournoi
    const name = searchParams.get('name') ?? ''
    const location = searchParams.get('location') ?? ''
    const status = searchParams.get('status') ?? ''
    const categories = searchParams.getAll('categories')
    const womenOnly = searchParams.get('womenOnly') === 'true'
    // les filtres « joueur » n'ont de sens que connecté
    const canRegister = loggedIn && searchParams.get('canRegister') === 'true'
    const registered = loggedIn && searchParams.get('registered') === 'true'
    const page = Number(searchParams.get('page') ?? '1') || 1

    // les champs texte sont saisis localement puis appliqués après une courte pause
    const [nameInput, setNameInput] = useState(name)
    const [locationInput, setLocationInput] = useState(location)

    const [result, setResult] = useState<TournamentPage | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    function updateParams(changes: Record<string, string | string[] | null>, keepPage = false) {
        setSearchParams((previous) => {
            const next = new URLSearchParams(previous)
            for (const [key, value] of Object.entries(changes)) {
                next.delete(key)
                if (Array.isArray(value)) value.forEach((v) => next.append(key, v))
                else if (value) next.set(key, value)
            }
            if (!keepPage) next.delete('page')
            return next
        }, { replace: true })
    }

    useEffect(() => {
        if (nameInput === name && locationInput === location) return
        const timer = setTimeout(
            () => updateParams({ name: nameInput || null, location: locationInput || null }),
            SEARCH_DEBOUNCE_MS,
        )
        return () => clearTimeout(timer)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [nameInput, locationInput])

    const apiParams = new URLSearchParams(searchParams)
    if (!loggedIn) {
        apiParams.delete('canRegister')
        apiParams.delete('registered')
    }
    const query = apiParams.toString()
    const token = session.token
    useEffect(() => {
        // une recherche plus récente annule la précédente (frappe rapide, changement de page, doublon du mode dev)
        const controller = new AbortController()
        setLoading(true)
        axiosInstance.get<TournamentPage>(`/tournaments?${query}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
            signal: controller.signal,
        })
            .then((response) => {
                setResult(response.data)
                setError(null)
            })
            .catch((err) => {
                if (axios.isCancel(err)) return
                setError(err.response?.status === 401
                    ? 'Votre session a expiré, reconnectez-vous pour utiliser ces filtres.'
                    : err.message)
            })
            .finally(() => { if (!controller.signal.aborted) setLoading(false) })
        return () => controller.abort()
    }, [query, token])

    const hasFilters = Boolean(
        name || location || status || categories.length || womenOnly || canRegister || registered
    )

    function resetFilters() {
        setNameInput('')
        setLocationInput('')
        setSearchParams({}, { replace: true })
    }

    function toggleCategory(value: string) {
        updateParams({
            categories: categories.includes(value)
                ? categories.filter((category) => category !== value)
                : [...categories, value],
        })
    }

    const tournaments = result?.items ?? []

    return <div className="home-page">
        <h2>Tournois</h2>

        <Paper className="filters" elevation={3}>
            <div className="filters-row">
                <TextField
                    size="small"
                    label="Nom du tournoi"
                    value={nameInput}
                    onChange={(event) => setNameInput(event.target.value)}
                />
                <TextField
                    size="small"
                    label="Lieu"
                    value={locationInput}
                    onChange={(event) => setLocationInput(event.target.value)}
                />
                <FormControl fullWidth size="small">
                    <InputLabel id="status-filter" shrink>Statut</InputLabel>
                    <Select
                        labelId="status-filter"
                        label="Statut"
                        notched
                        value={status}
                        onChange={(event) => updateParams({ status: event.target.value || null })}
                        displayEmpty
                        renderValue={(value) => value ? STATUS_LABELS[value as keyof typeof STATUS_LABELS] : 'Non clôturés'}
                    >
                        <MenuItem value="">Non clôturés</MenuItem>
                        {Object.entries(STATUS_LABELS).map(([value, label]) => (
                            <MenuItem key={value} value={value}>{label}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </div>
            <div className="filters-row filters-row-categories">
                <span className="filters-label">Catégories</span>
                {CATEGORIES.map((category) => {
                    const selected = categories.includes(category.value)
                    return <Chip
                        key={category.value}
                        label={category.label}
                        size="small"
                        clickable
                        onClick={() => toggleCategory(category.value)}
                        variant={selected ? 'filled' : 'outlined'}
                        sx={selected
                            ? { backgroundColor: category.color, color: '#fff', '&:hover': { backgroundColor: category.color } }
                            : { borderColor: category.color, color: category.color }}
                    />
                })}
                <FormControlLabel
                    control={
                        <Checkbox
                            size="small"
                            checked={womenOnly}
                            onChange={(event) => updateParams({ womenOnly: event.target.checked ? 'true' : null })}
                        />
                    }
                    label="Femmes uniquement"
                />
                {loggedIn && <>
                    <FormControlLabel
                        control={
                            <Checkbox
                                size="small"
                                checked={canRegister}
                                onChange={(event) => updateParams({ canRegister: event.target.checked ? 'true' : null })}
                            />
                        }
                        label="Je peux m'inscrire"
                    />
                    <FormControlLabel
                        control={
                            <Checkbox
                                size="small"
                                checked={registered}
                                onChange={(event) => updateParams({ registered: event.target.checked ? 'true' : null })}
                            />
                        }
                        label="Je suis inscrit"
                    />
                </>}
                <Button className="filters-reset" size="small" onClick={resetFilters} disabled={!hasFilters}>
                    Réinitialiser
                </Button>
            </div>
        </Paper>

        {error && <p className="field-error">{error}</p>}
        {result && !error && (
            <p className="results-count">
                {result.total} tournoi{result.total > 1 ? 's' : ''}
                {loading && <CircularProgress size={14} sx={{ ml: 1 }} />}
            </p>
        )}
        {loading && !result && <CircularProgress />}
        {result && !loading && !error && tournaments.length === 0 && (
            <p>{hasFilters ? 'Aucun tournoi ne correspond à votre recherche.' : 'Aucun tournoi pour le moment.'}</p>
        )}

        <div className="tournament-list" style={{ opacity: loading ? 0.6 : 1 }}>
            {tournaments.map((tournament) => (
                <Link className="tournament-card-link" to={`/tournaments/${tournament.id}`} key={tournament.id}>
                <Paper className="tournament-card" elevation={3}>
                    <h3>{tournament.name} <span className="tournament-id">#{tournament.id}</span></h3>
                    <p>{tournament.location ?? 'Lieu à définir'}</p>
                    <p>
                        {tournament.registeredPlayers} inscrit{tournament.registeredPlayers > 1 ? 's' : ''}
                        {' '}(min {tournament.minPlayers} · max {tournament.maxPlayers})
                    </p>
                    <p>Elo min : {tournament.minElo ?? '—'} · Elo max : {tournament.maxElo ?? '—'}</p>
                    {tournament.status === 'en_attente_de_joueurs' && (
                        <p>Inscriptions jusqu'au {formatDate(tournament.registrationEndDate)}</p>
                    )}
                    <p>Ronde courante : {tournament.currentRound}</p>
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
                </Link>
            ))}
        </div>

        {result && result.pages > 1 && (
            <Pagination
                className="pagination"
                count={result.pages}
                page={Math.min(page, result.pages)}
                onChange={(_event, value) => updateParams({ page: value > 1 ? String(value) : null }, true)}
                color="primary"
                shape="rounded"
            />
        )}
    </div>
}

export default HomePage
