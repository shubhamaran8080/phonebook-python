import axios from 'axios'

// In Docker the nginx proxy forwards /api to the backend;
// in local development the Vite dev server does the same.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api'
})

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
  }
}
