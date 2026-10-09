import axios from 'axios'
import { auth, clearAuth } from './auth'

// In Docker the nginx proxy forwards /api to the backend;
// in local development the Vite dev server does the same.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api'
})

/**
 * Register a handler that is called when the backend answers
 * with 401 (e.g. expired token). Used to redirect to /login.
 */
let unauthorizedHandler = null
export function onUnauthorized(handler) {
  unauthorizedHandler = handler
}

// Attach the JWT to every request.
api.interceptors.request.use((config) => {
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// On 401, clear the stored session and let the app redirect to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
      if (unauthorizedHandler) unauthorizedHandler()
    }
    return Promise.reject(error)
  }
)

/** Extract a human-readable message from an axios error. */
export function extractError(error) {
  if (error.response) {
    return error.response.data?.detail || `Request failed (${error.response.status})`
  }
  if (error.request) {
    return 'No response from the server. Is the backend running?'
  }
  return error.message
}

export default {
  // --- Authentication ---
  login(credentials) {
    return api.post('/auth/login', credentials)
  },
  logout() {
    return api.post('/auth/logout')
  },
  getMe() {
    return api.get('/auth/me')
  },
  getStats() {
    return api.get('/stats')
  },

  // --- Contacts ---
  listContacts({ page = 1, pageSize = 10, search = '' } = {}) {
    return api.get('/contacts', {
      params: { page, page_size: pageSize, q: search }
    })
  },
  getContact(id) {
    return api.get(`/contacts/${id}`)
  },
  createContact(data) {
    return api.post('/contacts', data)
  },
  updateContact(id, data) {
    return api.put(`/contacts/${id}`, data)
  },
  deleteContact(id) {
    return api.delete(`/contacts/${id}`)
  },

  // --- CSV import / export ---
  importContacts(formData) {
    return api.post('/contacts/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  exportContacts(search = '') {
    // The backend streams a CSV of every contact the
    // search matches (not just the current page).
    return api.get('/contacts/export', {
      params: search ? { q: search } : {},
      responseType: 'blob'
    })
  }
}
