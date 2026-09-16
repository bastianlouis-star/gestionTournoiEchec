import { atom } from 'jotai'

export interface Session {
    token: string | null
    role: string | null
    id: string | null
}

const sessionState = atom<Session>({
    token: null,
    role: null,
    id: null,
})

export default sessionState
