<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <div class="login-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
        </div>
        <h1>Phonebook</h1>
        <p>Sign in to your account</p>
      </div>

      <form class="login-form" @submit.prevent="submit" novalidate>
        <div class="field">
          <span>Email or Username</span>
          <input
            v-model.trim="form.username"
            type="text"
            class="input"
            :class="{ invalid: errors.username }"
            placeholder="you@example.com"
            autocomplete="username"
            :disabled="loading"
          />
          <span class="field-error" v-if="errors.username">{{ errors.username }}</span>
        </div>

        <div class="field">
          <span>Password</span>
          <input
            v-model="form.password"
            type="password"
            class="input"
            :class="{ invalid: errors.password }"
            placeholder="Enter your password"
            autocomplete="current-password"
            :disabled="loading"
          />
          <span class="field-error" v-if="errors.password">{{ errors.password }}</span>
        </div>

        <div class="alert error" v-if="serverError">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="flex-shrink:0; margin-top:2px">
            <circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>
          </svg>
          <span>{{ serverError }}</span>
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          <span class="spinner small" v-if="loading"></span>
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { extractError } from '../api'
import { setAuth } from '../auth'

const route = useRoute()
const router = useRouter()

const form = reactive({ username: '', password: '' })
const errors = reactive({ username: '', password: '' })
const loading = ref(false)
const serverError = ref('')

function validate() {
  errors.username = form.username ? '' : 'Email or username is required'
  errors.password = form.password ? '' : 'Password is required'
  return !errors.username && !errors.password
}

async function submit() {
  serverError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    const { data } = await api.login({
      username: form.username,
      password: form.password
    })
    setAuth(data.access_token, data.user)
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : { name: 'dashboard' }
    router.push(redirect)
  } catch (e) {
    const message = extractError(e)
    serverError.value =
      message === 'Not authenticated'
        ? 'Incorrect email/username or password.'
        : message
  } finally {
    loading.value = false
  }
}
</script>
