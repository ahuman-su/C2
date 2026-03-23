<script setup lang="ts">
import terminale from './dashboard/terminale.vue';
import paramtre from './dashboard/paramtre.vue';
import meteo from './dashboard/meteo.vue';
import machineinfo from './dashboard/machineinfo.vue';
import stockage from './dashboard/stockage.vue';

import {onMounted, ref} from 'vue'
import { checkTokenValidity } from '@/utils/auth'
import { useRouter } from 'vue-router'


const sharedMessage = ref('')

const router = useRouter()

onMounted(async () => {
  const isValid = await checkTokenValidity()
  if (!isValid) {
    router.push('/signin')
  }

})
</script>

<template>
  <div id="dashboard-page">
    <div id="fenetre">
      <terminale :message_shell="sharedMessage"/>
      <paramtre v-model="sharedMessage"/>
    </div>
    <meteo></meteo>
    <machineinfo></machineinfo>
    <stockage></stockage>
  </div>
</template>

<style scoped>
#dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  text-align: left;
}

#fenetre {
  display: flex;
  flex-direction: row;
  justify-content: space-between; /* Espace les éléments uniformément */
  align-items: flex-start; /* Aligne les éléments en haut */
  gap: 20px; /* Ajoute un espace entre les éléments */
  padding: 20px; /* Ajoute un peu d'espace autour */
}

@media (max-width: 980px) {
  #fenetre {
    flex-direction: column;
  }
}

</style>
