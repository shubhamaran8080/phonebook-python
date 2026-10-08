<template>
  <div class="page">
    <header class="page-header">
      <div>
        <router-link to="/contacts" class="link" style="font-weight: 500">← Back to contacts</router-link>
        <h1 style="margin-top: 8px">Contact Details</h1>
      </div>
    </header>

    <div v-if="loading" class="card"><div class="skeleton skeleton-row" style="height: 120px"></div></div>

    <div v-else-if="error" class="alert error">{{ error }}</div>

    <template v-else-if="contact">
      <div class="card" style="margin-bottom: 20px">
        <div class="profile-header">
          <span class="avatar large">{{ initials(contact.name) }}</span>
          <div>
            <h2>{{ contact.name }}</h2>
            <p class="subtitle">{{ contact.phone_number }}</p>
          </div>
        </div>
      </div>

      <div class="card form-card">
        <div class="card-header">
          <h2>Edit Contact</h2>
        </div>
        <form class="form-grid" @submit.prevent="save" novalidate>
          <div class="field">
            <span>Name *</span>
            <input v-model.trim="form.name" class="input" :class="{ invalid: errors.name }" maxlength="255" />
            <span class="field-error" v-if="errors.name">{{ errors.name }}</span>
          </div>

          <div class="field">
            <span>Phone number * <span class="hint">(E.164 format, e.g. +1234567890)</span></span>
            <input
              v-model.trim="form.phone_number"
              class="input"
              :class="{ invalid: errors.phone_number }"
              :pattern="PHONE_PATTERN"
              title="Phone number in E.164 format, e.g. +1234567890"
            />
            <span class="field-error" v-if="errors.phone_number">{{ errors.phone_number }}</span>
          </div>

          <div class="field">
            <span>Email <span class="hint">(optional)</span></span>
            <input v-model.trim="form.email" type="email" class="input" :class="{ invalid: errors.email }" />
            <span class="field-error" v-if="errors.email">{{ errors.email }}</span>
          </div>

          <div class="field">
            <span>Address <span class="hint">(optional)</span></span>
            <textarea v-model.trim="form.address" class="input"></textarea>
          </div>

          <div class="alert error" v-if="serverError">{{ serverError }}</div>

          <div style="display: flex; gap: 10px">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span class="spinner small" v-if="saving"></span>
              {{ saving ? 'Saving...' : 'Save changes' }}
            </button>
            <button type="button" class="btn" @click="reset" :disabled="saving">Reset</button>
          </div>
        </form>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import api, { extractError } from '../api'

const route = useRoute()
const PHONE_PATTERN = '^\\+[1-9]\\d{1,14}$'

const contact = ref(null)
const loading = ref(true)
const error = ref('')
const serverError = ref('')
const saving = ref(false)

const form = reactive({ name: '', phone_number: '', email: '', address: '' })
const errors = reactive({ name: '', phone_number: '', email: '' })

function initials(name) {
  return (name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

function reset() {
  form.name = contact.value.name
  form.phone_number = contact.value.phone_number
  form.email = contact.value.email || ''
  form.address = contact.value.address || ''
  serverError.value = ''
  Object.keys(errors).forEach((k) => (errors[k] = ''))
}

function validate() {
  errors.name = form.name ? '' : 'Name is required'
  errors.phone_number = form.phone_number
    ? new RegExp(PHONE_PATTERN).test(form.phone_number)
      ? ''
      : 'Must be in E.164 format, e.g. +1234567890'
    : 'Phone number is required'
  errors.email = form.email
    ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
      ? ''
      : 'Must be a valid email address'
    : ''
  return !errors.name && !errors.phone_number && !errors.email
}

// Empty optional fields are sent as null so they are cleared in the DB.
function payload() {
  return {
    name: form.name,
    phone_number: form.phone_number,
    email: form.email || null,
    address: form.address || null
  }
}

async function save() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    const { data } = await api.updateContact(route.params.id, payload())
    contact.value = data
    reset()
  } catch (e) {
    serverError.value = extractError(e)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.getContact(route.params.id)
    contact.value = data
    reset()
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
})
</script>
