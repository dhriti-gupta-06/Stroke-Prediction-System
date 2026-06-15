import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token,    setToken]    = useState(() => localStorage.getItem('ns_token') || null)
  const [username, setUsername] = useState(() => localStorage.getItem('ns_username') || null)

  const login = (tok, user) => {
    localStorage.setItem('ns_token',    tok)
    localStorage.setItem('ns_username', user)
    setToken(tok)
    setUsername(user)
  }

  const logout = () => {
    localStorage.removeItem('ns_token')
    localStorage.removeItem('ns_username')
    setToken(null)
    setUsername(null)
  }

  return (
    <AuthContext.Provider value={{ token, username, login, logout, isLoggedIn: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)