import { createContext, useContext, useState } from 'react'

const UserContext = createContext()

export function UserProvider({ children }) {
  const [username, setUsername] = useState(() => localStorage.getItem('relay-username') || '')

  const saveUsername = (name) => {
    setUsername(name)
    localStorage.setItem('relay-username', name)
  }

  return <UserContext.Provider value={{ username, setUsername: saveUsername }}>{children}</UserContext.Provider>
}

export const useUser = () => useContext(UserContext)
