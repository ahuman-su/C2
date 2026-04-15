<script setup lang="ts">
import { computed, ref } from 'vue'

interface LeakResult {
  count: number
  exposed: boolean
  message: string
  severity: 'danger' | 'safe'
}

const API = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:5000'

const password = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<LeakResult | null>(null)

const occurrenceLabel = computed(() => {
  if (!result.value) return ''
  return new Intl.NumberFormat('fr-FR').format(result.value.count)
})

function authHeaders() {
  const token = sessionStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) headers.Authorization = `Bearer ${token}`

  return headers
}

async function checkPassword() {
  error.value = ''
  result.value = null

  if (!password.value) {
    error.value = 'Saisis un mot de passe a verifier.'
    return
  }

  loading.value = true

  try {
    const response = await fetch(`${API}/dashboard/pwned-password`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ password: password.value }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.message || 'Impossible de verifier le mot de passe.')
    }

    result.value = data as LeakResult
    password.value = ''
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Impossible de verifier le mot de passe.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="pwned-panel">
    <div class="panel-header">
      <div>
        <h2>Have I Been Pwned</h2>
        <p>Verifie si un mot de passe apparait dans des fuites publiques connues.</p>
      </div>
    </div>

    <form class="lookup-form" @submit.prevent="checkPassword">
      <label for="pwned-password-input">Mot de passe a verifier</label>

      <div class="input-row">
        <input
          id="pwned-password-input"
          v-model="password"
          type="password"
          autocomplete="new-password"
          placeholder="Saisis le mot de passe..."
        />
        <button type="submit" :disabled="loading">
          {{ loading ? 'verification...' : 'verifier' }}
        </button>
      </div>
    </form>

    <p class="privacy-note">
      La verification passe par l'API HIBP Pwned Passwords. Seul le prefixe du hash SHA-1 est
      envoye au service.
    </p>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <div v-else-if="result" class="result-panel" :class="result.severity">
      <p class="result-kicker">
        {{ result.exposed ? 'Mot de passe compromis' : 'Aucune fuite connue' }}
      </p>
      <p class="result-message">{{ result.message }}</p>
      <p class="result-count">
        {{
          result.exposed
            ? `Occurrences retrouvees: ${occurrenceLabel}`
            : 'Aucune occurrence retournee par HIBP.'
        }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.pwned-panel {
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
  text-align: left;
}

.panel-header h2,
.panel-header p,
.lookup-form label,
.feedback,
.result-kicker,
.result-message,
.result-count,
.privacy-note {
  margin: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.panel-header h2 {
  color: #f1f5ff;
  margin-bottom: 0.35rem;
}

.panel-header p,
.privacy-note {
  color: rgba(178, 255, 178, 0.72);
}

.lookup-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.lookup-form label {
  color: #fff;
  font-weight: 600;
}

.input-row {
  display: flex;
  gap: 0.75rem;
}

.input-row input {
  flex: 1;
  min-width: 0;
  border-radius: 6px;
  border: 1px solid rgba(0, 255, 0, 0.28);
  background: rgba(7, 18, 7, 0.9);
  color: #e8ffe8;
  padding: 0.85rem 1rem;
  font: inherit;
}

.input-row input:focus {
  outline: 2px solid rgba(0, 255, 0, 0.4);
  outline-offset: 2px;
}

.input-row button {
  border: none;
  border-radius: 6px;
  padding: 0.9rem 1.2rem;
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.input-row button:hover:not(:disabled) {
  background: #b388ff;
}

.input-row button:disabled {
  opacity: 0.7;
  cursor: wait;
}

.feedback.error {
  color: #ffb4b4;
  background: rgba(126, 20, 20, 0.28);
  border: 1px solid rgba(255, 107, 107, 0.5);
  border-radius: 8px;
  padding: 0.85rem 1rem;
}

.result-panel {
  border-radius: 8px;
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  border: 1px solid transparent;
}

.result-panel.safe {
  background: rgba(17, 84, 44, 0.28);
  border-color: rgba(95, 226, 132, 0.42);
}

.result-panel.danger {
  background: rgba(126, 20, 20, 0.28);
  border-color: rgba(255, 107, 107, 0.5);
}

.result-kicker {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(210, 225, 255, 0.72);
}

.result-message {
  color: #f1f5ff;
  font-size: 1.05rem;
  font-weight: 600;
}

.result-count {
  color: rgba(210, 225, 255, 0.8);
}

@media (max-width: 720px) {
  .input-row {
    flex-direction: column;
  }

  .input-row button {
    width: 100%;
  }
}
</style>
