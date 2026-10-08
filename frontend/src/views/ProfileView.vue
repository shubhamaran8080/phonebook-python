<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Account</h1>
        <p class="subtitle">Your profile and session details</p>
      </div>
    </header>

    <div v-if="loading" class="card"><div class="skeleton skeleton-row"></div></div>
    <div v-else-if="error" class="alert error">{{ error }}</div>

    <div v-else-if="user" class="card">
      <div class="profile-header">
        <span class="avatar large">{{ initialsOf(user) }}</span>
        <div>
          <h2>{{ user.username }}</h2>
          <p class="subtitle">{{ user.email || 'No email address' }}</p>
        </div>
      </div>
      <div class="profile-field">
        <span class="k">Username</span>
        <span class="v">{{ user.username }}</span>
      </div>
      <div class="profile-field">
        <span class="k">Email</span>
        <span class="v">{{ user.email || '—' }}</span>
      </div>
      <div class="profile-field">
        <span class="k">Member since</span>
        <span class="v">{{ formatDate(user.created_at) }}</span>
      </div>
      <div class="card-body" style="border-top: 1px solid var(--border)">
        <button class="btn btn-danger" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>
          </svg>
          Log out
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { extractError } from '../api'
import { auth, clearAuth, initialsOf } from '../auth'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    // Prefer fresh data from the API; fall back to the stored session.
    const { data } = await api.getMe()
    user.value = data
  } catch (e) {
    if (auth.user) {
      user.value = auth.user
    } else {
      error.value = extractError(e)
    }
  } finally {
    loading.value = false
  }
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

async function handleLogout() {
  try {
    await api.logout()
  } catch (e) {
    console.warn('Logout request failed:', extractError(e))
  }
  clearAuth()
  router.push({ name: 'login' })
}

onMounted(load)
</script>
