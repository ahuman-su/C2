<script setup lang="ts">
import terminale from './dashboard/terminale.vue';
import paramtre from './dashboard/paramtre.vue';
import pwnedPassword from './dashboard/pwnedPassword.vue';
import machineinfo from './dashboard/machineinfo.vue';
import stockage from './dashboard/stockage.vue';

import {onMounted, ref} from 'vue'
import { checkTokenValidity } from '@/utils/auth'
import { useRouter } from 'vue-router'


const sharedMessage = ref('')

const router = useRouter()

function logout() {
  sessionStorage.removeItem('token')
  router.push('/signin')
}

onMounted(async () => {
  const isValid = await checkTokenValidity()
  if (!isValid) {
    router.push('/signin')
  }

})
</script>

<template>
  <div class="dashboard-page">
    <main class="dashboard-main">
      <section id="fenetre">
        <terminale :message_shell="sharedMessage"/>
        <paramtre v-model="sharedMessage"/>
      </section>

      <pwned-password></pwned-password>
      <machineinfo></machineinfo>
      <stockage></stockage>

      <div class="logout-row">
        <button class="bouton-header" type="button" @click="logout">deconnexion</button>
      </div>
    </main>
  </div>
</template>

<style scoped>
:global(body) {
  display: block;
  min-height: 100vh;
  background: #101010;
}

:global(#app) {
  width: 100%;
  max-width: none;
  padding: 0;
  text-align: left;
}

.dashboard-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(179, 136, 255, 0.12), transparent 28%),
    radial-gradient(circle at 14% 78%, rgba(0, 255, 128, 0.12), transparent 34%),
    #101010;
  color: #fff;
  font-family: monospace;
}

.bouton-header {
  color: #646cff;
  font-size: 1.2em;
  border: 1px solid #646cff;
  padding: 0.5em 1em;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.bouton-header:hover {
  background: rgba(100, 108, 255, 0.12);
}

.dashboard-main {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 2rem 0 3rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.logout-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.5rem;
}

#fenetre {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 1rem;
}

@media (max-width: 980px) {
  .dashboard-main {
    padding: 1.5rem 0 2rem;
  }

  #fenetre {
    flex-direction: column;
  }

  .logout-row {
    justify-content: center;
  }
}

</style>
