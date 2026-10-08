<template>
  <div class="page">
    <header class="page-header">
      <div>
        <router-link to="/contacts" class="link" style="font-weight: 500">← Back to contacts</router-link>
        <h1 style="margin-top: 8px">Add Contact</h1>
        <p class="subtitle">Create a new phonebook entry</p>
      </div>
    </header>

    <div class="card form-card">
      <form class="form-grid" @submit.prevent="submit" novalidate>
        <div class="field">
          <span>Name *</span>
          <input v-model.trim="form.name" class="input" :class="{ invalid: errors.name }" maxlength="255" placeholder="Jane Doe" />
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
            placeholder="+1234567890"
          />
          <span class="field-error" v-if="errors.phone_number">{{ errors.phone_number }}</span>
        </div>

        <div class="field">
          <span>Email <span class="hint">(optional)</span></span>
          <input v-model.trim="form.email" type="email" class="input" :class="{ invalid: errors.email }" placeholder="jane@example.com" />
          <span class="field-error" v-if="errors.email">{{ errors.email }}</span>
        </div>

        <div class="field">
          <span>Address <span class="hint">(optional)</span></span>
          <textarea v-model.trim="form.address" class="input" placeholder="123 Main St, City"></textarea>
        </div>

        <div class="alert error" v-if="serverError">{{ serverError }}</div>

        <div style="display: flex; gap: 10px">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <span class="spinner small" v-if="submitting"></span>
            {{ submitting ? 'Adding...' : 'Add Contact' }}
          </button>
          <router-link to="/contacts" class="btn">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { extractError } from '../api'

const router = useRouter()
const PHONE_PATTERN = '^\\+[1-9]\\d{1,14}$'

const form = reactive({ name: '', phone_number: '', email: '', address: '' })
const errors = reactive({ name: '', phone_number: '', email: '' })
const serverError = ref('')
const submitting = ref(false)

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

// Empty optional fields are sent as null rather than empty strings.
function payload() {
  return {
    name: form.name,
    phone_number: form.phone_number,
    email: form.email || null,
    address: form.address || null
  }
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    const { data } = await api.createContact(payload())
    router.push({ name: 'contact-detail', params: { id: data.id } })
  } catch (e) {
    serverError.value = extractError(e)
  } finally {
    submitting.value = false
  }
}
</script>
