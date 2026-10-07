<template>
  <section>
    <div class="toolbar">
      <input
        v-model="search"
        type="search"
        placeholder="Search by name or phone number..."
        aria-label="Search contacts"
        @input="onSearch"
      />
      <router-link to="/contacts/new" class="btn btn-primary">+ Add Contact</router-link>
    </div>

    <p v-if="loading">Loading contacts...</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <table v-else-if="contacts.length">
      <thead>
        <tr>
          <th>Name</th>
          <th>Phone</th>
          <th>Email</th>
          <th>Address</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="contact in contacts" :key="contact.id">
          <td data-label="Name">
            <router-link :to="`/contacts/${contact.id}`">{{ contact.name }}</router-link>
          </td>
          <td data-label="Phone">{{ contact.phone_number }}</td>
          <td data-label="Email">{{ contact.email || '—' }}</td>
          <td data-label="Address">{{ contact.address || '—' }}</td>
          <td data-label="Actions">
            <div class="actions">
              <router-link :to="`/contacts/${contact.id}`">Edit</router-link>
              <button @click="remove(contact)">Delete</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>No contacts found.</p>

    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="goToPage(page - 1)">Previous</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="goToPage(page + 1)">Next</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api, { extractError } from '../api'

const contacts = ref([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const search = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.listContacts({
      page: page.value,
      pageSize,
      search: search.value
    })
    contacts.value = response.data
    total.value = Number(response.headers['x-total-count'] || 0)
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

function goToPage(p) {
  page.value = p
  load()
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

onMounted(load)
onUnmounted(() => clearTimeout(searchTimer))
</script>
