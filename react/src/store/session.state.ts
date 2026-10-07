import { atomWithStorage, createJSONStorage } from 'jotai/utils'

export interface Session {
    token: string | null
    role: string | null
    id: string | null
    username?: string | null
}

const sessionState = atomWithStorage<Session>(
    'session',
    {
        token: null,
        role: null,
        id: null,
    },
    createJSONStorage<Session>(() => localStorage),
    { getOnInit: true },
)

export default sessionState
