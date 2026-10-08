<template>
  <div class="app-shell">
    <!-- Sidebar: always visible on desktop, slide-over on mobile -->
    <aside class="sidebar" :class="{ open: sidebarOpen }" v-if="auth.user">
      <div class="sidebar-brand">
        <span class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
        </span>
        <span class="brand-text">Phonebook</span>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section-label">Menu</div>
        <router-link to="/" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>
          </svg>
          Dashboard
        </router-link>
        <router-link to="/contacts" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Contacts
        </router-link>
        <router-link to="/contacts/new" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 8v8"/><path d="M8 12h8"/>
          </svg>
          Add Contact
        </router-link>
        <router-link to="/profile" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
          Account
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-chip">
          <span class="avatar">{{ initialsOf(auth.user) }}</span>
          <div class="user-meta">
            <span class="user-name">{{ auth.user.username }}</span>
            <span class="user-email">{{ auth.user.email || '—' }}</span>
          </div>
        </div>
        <button class="nav-item logout-item" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>
          </svg>
          Logout
        </button>
      </div>
    </aside>
    <div class="sidebar-backdrop" v-if="sidebarOpen && auth.user" @click="sidebarOpen = false"></div>

    <!-- Main area -->
    <div class="main-wrapper">
      <header class="topbar" v-if="auth.user">
        <button class="hamburger" @click="sidebarOpen = true" aria-label="Open menu">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M3 6h18"/><path d="M3 12h18"/><path d="M3 18h18"/>
          </svg>
        </button>
        <span class="topbar-title">{{ pageTitle }}</span>
      </header>
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { auth, clearAuth, initialsOf } from './auth'
import api, { extractError } from './api'

const router = useRouter()
const sidebarOpen = ref(false)

// Close the mobile menu whenever the route changes.
watch(
  () => router.currentRoute.value.fullPath,
  () => {
    sidebarOpen.value = false
  }
)

const pageTitle = computed(() => router.currentRoute.value.meta?.title || 'Phonebook')

async function handleLogout() {
  try {
    await api.logout()
  } catch (e) {
    // The token is discarded locally regardless; the API call is
    // best-effort (JWTs are stateless on the server).
    console.warn('Logout request failed:', extractError(e))
  }
  clearAuth()
  router.push({ name: 'login' })
}
</script>
