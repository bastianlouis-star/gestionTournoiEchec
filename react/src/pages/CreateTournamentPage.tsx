import { Button, Checkbox, FormControlLabel, FormGroup, FormLabel, Paper, TextField } from "@mui/material"
import { useActionState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { useAtomValue } from "jotai"
import axiosInstance from "../api/axios-instance"
import sessionState from "../store/session.state"
import { CATEGORIES } from "../categories"

interface FormValues {
    name: string
    location: string
    minPlayers: string
    maxPlayers: string
    minElo: string
    maxElo: string
    categories: string[]
    womenOnly: boolean
    registrationEndDate: string
}

interface FormState {
    errors: string[]
    data: FormValues
}

const initialState: FormState = {
    errors: [],
    data: {
        name: '',
        location: '',
        minPlayers: '2',
        maxPlayers: '32',
        minElo: '',
        maxElo: '',
        categories: CATEGORIES.map((category) => category.value),
        womenOnly: false,
        registrationEndDate: '',
    },
}

function extractErrors(err: any): string[] {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return [detail]
    if (Array.isArray(detail)) return detail.map((d) => d.msg)
    return [err.message]
}

const optionalNumber = (value: string) => value === '' ? null : Number(value)

function CreateTournamentPage() {

    const session = useAtomValue(sessionState)
    const nav = useNavigate()

    function submit(_: FormState, formData: FormData): Promise<FormState> {
        const values: FormValues = {
            name: String(formData.get('name') ?? ''),
            location: String(formData.get('location') ?? ''),
            minPlayers: String(formData.get('minPlayers') ?? ''),
            maxPlayers: String(formData.get('maxPlayers') ?? ''),
            minElo: String(formData.get('minElo') ?? ''),
            maxElo: String(formData.get('maxElo') ?? ''),
            categories: formData.getAll('categories').map(String),
            womenOnly: formData.get('womenOnly') === 'on',
            registrationEndDate: String(formData.get('registrationEndDate') ?? ''),
        }

        if (values.categories.length === 0) {
            return Promise.resolve({ errors: ['Choisissez au moins une catégorie.'], data: values })
        }

        return axiosInstance.post('/tournaments', {
            name: values.name,
            location: values.location || null,
            minPlayers: Number(values.minPlayers),
            maxPlayers: Number(values.maxPlayers),
            minElo: optionalNumber(values.minElo),
            maxElo: optionalNumber(values.maxElo),
            categories: values.categories,
            womenOnly: values.womenOnly,
            registrationEndDate: values.registrationEndDate,
        }, {
            headers: { Authorization: `Bearer ${session.token}` },
        }).then(() => {
            nav('/')
            return { errors: [], data: values }
        }).catch((err) => {
            return { errors: extractErrors(err), data: values }
        })
    }

    const [formState, action] = useActionState(submit, initialState)

    if (session.role !== 'admin') {
        return <Navigate to="/" replace />
    }

    return <div className="auth-page">
        <Paper className="auth-card" elevation={3}>
            <h2>Créer un tournoi</h2>
            {formState.errors.map((error, i) => (
                <p className="field-error" key={i}>{error}</p>
            ))}
            <form action={action} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <TextField defaultValue={formState.data.name} name="name" label="Nom" required />
                <TextField defaultValue={formState.data.location} name="location" label="Lieu" />
                <div style={{ display: 'flex', gap: '16px' }}>
                    <TextField
                        defaultValue={formState.data.minPlayers}
                        name="minPlayers"
                        label="Joueurs minimum"
                        type="number"
                        required
                        slotProps={{ htmlInput: { min: 2, max: 32 } }}
                    />
                    <TextField
                        defaultValue={formState.data.maxPlayers}
                        name="maxPlayers"
                        label="Joueurs maximum"
                        type="number"
                        required
                        slotProps={{ htmlInput: { min: 2, max: 32 } }}
                    />
                </div>
                <div style={{ display: 'flex', gap: '16px' }}>
                    <TextField
                        defaultValue={formState.data.minElo}
                        name="minElo"
                        label="Elo minimum"
                        type="number"
                        slotProps={{ htmlInput: { min: 0, max: 3000 } }}
                    />
                    <TextField
                        defaultValue={formState.data.maxElo}
                        name="maxElo"
                        label="Elo maximum"
                        type="number"
                        slotProps={{ htmlInput: { min: 0, max: 3000 } }}
                    />
                </div>
                <div>
                    <FormLabel component="legend">Catégories</FormLabel>
                    <FormGroup row>
                        {CATEGORIES.map((category) => (
                            <FormControlLabel
                                key={category.value}
                                label={<span style={{ color: category.color, fontWeight: 600 }}>{category.label}</span>}
                                control={
                                    <Checkbox
                                        name="categories"
                                        value={category.value}
                                        sx={{ color: category.color, '&.Mui-checked': { color: category.color } }}
                                        defaultChecked={formState.data.categories.includes(category.value)}
                                    />
                                }
                            />
                        ))}
                    </FormGroup>
                </div>
                <TextField
                    defaultValue={formState.data.registrationEndDate}
                    name="registrationEndDate"
                    label="Fin des inscriptions"
                    type="date"
                    required
                    helperText="Doit être postérieure à aujourd'hui + le nombre minimum de joueurs (en jours)"
                    slotProps={{ inputLabel: { shrink: true } }}
                />
                <FormControlLabel
                    control={<Checkbox name="womenOnly" defaultChecked={formState.data.womenOnly} />}
                    label="Réservé aux femmes"
                />
                <Button type="submit" variant="contained" size="large">Créer le tournoi</Button>
            </form>
        </Paper>
    </div>
}

export default CreateTournamentPage
