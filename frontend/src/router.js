import { createRouter, createWebHistory } from 'vue-router'
import ContactList from './views/ContactList.vue'
import ContactDetail from './views/ContactDetail.vue'
import CreateContact from './views/CreateContact.vue'

const routes = [
  { path: '/', name: 'contacts', component: ContactList },
  { path: '/contacts/new', name: 'create-contact', component: CreateContact },
  {
    path: '/contacts/:id',
    name: 'contact-detail',
    component: ContactDetail,
    props: true
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
