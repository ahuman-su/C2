<script setup lang="ts">
import { onMounted, ref } from 'vue'

interface InvitedUser {
  id: number
  nom: string
  prenom: string
  username: string
  email: string
  is_blocked: boolean
  is_expired: boolean
  status: 'active' | 'expired' | 'blocked'
  expiration_date: string | null
  remaining_seconds: number | null
}

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'

const users = ref<InvitedUser[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const updatingId = ref<number | null>(null)

function authHeaders() {
  const token = sessionStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function request(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  })

  let data: any = {}
  try {
    data = await response.json()
  } catch {}

  if (!response.ok) {
    throw new Error(data.message || 'Erreur serveur.')
  }

  return data
}

async function fetchInvitedUsers() {
  loading.value = true
  error.value = ''

  try {
    const data = await request('/dashboard/admin/invited-users', { method: 'GET' })
    users.value = data.users || []
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Impossible de charger les invites.'
  } finally {
    loading.value = false
  }
}

function formatDate(value: string | null) {
  if (!value) return 'Aucune'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('fr-FR')
}

function formatRemaining(seconds: number | null) {
  if (seconds === null) return 'Sans expiration'
  if (seconds <= 0) return 'Expire'

  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days}j ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${Math.max(1, minutes)}m`
}

function statusLabel(status: InvitedUser['status']) {
  if (status === 'blocked') return 'Bloque'
  if (status === 'expired') return 'Expire'
  return 'Actif'
}

function displayName(user: InvitedUser) {
  const fullName = `${user.prenom || ''} ${user.nom || ''}`.trim()
  return fullName || user.username
}

async function toggleBlocked(user: InvitedUser) {
  error.value = ''
  success.value = ''
  updatingId.value = user.id

  try {
    const data = await request(`/dashboard/admin/invited-users/${user.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_blocked: !user.is_blocked }),
    })

    const updatedUser = data.user
    users.value = users.value.map((item) => (item.id === updatedUser.id ? updatedUser : item))
    success.value = updatedUser.is_blocked ? 'Utilisateur bloque.' : 'Utilisateur debloque.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Impossible de modifier le statut.'
  } finally {
    updatingId.value = null
  }
}

async function extendExpiration(user: InvitedUser, hours: number) {
  error.value = ''
  success.value = ''
  updatingId.value = user.id

  try {
    const data = await request(`/dashboard/admin/invited-users/${user.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ add_hours: hours }),
    })

    const updatedUser = data.user
    users.value = users.value.map((item) => (item.id === updatedUser.id ? updatedUser : item))
    success.value = hours === 1 ? 'Expiration prolongee de 1h.' : 'Expiration prolongee de 1j.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible de prolonger l'expiration."
  } finally {
    updatingId.value = null
  }
}

onMounted(fetchInvitedUsers)
</script>

<template>
  <section class="admin-panel">
    <div class="admin-header">
      <div>
        <h2>Administration invites</h2>
        <p>Comptes temporaires, expiration et blocage manuel.</p>
      </div>
      <button type="button" class="refresh-button" @click="fetchInvitedUsers">rafraichir</button>
    </div>

    <p v-if="error" class="feedback error">{{ error }}</p>
    <p v-else-if="success" class="feedback success">{{ success }}</p>

    <div class="table-wrap">
      <p v-if="loading" class="empty-state">Chargement...</p>
      <p v-else-if="users.length === 0 && !error" class="empty-state">Aucun utilisateur invite.</p>

      <table v-else-if="users.length > 0">
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th>Email</th>
            <th>Statut</th>
            <th>Expiration</th>
            <th>Temps restant</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <strong>{{ displayName(user) }}</strong>
              <small>@{{ user.username }}</small>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['status-badge', `status-${user.status}`]">
                {{ statusLabel(user.status) }}
              </span>
            </td>
            <td>{{ formatDate(user.expiration_date) }}</td>
            <td>{{ formatRemaining(user.remaining_seconds) }}</td>
            <td>
              <div class="button-row">
                <button
                  type="button"
                  class="submit-button small-button"
                  :disabled="updatingId === user.id"
                  @click="extendExpiration(user, 1)"
                >
                  +1h
                </button>
                <button
                  type="button"
                  class="submit-button small-button"
                  :disabled="updatingId === user.id"
                  @click="extendExpiration(user, 24)"
                >
                  +1j
                </button>
                <button
                  type="button"
                  :class="user.is_blocked ? 'submit-button' : 'danger-button'"
                  :disabled="updatingId === user.id"
                  @click="toggleBlocked(user)"
                >
                  {{ user.is_blocked ? 'debloquer' : 'bloquer' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.admin-panel {
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

.admin-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.admin-header h2,
.admin-header p,
.empty-state,
.feedback,
td strong,
td small {
  margin: 0;
}

.admin-header p,
.empty-state,
td small {
  color: rgba(178, 255, 178, 0.72);
}

.refresh-button,
.submit-button,
.danger-button {
  border: none;
  border-radius: 6px;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.25s ease;
}

.refresh-button,
.submit-button {
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  padding: 0.75rem 1rem;
}

.refresh-button:hover,
.submit-button:hover {
  background: #b388ff;
}

.danger-button {
  background: rgba(165, 38, 38, 0.45);
  color: #fff;
  padding: 0.75rem 1rem;
}

.danger-button:hover {
  background: rgba(219, 80, 80, 0.85);
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.small-button {
  padding: 0.75rem 0.85rem;
}

.submit-button:disabled,
.danger-button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.feedback {
  padding: 0.85rem 1rem;
  border-radius: 8px;
  border: 1px solid transparent;
}

.feedback.error {
  color: #ffb4b4;
  background: rgba(126, 20, 20, 0.28);
  border-color: rgba(255, 107, 107, 0.5);
}

.feedback.success {
  color: #b8ffcb;
  background: rgba(17, 84, 44, 0.28);
  border-color: rgba(95, 226, 132, 0.42);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 860px;
  border-collapse: collapse;
}

th,
td {
  border-top: 1px solid rgba(0, 255, 0, 0.22);
  padding: 0.85rem;
  text-align: left;
  vertical-align: middle;
}

th {
  color: #f1f5ff;
  font-weight: 700;
}

td {
  color: #d6ffd6;
}

td:first-child {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 5.75rem;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  border: 1px solid rgba(0, 255, 0, 0.35);
}

.status-active {
  color: #b8ffcb;
  background: rgba(17, 84, 44, 0.28);
}

.status-expired {
  color: #ffe2a8;
  background: rgba(123, 84, 18, 0.3);
  border-color: rgba(255, 184, 77, 0.48);
}

.status-blocked {
  color: #ffb4b4;
  background: rgba(126, 20, 20, 0.28);
  border-color: rgba(255, 107, 107, 0.5);
}

@media (max-width: 760px) {
  .admin-header {
    flex-direction: column;
  }
}
</style>
