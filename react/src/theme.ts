import { createTheme } from '@mui/material/styles'

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#1f2733',
            light: '#3a4553',
            dark: '#12161d',
            contrastText: '#f5f2e9',
        },
        secondary: {
            main: '#c9a227',
            light: '#ddbb52',
            dark: '#9c7c17',
            contrastText: '#1f2733',
        },
        background: {
            default: '#f4f1ea',
            paper: '#ffffff',
        },
        text: {
            primary: '#1f2733',
            secondary: '#5b6472',
        },
    },
    shape: {
        borderRadius: 12,
    },
    typography: {
        fontFamily: '"Segoe UI", system-ui, Roboto, sans-serif',
        h1: { fontWeight: 700 },
        h2: { fontWeight: 600 },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                    borderRadius: 8,
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                },
            },
        },
        MuiTextField: {
            defaultProps: {
                fullWidth: true,
                variant: 'outlined',
            },
        },
    },
})

export default theme
