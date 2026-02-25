/* eslint-disable react-refresh/only-export-components */
import React, { useState, useEffect, createContext, useContext } from 'react'
import { hackathonApi } from '../lib/api'

export interface DiscordUser {
  discord_id: string
  username: string
  discriminator?: string
  avatar?: string
}

export interface AuthState {
  isAuthenticated: boolean
  authMethod: 'discord' | null
  discordUser: DiscordUser | null
}

export interface AuthContextType {
  authState: AuthState
  login: (discordUser: DiscordUser, token: string) => void
  logout: () => void
  loading: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Dev mode: bypass Discord auth for local recording/demos
// Only enabled when VITE_DEV_MODE is explicitly 'true' AND not in production
function isDevMode(): boolean {
  const flag = import.meta.env.VITE_DEV_MODE
  const isProd = import.meta.env.PROD
  if (isProd && flag === 'true') {
    console.warn('VITE_DEV_MODE is ignored in production builds')
    return false
  }
  return flag === 'true'
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const devMode = isDevMode()

  const [authState, setAuthState] = useState<AuthState>(
    devMode
      ? {
          isAuthenticated: true,
          authMethod: 'discord',
          discordUser: { discord_id: 'dev', username: 'DevMode' }
        }
      : {
          isAuthenticated: false,
          authMethod: null,
          discordUser: null
        }
  )
  const [loading, setLoading] = useState(!devMode)

  useEffect(() => {
    if (devMode) return

    // Check for existing Discord authentication on mount
    const checkExistingAuth = async () => {
      try {
        const token = localStorage.getItem('discord_token')
        if (token) {
          // Verify token is still valid
          const user = await hackathonApi.getCurrentUser(token)
          setAuthState({
            isAuthenticated: true,
            authMethod: 'discord',
            discordUser: user
          })
        }
      } catch (error) {
        // Token is invalid, clear it
        localStorage.removeItem('discord_token')
        console.warn('Stored Discord token is invalid, cleared from storage')
      } finally {
        setLoading(false)
      }
    }

    checkExistingAuth()
  }, [])

  const login = (discordUser: DiscordUser, token: string) => {
    localStorage.setItem('discord_token', token)
    setAuthState({
      isAuthenticated: true,
      authMethod: 'discord',
      discordUser
    })
  }

  const logout = async () => {
    try {
      await hackathonApi.discordLogout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('discord_token')
      setAuthState({
        isAuthenticated: false,
        authMethod: null,
        discordUser: null
      })
    }
  }

  return (
    <AuthContext.Provider value={{
      authState,
      login,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}