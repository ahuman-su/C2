<script setup lang="ts">
import terminale from './dashboard/terminale.vue';
import paramtre from './dashboard/paramtre.vue';

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
  <div id="fenetre">
    <terminale :message_shell="sharedMessage"/>
    <paramtre v-model="sharedMessage"/>
  </div>
</template>

<style scoped>
#fenetre {
  display: flex;
  flex-direction: row;
  justify-content: space-between; /* Espace les éléments uniformément */
  align-items: flex-start; /* Aligne les éléments en haut */
  gap: 20px; /* Ajoute un espace entre les éléments */
  padding: 20px; /* Ajoute un peu d'espace autour */
}



</style>