import { reactive, computed } from 'vue'

const TOKEN_KEY = 'phonebook_token'
const USER_KEY = 'phonebook_user'

/** Authentication state shared across the app. */
export const auth = reactive({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  loggingIn: false
})

export const isAuthenticated = computed(() => Boolean(auth.token))

export function setAuth(token, user) {
  auth.token = token
  auth.user = user
  localStorage.setItem(TOKEN_KEY, token)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  auth.token = null
  auth.user = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function initialsOf(user) {
  if (!user?.username) return '?'
  return user.username
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}
