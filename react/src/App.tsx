import { AppBar, Button, Toolbar } from '@mui/material'
import './App.css'
import { NavLink, Route, Routes } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { useAtom } from 'jotai'
import sessionState from './store/session.state'

function App() {  
  
  const [session, setSession] = useAtom(sessionState)

  return (
    <>
      <AppBar position='static' color='primary'>
        <Toolbar>
          <h1 className='app-title' color='inherit'>Gestion de tournoi d'échec</h1>
          { !session.token ? 
          <>
            <NavLink style={{ color: 'inherit' }} to='/register'>
              <Button color='inherit'>Register</Button>
            </NavLink>
            <NavLink style={{ color: 'inherit' }} to='/login'>
              <Button color='inherit'>Login</Button>
            </NavLink> 
          </>
          : <>
            <p>{session.role}</p>
            <Button color='inherit' onClick={() => {
              setSession({ token: null, role: null, id: null })
            }}>Se déconnecter</Button>
          </>}
        </Toolbar>
      </AppBar>
      <main>
        <Routes>
          <Route path='/login' element={<LoginPage />} />
          <Route path='/register' element={<RegisterPage />} />
        </Routes>
      </main>
    </>
  )
}

export default App