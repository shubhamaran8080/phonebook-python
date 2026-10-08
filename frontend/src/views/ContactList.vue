<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Contacts</h1>
        <p class="subtitle">{{ total.toLocaleString() }} contact{{ total === 1 ? '' : 's' }}</p>
      </div>
      <div class="page-actions">
        <router-link to="/contacts/new" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
          Add Contact
        </router-link>
      </div>
    </header>

    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            v-model="search"
            type="search"
            class="input"
            placeholder="Search by name or phone number..."
            aria-label="Search contacts"
            @input="onSearch"
          />
        </div>
        <select v-model.number="pageSize" class="input" style="width: auto" aria-label="Rows per page" @change="onPageSizeChange">
          <option :value="10">10 / page</option>
          <option :value="25">25 / page</option>
          <option :value="50">50 / page</option>
        </select>
      </div>

      <div v-if="loading" aria-busy="true">
        <div v-for="i in pageSize" :key="i" class="skeleton skeleton-row"></div>
      </div>

      <div v-else-if="error" style="padding: 20px">
        <div class="alert error">{{ error }}</div>
      </div>

      <div v-else-if="contacts.length" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Address</th>
              <th style="text-align: right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="contact in contacts" :key="contact.id">
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
              <td data-label="Address" class="cell-sub">{{ contact.address || '—' }}</td>
              <td data-label="Actions" class="cell-actions">
                <router-link :to="`/contacts/${contact.id}`" class="btn btn-sm">Edit</router-link>
                <button class="btn btn-sm btn-danger" @click="remove(contact)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <h3 v-if="search">No results for "{{ search }}"</h3>
        <h3 v-else>No contacts yet</h3>
        <p v-if="search">Try a different name or phone number.</p>
        <p v-else>Add your first contact to get started.</p>
        <router-link v-if="!search" to="/contacts/new" class="btn btn-primary">Add Contact</router-link>
        <button v-else class="btn" @click="clearSearch">Clear search</button>
      </div>

      <div class="table-footer" v-if="!loading && !error && total > 0">
        <span class="page-info">
          Showing {{ rangeStart }}–{{ rangeEnd }} of {{ total.toLocaleString() }}
        </span>
        <div class="pagination">
          <button class="btn btn-sm" :disabled="page <= 1" @click="goToPage(page - 1)">Previous</button>
          <span>Page {{ page }} of {{ totalPages }}</span>
          <button class="btn btn-sm" :disabled="page >= totalPages" @click="goToPage(page + 1)">Next</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api, { extractError } from '../api'

const contacts = ref([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const search = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const rangeStart = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const rangeEnd = computed(() => Math.min(total.value, page.value * pageSize.value))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.listContacts({
      page: page.value,
      pageSize: pageSize.value,
      search: search.value
    })
    contacts.value = response.data
    total.value = Number(response.headers['x-total-count'] || 0)
    // If the search shrank the result set, clamp the page number.
    if (page.value > totalPages.value) {
      page.value = totalPages.value
      await load()
    }
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}

let searchTimer
function onSearch() {
  page.value = 1
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 250)
}

function clearSearch() {
  search.value = ''
  page.value = 1
  load()
}

function onPageSizeChange() {
  page.value = 1
  load()
}

function goToPage(p) {
  page.value = p
  load()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function remove(contact) {
  if (!confirm(`Delete contact "${contact.name}"?`)) return
  try {
    await api.deleteContact(contact.id)
    await load()
  } catch (e) {
    error.value = extractError(e)
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

onMounted(load)
onUnmounted(() => clearTimeout(searchTimer))
</script>
