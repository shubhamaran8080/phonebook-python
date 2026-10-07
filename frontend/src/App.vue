<template>
  <div class="app">
    <header class="app-header">
      <nav>
        <router-link to="/">Contacts</router-link>
        <router-link to="/contacts/new">Add Contact</router-link>
      </nav>
      <h1>Phonebook</h1>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>
