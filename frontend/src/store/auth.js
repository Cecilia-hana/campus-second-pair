import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  actions: {
    setUser(u, token) {
      this.user = u
      localStorage.setItem('user', JSON.stringify(u))
      localStorage.setItem('token', token)
    },
    logout() {
      this.user = null
      localStorage.removeItem('user')
      localStorage.removeItem('token')
    }
  }
})
