import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from './auth'
import Dashboard from './views/DashboardView.vue'
import ContactList from './views/ContactList.vue'
import ContactDetail from './views/ContactDetail.vue'
import CreateContact from './views/CreateContact.vue'
import Profile from './views/ProfileView.vue'
import Login from './views/LoginView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard, meta: { requiresAuth: true, title: 'Dashboard' } },
  { path: '/contacts', name: 'contacts', component: ContactList, meta: { requiresAuth: true, title: 'Contacts' } },
  { path: '/contacts/new', name: 'create-contact', component: CreateContact, meta: { requiresAuth: true, title: 'Add Contact' } },
  {
    path: '/contacts/:id',
    name: 'contact-detail',
    component: ContactDetail,
    props: true,
    meta: { requiresAuth: true, title: 'Contact Details' }
  },
  { path: '/profile', name: 'profile', component: Profile, meta: { requiresAuth: true, title: 'Account' } },
  { path: '/login', name: 'login', component: Login, meta: { title: 'Sign in' } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard: protected pages require a stored session.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && isAuthenticated.value) {
    return { name: 'dashboard' }
  }
})

export default router
