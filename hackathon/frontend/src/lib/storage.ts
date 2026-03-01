// Storage utility for managing auth tokens and user data
// This centralizes localStorage access for better testability and maintainability

interface DiscordAuth {
  user: {
    username: string
    discriminator: string
    id: string
    avatar?: string
  }
  accessToken: string
}

export const storage = {
  // Discord authentication
  getDiscordAuth(): DiscordAuth | null {
    try {
      const data = localStorage.getItem('discord_auth')
      return data ? JSON.parse(data) : null
    } catch (error) {
      console.error('Failed to parse Discord auth from localStorage:', error)
      return null
    }
  },

  setDiscordAuth(auth: DiscordAuth): void {
    try {
      localStorage.setItem('discord_auth', JSON.stringify(auth))
    } catch (error) {
      console.error('Failed to save Discord auth to localStorage:', error)
    }
  },

  removeDiscordAuth(): void {
    localStorage.removeItem('discord_auth')
  },

  // Clear all auth data
  clearAuth(): void {
    this.removeDiscordAuth()
    // Clear any legacy invite code data if it exists
    localStorage.removeItem('invite_code')
  }
} 