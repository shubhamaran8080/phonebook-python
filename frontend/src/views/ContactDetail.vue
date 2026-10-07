<template>
  <section>
    <router-link to="/">← Back to list</router-link>

    <p v-if="loading">Loading contact...</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <form v-else-if="contact" @submit.prevent="save">
      <h2>Edit Contact</h2>

      <label>
        Name *
        <input v-model.trim="form.name" required maxlength="255" />
      </label>

      <label>
        Phone number * (E.164 format, e.g. +1234567890)
        <input
          v-model.trim="form.phone_number"
          required
          pattern="\+[1-9]\d{1,14}"
          title="Phone number in E.164 format, e.g. +1234567890"
        />
      </label>

      <label>
        Email
        <input v-model.trim="form.email" type="email" />
      </label>

      <label>
        Address
        <textarea v-model.trim="form.address"></textarea>
      </label>

      <p v-if="serverError" class="error">{{ serverError }}</p>

      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button type="button" @click="reset">Reset</button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import api, { extractError } from '../api'

const route = useRoute()
const contact = ref(null)
const loading = ref(true)
const error = ref('')
const serverError = ref('')
const saving = ref(false)

const form = reactive({
  name: '',
  phone_number: '',
  email: '',
  address: ''
})

function reset() {
  form.name = contact.value.name
  form.phone_number = contact.value.phone_number
  form.email = contact.value.email || ''
  form.address = contact.value.address || ''
  serverError.value = ''
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
  saving.value = true
  serverError.value = ''
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
