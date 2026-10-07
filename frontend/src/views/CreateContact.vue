<template>
  <section>
    <router-link to="/">← Back to list</router-link>

    <form @submit.prevent="submit">
      <h2>Add Contact</h2>

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
        <button type="submit" :disabled="submitting">{{ submitting ? 'Saving...' : 'Add Contact' }}</button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { extractError } from '../api'

const router = useRouter()
const serverError = ref('')
const submitting = ref(false)

const form = reactive({
  name: '',
  phone_number: '',
  email: '',
  address: ''
})

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
  submitting.value = true
  serverError.value = ''
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
