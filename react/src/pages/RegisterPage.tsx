import { Button, FormControl, InputLabel, MenuItem, Paper, Select, TextField } from "@mui/material"
import { useActionState } from "react"
import axiosInstance from "../api/axios-instance"
import { useNavigate } from "react-router-dom"

function RegisterPage() {

    const nav = useNavigate()

    function submit(_, newValues: FormData) {
        return axiosInstance.post(
            '/auth/register', 
            Object.fromEntries(newValues.entries())
        ).then(() => {
            nav('/login')
            return {
                errors: [],
                data: Object.fromEntries(newValues.entries())
            }
        }).catch(err => {
            return {
                errors: [err.message],
                data: Object.fromEntries(newValues.entries())
            }
        })
    }

    const [formState, action] = useActionState(submit, {
        errors: [],
        data: { username: '', email: '', dateOfBirth: '', genre: 'fille', password: '' }
    })

    return <div className="auth-page">
        <Paper className="auth-card" elevation={3}>
            <h2>Créer un compte</h2>
            {formState.errors.map((error, i) => (
                <p className="field-error" key={i}>{error}</p>
            ))}
            <form action={action} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <TextField defaultValue={formState.data.username} name="username" label="Username" />
                <TextField defaultValue={formState.data.email} name="email" label="Email" type="email" />
                <TextField
                    defaultValue={formState.data.dateOfBirth}
                    name="dateOfBirth"
                    label="Date de naissance"
                    type="date"
                    slotProps={{ inputLabel: { shrink: true } }}
                />
                <FormControl fullWidth>
                    <InputLabel id="genre">Genre</InputLabel>
                    <Select defaultValue={formState.data.genre} name="genre" fullWidth label='Genre' labelId="genre">
                        <MenuItem value='fille'>Fille</MenuItem>
                        <MenuItem value='garçon'>Garçon</MenuItem>
                        <MenuItem value='autre'>Autre</MenuItem>
                    </Select>
                </FormControl>
                <TextField
                    defaultValue={formState.data.password}
                    name="password"
                    label="Mot de passe"
                    type="password"
                    helperText="Laisser vide pour générer un mot de passe automatiquement"
                />
                <Button type="submit" variant="contained" size="large">Créer un compte</Button>
            </form>
        </Paper>
    </div>
}

export default RegisterPage