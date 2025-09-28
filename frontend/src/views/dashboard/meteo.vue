<template>
  <div class="meteo-card">
    <h2>Meteo</h2>
    <div v-if="loading" class="status">Chargement...</div>
    <div v-else-if="error" class="status error">{{ error }}</div>
    <div v-else class="meteo-body">
      <p class="meteo-temperature">Utilisateur : {{ meteo.user }}</p>
      <p class="meteo-condition">{{ meteo.message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface MeteoData {
  user: string
  message: string
}

const meteo = ref<MeteoData>({ user: '', message: '' })
const loading = ref(true)
const error = ref('')

const apiClient = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:5000',
})

async function fetchMeteo() {
  try {
    const token = sessionStorage.getItem('token')
    const { data } = await apiClient.get('/dashboard/meteo', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    meteo.value = data
  } catch (e) {
    error.value = 'Impossible de recuperer la meteo.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchMeteo)
</script>

<style scoped>
.meteo-card {
  background: var(--surface-elevated);
  border-radius: 20px;
  border: 1px solid var(--border-subtle);
  padding: 1.5rem;
  box-shadow: 0 16px 32px rgba(5, 10, 22, 0.28);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.meteo-card h2 {
  margin: 0;
}

.status {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.status.error {
  color: #ff8a8a;
}

.meteo-body {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  color: var(--text-secondary);
}

.meteo-temperature {
  font-weight: 600;
  color: var(--text-primary);
}

.meteo-condition {
  margin: 0;
}
</style>
