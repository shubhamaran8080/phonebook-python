<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Contacts</h1>
        <p class="subtitle">{{ total.toLocaleString() }} contact{{ total === 1 ? '' : 's' }}</p>
      </div>
      <div class="page-actions">
        <input
          ref="fileInput"
          type="file"
          accept=".csv,text/csv"
          class="file-input"
          aria-label="Choose a CSV file to import"
          @change="onFileSelected"
        />
        <button
          class="btn"
          type="button"
          :disabled="busy"
          aria-label="Import contacts from a CSV file"
          @click="triggerImport"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>
          <template v-if="importing">Importing...</template>
          <template v-else>Import CSV</template>
        </button>
        <button
          class="btn"
          type="button"
          :disabled="busy"
          aria-label="Export contacts to a CSV file"
          @click="exportCsv"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/></svg>
          <template v-if="exporting">Exporting...</template>
          <template v-else>Export CSV</template>
        </button>
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
        <button class="link" type="button" @click="downloadTemplate">CSV template</button>
      </div>

      <div v-if="importResult || csvError" class="import-panel" aria-live="polite">
        <div v-if="csvError" class="alert error">{{ csvError }}</div>
        <template v-else>
          <div class="alert" :class="importAlertClass">{{ importMessage }}</div>
          <div v-if="importResult.errors && importResult.errors.length" class="error-list">
            <h4>Rows with errors ({{ importResult.errors.length }})</h4>
            <ul>
              <li v-for="err in importResult.errors" :key="err.row">
                <strong>Row {{ err.row }}:</strong>
                <span>{{ err.errors.join('; ') }}</span>
              </li>
            </ul>
          </div>
        </template>
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
        <nav class="pagination" :aria-label="`Pagination, page ${page} of ${totalPages}`">
          <button
            class="btn btn-sm"
            type="button"
            :disabled="page <= 1"
            aria-label="Go to previous page"
            @click="goToPage(page - 1)"
          >Previous</button>
          <template v-for="(item, i) in pageButtons" :key="i">
            <button
              v-if="item !== '...'"
              class="btn btn-sm page-btn"
              type="button"
              :class="{ active: item === page }"
              :aria-label="`Go to page ${item}`"
              :aria-current="item === page ? 'page' : undefined"
              @click="onPageClick(item)"
            >{{ item }}</button>
            <span v-else class="pagination-ellipsis" aria-hidden="true">...</span>
          </template>
          <button
            class="btn btn-sm"
            type="button"
            :disabled="page >= totalPages"
            aria-label="Go to next page"
            @click="goToPage(page + 1)"
          >Next</button>
        </nav>
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

// CSV import / export state
const fileInput = ref(null)
const importing = ref(false)
const exporting = ref(false)
const importResult = ref(null)
const csvError = ref('')

const busy = computed(() => importing.value || exporting.value)

const importMessage = computed(() => {
  const r = importResult.value
  if (!r) return ''
  const parts = []
  if (r.imported > 0) {
    parts.push(`${r.imported} contact${r.imported === 1 ? '' : 's'} imported`)
  }
  if (r.duplicates > 0) {
    parts.push(`${r.duplicates} duplicate${r.duplicates === 1 ? '' : 's'} skipped`)
  }
  if (r.failed > 0) {
    parts.push(`${r.failed} row${r.failed === 1 ? '' : 's'} failed`)
  }
  if (parts.length === 0) return 'The CSV file contained no contact rows.'
  return `Import complete — ${parts.join(', ')}.`
})

const importAlertClass = computed(() => {
  const r = importResult.value
  if (!r) return 'info'
  if (r.failed === 0 && r.duplicates === 0 && r.imported > 0) return 'success'
  if (r.imported === 0 && r.failed > 0) return 'error'
  return 'info'
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const rangeStart = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const rangeEnd = computed(() => Math.min(total.value, page.value * pageSize.value))

// Google-style page window: always keep the first and last page
// reachable, and show a compact window of 2 pages around the
// current page with "..." gaps in between.
const PAGINATION_DELTA = 2
const PAGINATION_EDGE_WINDOW = 3 + 2 * PAGINATION_DELTA // 7 pages

const pageButtons = computed(() => {
  const last = totalPages.value
  const all = Array.from({ length: last }, (_, i) => i + 1)
  if (last <= PAGINATION_DELTA * 2 + 2) {
    // Few enough pages to list every one without ellipsis.
    return all
  }
  const current = page.value
  const left = Math.max(current - PAGINATION_DELTA, 1)
  const right = Math.min(current + PAGINATION_DELTA, last)
  const showLeftDots = left > 3
  const showRightDots = right < last - 2
  if (!showLeftDots && !showRightDots) {
    // Window spans (nearly) the whole range — list every page.
    return all
  }
  if (!showLeftDots) {
    // Near the start: first pages, then a gap, then the last page.
    return [...all.slice(0, PAGINATION_EDGE_WINDOW), '...', last]
  }
  if (!showRightDots) {
    // Near the end: first page, a gap, then the last pages.
    return [1, '...', ...all.slice(last - PAGINATION_EDGE_WINDOW)]
  }
  // In the middle: first page, a gap, the window, a gap, last page.
  return [1, '...', ...all.slice(left - 1, right), '...', last]
})

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
  // Clamp so the page can never go below 1 or beyond the last
  // page, and never reload the page we are already on.
  const target = Math.min(Math.max(1, p), totalPages.value)
  if (target === page.value) return
  page.value = target
  load()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onPageClick(p) {
  // Clicking the current page must not trigger another API request.
  if (p === page.value) return
  goToPage(p)
}

function triggerImport() {
  csvError.value = ''
  importResult.value = null
  fileInput.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  // Clear the selection so the same file can be chosen again.
  event.target.value = ''
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    csvError.value = 'Only .csv files can be imported.'
    return
  }
  importing.value = true
  csvError.value = ''
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.importContacts(formData)
    importResult.value = data
    if (data.imported > 0) {
      // New contacts may not match the current search,
      // so restart from page 1 and refresh the list.
      page.value = 1
      await load()
    }
  } catch (e) {
    csvError.value = extractError(e)
  } finally {
    importing.value = false
  }
}

async function exportCsv() {
  exporting.value = true
  csvError.value = ''
  try {
    const response = await api.exportContacts(search.value)
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download =
      filenameFromResponse(response) ||
      `phonebook-export-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    csvError.value = extractError(e)
  } finally {
    exporting.value = false
  }
}

function filenameFromResponse(response) {
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^";]+)"?/)
  return match ? match[1] : ''
}

function downloadTemplate() {
  const rows = [
    ['name', 'phone_number', 'email', 'address'],
    ['Rahul Sharma', '+919876543210', 'rahul@example.com', 'Pune'],
    ['Amit Patil', '+919876543211', 'amit@example.com', 'Mumbai']
  ]
  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'contacts-template.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
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
