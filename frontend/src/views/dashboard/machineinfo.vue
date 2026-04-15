<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

interface MachineInfo {
  shell_id: number
  shell_name: string
  type_shell: string
  id_output: string | null
  groups_output: string | null
  users_output: string | null
  uname_output: string | null
  created_at: string | null
  updated_at: string | null
}

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'

const machines = ref<MachineInfo[]>([])
const loading = ref(true)
const error = ref('')

function authHeaders() {
  const token = sessionStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

function formatDate(value: string | null) {
  if (!value) return 'Jamais'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('fr-FR')
}

async function fetchMachineInfo() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`${API}/dashboard/machine_info`, {
      method: 'GET',
      headers: authHeaders(),
    })
    if (!response.ok) throw new Error('Impossible de charger les informations machine.')
    machines.value = await response.json()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Impossible de charger les informations machine.'
  } finally {
    loading.value = false
  }
}

function handleRefreshEvent() {
  fetchMachineInfo()
}

onMounted(() => {
  fetchMachineInfo()
  window.addEventListener('machine-info-updated', handleRefreshEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('machine-info-updated', handleRefreshEvent)
})
</script>

<template>
  <section class="machine-panel">
    <div class="machine-header">
      <div>
        <h2>Infos machine</h2>
        <p>Lance `system_probe` dans le terminal pour collecter et mettre a jour les donnees de chaque shell.</p>
      </div>
      <button type="button" class="refresh-button" @click="fetchMachineInfo">rafraichir</button>
    </div>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <div class="machine-grid">
      <p v-if="loading" class="empty-state">Chargement...</p>
      <p v-else-if="machines.length === 0" class="empty-state">Aucune machine enregistree.</p>

      <article v-for="machine in machines" :key="machine.shell_id" class="machine-card">
        <div class="machine-card-head">
          <div>
            <h3>{{ machine.shell_name }}</h3>
            <small>{{ machine.type_shell }} | mise a jour: {{ formatDate(machine.updated_at) }}</small>
          </div>
        </div>

        <div v-if="machine.id_output" class="machine-content">
          <div class="info-block">
            <span class="label">id</span>
            <pre>{{ machine.id_output }}</pre>
          </div>
          <div class="info-block">
            <span class="label">groups</span>
            <pre>{{ machine.groups_output }}</pre>
          </div>
          <div class="info-block">
            <span class="label">users</span>
            <pre>{{ machine.users_output }}</pre>
          </div>
          <div class="info-block">
            <span class="label">uname -a</span>
            <pre>{{ machine.uname_output }}</pre>
          </div>
        </div>

        <p v-else class="empty-state">Aucune collecte pour cette machine. Execute `system_probe`.</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.machine-panel {
  background: #000;
  color: #0f0;
  border: 1px solid #0f0;
  border-radius: 8px;
  padding: 1rem;
  box-sizing: border-box;
  font-family: monospace;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.machine-header,
.machine-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.machine-header h2,
.machine-header p,
.machine-card h3,
.machine-card small,
.empty-state,
.feedback,
.label,
.info-block pre {
  margin: 0;
}

.machine-header p,
.machine-card small,
.empty-state {
  color: rgba(178, 255, 178, 0.72);
}

.refresh-button {
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  font-family: inherit;
}

.refresh-button:hover {
  background: #b388ff;
}

.feedback.error {
  color: #ffb4b4;
}

.machine-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.machine-card {
  border: 1px solid rgba(0, 255, 0, 0.28);
  border-radius: 8px;
  background: rgba(7, 18, 7, 0.9);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.machine-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-block {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  color: #fff;
  font-weight: 700;
}

.info-block pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
