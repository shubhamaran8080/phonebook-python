import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { onUnauthorized } from './api'
import './style.css'

// When the backend rejects a request with 401 (expired/invalid
// token), send the user back to the login screen.
onUnauthorized(() => {
  if (router.currentRoute.value.name !== 'login') {
    router.push({ name: 'login' })
  }
})

createApp(App).use(router).mount('#app')
