import { Button, Paper, TextField } from "@mui/material"

import { useActionState } from "react"
import axiosInstance from "../api/axios-instance"
import { jwtDecode } from "jwt-decode"
import { useAtom } from "jotai"
import sessionState from "../store/session.state"

function LoginPage() {

    const [_, setSession] = useAtom(sessionState)

    function submit(_, data: FormData) {
        return axiosInstance.post('/auth/login', Object.fromEntries(data.entries())).then((result) => {
            // gestion de la connection
            const userInfo = jwtDecode(result.data.access_token) as any
            setSession({ 
                token: result.data.access_token,
                role: userInfo.role,
                id: userInfo.id 
            })
            return { errors: [], data: Object.fromEntries(data.entries()) } 
        }).catch(err => {
            return { errors: [err.message], data: Object.fromEntries(data.entries()) }
        })
    }

    const [formState, action] = useActionState(submit, {
        errors: [],
        data: { username: '', password: '' }
    })

    return <div className="auth-page">
        <Paper className="auth-card" elevation={3}>
            <h2>Se connecter</h2>
            {formState.errors.map((error, i) => (
                <p className="field-error" key={i}>{error}</p>
            ))}
            <form action={action} style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '16px'
            }}>
                <TextField defaultValue={formState.data.username} name="username" label="Username" />
                <TextField defaultValue={formState.data.password} name="password" label="Password" type="password" />
                <Button type="submit" variant="contained" size="large">Se connecter</Button>
            </form>
        </Paper>
    </div>
}

export default LoginPage