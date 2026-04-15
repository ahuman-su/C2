<script setup lang="ts">
import { onMounted, ref } from 'vue'

interface Snippet {
  id: number
  titre: string
  langage: string
  contenu: string
  tags: string[]
  created_at: string
}

interface Note {
  id: number
  titre: string
  contenu: string
  created_at: string
}

interface PasswordEntry {
  id: number
  libelle: string
  identifiant: string
  mot_de_passe: string
  created_at: string
}

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'

const snippets = ref<Snippet[]>([])
const notes = ref<Note[]>([])
const passwords = ref<PasswordEntry[]>([])

const snippetTitle = ref('')
const snippetLanguage = ref('')
const snippetContent = ref('')
const snippetTags = ref('')

const noteTitle = ref('')
const noteContent = ref('')

const passwordLabel = ref('')
const passwordUsername = ref('')
const passwordValue = ref('')

const loading = ref(true)
const error = ref('')
const success = ref('')
const visiblePasswords = ref<Record<number, boolean>>({})

function getHeaders() {
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
      ...getHeaders(),
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    let message = 'Erreur serveur.'
    try {
      const data = await response.json()
      message = data.message || message
    } catch {}
    throw new Error(message)
  }

  return response.json()
}

async function fetchStorage() {
  loading.value = true
  error.value = ''

  try {
    const data = await request('/dashboard/storage', { method: 'GET' })
    snippets.value = data.snippets || []
    notes.value = data.notes || []
    passwords.value = data.passwords || []
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Impossible de charger le stockage.'
  } finally {
    loading.value = false
  }
}

function clearMessages() {
  error.value = ''
  success.value = ''
}

function formatDate(value: string) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('fr-FR')
}

function resetSnippetForm() {
  snippetTitle.value = ''
  snippetLanguage.value = ''
  snippetContent.value = ''
  snippetTags.value = ''
}

function parseTags(value: string) {
  const seen = new Set<string>()
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => {
      if (!tag) return false
      const key = tag.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

function resetNoteForm() {
  noteTitle.value = ''
  noteContent.value = ''
}

function resetPasswordForm() {
  passwordLabel.value = ''
  passwordUsername.value = ''
  passwordValue.value = ''
}

async function createSnippet() {
  clearMessages()

  try {
    await request('/dashboard/snippets', {
      method: 'POST',
      body: JSON.stringify({
        title: snippetTitle.value,
        language: snippetLanguage.value,
        content: snippetContent.value,
        tags: parseTags(snippetTags.value),
      }),
    })
    resetSnippetForm()
    success.value = 'Snippet enregistre.'
    await fetchStorage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible d'enregistrer le snippet."
  }
}

async function createNote() {
  clearMessages()

  try {
    await request('/dashboard/notes', {
      method: 'POST',
      body: JSON.stringify({
        title: noteTitle.value,
        content: noteContent.value,
      }),
    })
    resetNoteForm()
    success.value = 'Note enregistree.'
    await fetchStorage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible d'enregistrer la note."
  }
}

async function createPassword() {
  clearMessages()

  try {
    await request('/dashboard/passwords', {
      method: 'POST',
      body: JSON.stringify({
        label: passwordLabel.value,
        username: passwordUsername.value,
        password: passwordValue.value,
      }),
    })
    resetPasswordForm()
    success.value = 'Mot de passe enregistre.'
    await fetchStorage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible d'enregistrer le mot de passe."
  }
}

async function deleteEntry(type: 'snippets' | 'notes' | 'passwords', id: number) {
  clearMessages()

  try {
    await request(`/dashboard/${type}/${id}`, {
      method: 'DELETE',
    })
    success.value = 'Element supprime.'
    await fetchStorage()
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Impossible de supprimer l'element."
  }
}

function togglePassword(id: number) {
  visiblePasswords.value[id] = !visiblePasswords.value[id]
}

onMounted(fetchStorage)
</script>

<template>
  <section class="storage-panel">
    <div class="storage-header">
      <h2>Stockage rapide</h2>
      <p>Snippets, notes et mots de passe saisis a la main sont conserves dans la base.</p>
    </div>

    <p v-if="error" class="feedback error">{{ error }}</p>
    <p v-else-if="success" class="feedback success">{{ success }}</p>

    <div class="storage-grid">
      <section class="storage-card">
        <div class="card-head">
          <h3>Snippets</h3>
          <span>{{ snippets.length }}</span>
        </div>

        <form class="storage-form" @submit.prevent="createSnippet">
          <input v-model="snippetTitle" type="text" placeholder="Titre du snippet" required />
          <input v-model="snippetLanguage" type="text" placeholder="Langage (optionnel)" />
          <input v-model="snippetTags" type="text" placeholder="Tags separes par des virgules" />
          <textarea v-model="snippetContent" rows="6" placeholder="Code a conserver" required />
          <button type="submit" class="submit-button">Ajouter</button>
        </form>

        <div class="entry-list">
          <p v-if="loading" class="empty-state">Chargement...</p>
          <p v-else-if="snippets.length === 0" class="empty-state">Aucun snippet enregistre.</p>
          <article v-for="snippet in snippets" :key="snippet.id" class="entry-card">
            <div class="entry-head">
              <div>
                <h4>{{ snippet.titre }}</h4>
                <small>{{ snippet.langage || 'Texte brut' }} | {{ formatDate(snippet.created_at) }}</small>
              </div>
              <button type="button" class="danger-button" @click="deleteEntry('snippets', snippet.id)">supprimer</button>
            </div>
            <div v-if="snippet.tags && snippet.tags.length > 0" class="tag-list">
              <span v-for="tag in snippet.tags" :key="`${snippet.id}-${tag}`" class="tag-chip">{{ tag }}</span>
            </div>
            <pre>{{ snippet.contenu }}</pre>
          </article>
        </div>
      </section>

      <section class="storage-card">
        <div class="card-head">
          <h3>Notes</h3>
          <span>{{ notes.length }}</span>
        </div>

        <form class="storage-form" @submit.prevent="createNote">
          <input v-model="noteTitle" type="text" placeholder="Titre de la note" required />
          <textarea v-model="noteContent" rows="6" placeholder="Texte libre" required />
          <button type="submit" class="submit-button">Ajouter</button>
        </form>

        <div class="entry-list">
          <p v-if="loading" class="empty-state">Chargement...</p>
          <p v-else-if="notes.length === 0" class="empty-state">Aucune note enregistree.</p>
          <article v-for="note in notes" :key="note.id" class="entry-card">
            <div class="entry-head">
              <div>
                <h4>{{ note.titre }}</h4>
                <small>{{ formatDate(note.created_at) }}</small>
              </div>
              <button type="button" class="danger-button" @click="deleteEntry('notes', note.id)">supprimer</button>
            </div>
            <p>{{ note.contenu }}</p>
          </article>
        </div>
      </section>

      <section class="storage-card">
        <div class="card-head">
          <h3>Mots de passe</h3>
          <span>{{ passwords.length }}</span>
        </div>

        <form class="storage-form" @submit.prevent="createPassword">
          <input v-model="passwordLabel" type="text" placeholder="Service / libelle" required />
          <input v-model="passwordUsername" type="text" placeholder="Identifiant (optionnel)" />
          <input v-model="passwordValue" type="password" placeholder="Mot de passe" required />
          <button type="submit" class="submit-button">Ajouter</button>
        </form>

        <div class="entry-list">
          <p v-if="loading" class="empty-state">Chargement...</p>
          <p v-else-if="passwords.length === 0" class="empty-state">Aucun mot de passe enregistre.</p>
          <article v-for="entry in passwords" :key="entry.id" class="entry-card">
            <div class="entry-head">
              <div>
                <h4>{{ entry.libelle }}</h4>
                <small>{{ entry.identifiant || 'Sans identifiant' }} | {{ formatDate(entry.created_at) }}</small>
              </div>
              <button type="button" class="danger-button" @click="deleteEntry('passwords', entry.id)">supprimer</button>
            </div>
            <div class="password-row">
              <span class="password-value">{{ visiblePasswords[entry.id] ? entry.mot_de_passe : '************' }}</span>
              <button type="button" class="toggle-button" @click="togglePassword(entry.id)">
                {{ visiblePasswords[entry.id] ? 'masquer' : 'voir' }}
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.storage-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  text-align: left;
}

.storage-header h2,
.storage-header p,
.card-head h3,
.entry-head h4,
.entry-card p,
.entry-card small,
.empty-state,
.feedback,
.password-value {
  margin: 0;
}

.storage-header h2 {
  color: #f1f5ff;
  margin-bottom: 0.35rem;
}

.storage-header p {
  color: rgba(210, 225, 255, 0.72);
}

.feedback {
  padding: 0.85rem 1rem;
  border-radius: 8px;
  font-family: monospace;
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

.storage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 1rem;
}

.storage-card {
  background: #000;
  color: #0f0;
  border: 1px solid #0f0;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 560px;
  box-sizing: border-box;
  font-family: monospace;
}

.card-head,
.entry-head,
.password-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.card-head span {
  min-width: 2rem;
  text-align: center;
  padding: 0.2rem 0.45rem;
  border: 1px solid #0f0;
  border-radius: 999px;
}

.storage-form {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.storage-form input,
.storage-form textarea {
  width: 100%;
  box-sizing: border-box;
  background: rgba(12, 12, 12, 0.95);
  border: 1px solid rgba(0, 255, 0, 0.35);
  border-radius: 6px;
  color: #d3ffd3;
  font-family: inherit;
  padding: 0.75rem;
  resize: vertical;
}

.storage-form input:focus,
.storage-form textarea:focus {
  outline: none;
  border-color: #0f0;
  box-shadow: 0 0 0 2px rgba(0, 255, 0, 0.12);
}

.submit-button,
.danger-button,
.toggle-button {
  border: none;
  border-radius: 6px;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.25s ease;
}

.submit-button {
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  padding: 0.8rem 1rem;
}

.submit-button:hover,
.toggle-button:hover {
  background: #b388ff;
}

.danger-button {
  background: rgba(165, 38, 38, 0.45);
  color: #fff;
  padding: 0.55rem 0.85rem;
}

.danger-button:hover {
  background: rgba(219, 80, 80, 0.85);
}

.toggle-button {
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  padding: 0.45rem 0.75rem;
}

.entry-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 0.2rem;
}

.entry-card {
  border: 1px solid rgba(0, 255, 0, 0.28);
  border-radius: 8px;
  padding: 0.85rem;
  background: rgba(7, 18, 7, 0.9);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.entry-card h4 {
  margin: 0 0 0.25rem;
}

.entry-card small {
  color: rgba(178, 255, 178, 0.72);
}

.entry-card p,
.entry-card pre {
  white-space: pre-wrap;
  word-break: break-word;
  color: #d6ffd6;
}

.entry-card pre {
  margin: 0;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.tag-chip {
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(0, 255, 0, 0.35);
  background: rgba(0, 255, 0, 0.08);
  color: #b9ffb9;
  font-size: 0.85rem;
}

.empty-state {
  color: rgba(178, 255, 178, 0.72);
}

.password-row {
  align-items: center;
}

.password-value {
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .storage-card {
    min-height: auto;
  }
}
</style>
