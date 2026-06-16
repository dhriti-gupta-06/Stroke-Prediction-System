import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token,    setToken]    = useState(() => localStorage.getItem('ns_token') || null)
  const [username, setUsername] = useState(() => localStorage.getItem('ns_username') || null)
  const [role,     setRole]     = useState(() => localStorage.getItem('ns_role') || null)

  const login = (tok, user, userRole) => {
    localStorage.setItem('ns_token',    tok)
    localStorage.setItem('ns_username', user)
    localStorage.setItem('ns_role',     userRole || 'doctor')
    setToken(tok)
    setUsername(user)
    setRole(userRole || 'doctor')
  }

  const logout = () => {
    localStorage.removeItem('ns_token')
    localStorage.removeItem('ns_username')
    localStorage.removeItem('ns_role')
    setToken(null)
    setUsername(null)
    setRole(null)
  }

  const isAdmin = role === 'admin' || username === 'admin'

  return (
    <AuthContext.Provider value={{ token, username, role, isAdmin, login, logout, isLoggedIn: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
