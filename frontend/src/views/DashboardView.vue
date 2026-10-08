<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p class="subtitle">Welcome back, {{ auth.user?.username }}</p>
      </div>
      <div class="page-actions">
        <router-link to="/contacts/new" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
          Add Contact
        </router-link>
      </div>
    </header>

    <div v-if="loading" class="stats-grid">
      <div v-for="i in 4" :key="i" class="stat-card skeleton"></div>
    </div>

    <div v-else-if="error" class="alert error">{{ error }}</div>

    <template v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon indigo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div class="stat-body">
            <span class="stat-value">{{ stats.total_contacts }}</span>
            <span class="stat-label">Total Contacts</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          <div class="stat-body">
            <span class="stat-value">{{ stats.recent_contacts }}</span>
            <span class="stat-label">Added in last 7 days</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><path d="M22 6l-10 7L2 6"/></svg>
          </div>
          <div class="stat-body">
            <span class="stat-value">{{ stats.with_email }}</span>
            <span class="stat-label">With email</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon amber">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          </div>
          <div class="stat-body">
            <span class="stat-value">{{ stats.with_phone }}</span>
            <span class="stat-label">With phone</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>Recently added</h2>
          <router-link to="/contacts" class="link">View all contacts</router-link>
        </div>

        <div v-if="stats.recent_list?.length" class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Added</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="contact in stats.recent_list" :key="contact.id">
                <td data-label="Name">
                  <div class="contact-cell">
                    <span class="avatar">{{ initials(contact.name) }}</span>
                    <span class="cell-main">
                      <router-link :to="`/contacts/${contact.id}`">{{ contact.name }}</router-link>
                    </span>
                  </div>
                </td>
                <td data-label="Phone" class="cell-sub">{{ contact.phone_number }}</td>
                <td data-label="Email" class="cell-sub">{{ contact.email || '—' }}</td>
                <td data-label="Added" class="cell-sub">{{ formatDate(contact.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <h3>No contacts yet</h3>
          <p>Add your first contact to get started.</p>
          <router-link to="/contacts/new" class="btn btn-primary">Add Contact</router-link>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api, { extractError } from '../api'
import { auth } from '../auth'

const stats = ref({
  total_contacts: 0,
  recent_contacts: 0,
  with_email: 0,
  with_phone: 0,
  recent_list: []
})
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.getStats()
    stats.value = data
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}

function initials(name) {
  return (name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(load)
</script>
