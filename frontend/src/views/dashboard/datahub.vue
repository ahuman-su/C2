<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

type Tab = 'snippets' | 'notes' | 'credentials'
const activeTab = ref<Tab>('snippets')

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'
const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${sessionStorage.getItem('token')}`,
})

interface Snippet {
  id: number
  titre: string
  commande: string
  description?: string | null
  type_shell?: string | null
  tags: string[]
}

interface Note {
  id: number
  titre: string
  contenu: string
  contexte?: string | null
}

interface Credential {
  id: number
  nom: string
  username?: string | null
  secret: string
  type_credential?: string | null
  host?: string | null
  port?: number | null
  note?: string | null
  is_encrypted?: boolean
}

const snippets = ref<Snippet[]>([])
const notes = ref<Note[]>([])
const credentials = ref<Credential[]>([])
const snippetSearch = ref('')
const noteSearch = ref('')
const credentialSearch = ref('')
const credentialError = ref('')

const snippetForm = reactive({
  id: null as number | null,
  titre: '',
  commande: '',
  description: '',
  type_shell: '',
  tags: '',
})

const noteForm = reactive({
  id: null as number | null,
  titre: '',
  contenu: '',
  contexte: '',
})

const credentialForm = reactive({
  id: null as number | null,
  nom: '',
  username: '',
  secret: '',
  type_credential: '',
  host: '',
  port: '' as string | number,
  note: '',
})

const resetSnippetForm = () => {
  snippetForm.id = null
  snippetForm.titre = ''
  snippetForm.commande = ''
  snippetForm.description = ''
  snippetForm.type_shell = ''
  snippetForm.tags = ''
}

const resetNoteForm = () => {
  noteForm.id = null
  noteForm.titre = ''
  noteForm.contenu = ''
  noteForm.contexte = ''
}

const resetCredentialForm = () => {
  credentialForm.id = null
  credentialForm.nom = ''
  credentialForm.username = ''
  credentialForm.secret = ''
  credentialForm.type_credential = ''
  credentialForm.host = ''
  credentialForm.port = ''
  credentialForm.note = ''
}

// Charge les snippets de l'utilisateur (input: token; output: liste de snippets).
const fetchSnippets = async () => {
  const response = await fetch(`${API}/dashboard/snippets`, { headers: authHeaders() })
  if (response.ok) snippets.value = await response.json()
}

// Charge les notes de l'utilisateur (input: token; output: liste de notes).
const fetchNotes = async () => {
  const response = await fetch(`${API}/dashboard/notes`, { headers: authHeaders() })
  if (response.ok) notes.value = await response.json()
}

// Charge les credentials (input: token; output: liste de credentials).
const fetchCredentials = async () => {
  credentialError.value = ''
  const response = await fetch(`${API}/dashboard/credentials`, { headers: authHeaders() })
  if (response.ok) {
    credentials.value = await response.json()
  } else {
    const data = await response.json().catch(() => null)
    credentialError.value = data?.error || 'Erreur lors du chargement des credentials.'
  }
}

// Crée ou met à jour un snippet (input: formulaire; output: refresh liste).
const saveSnippet = async () => {
  if (!snippetForm.titre || !snippetForm.commande) return
  const payload = {
    titre: snippetForm.titre,
    commande: snippetForm.commande,
    description: snippetForm.description || null,
    type_shell: snippetForm.type_shell || null,
    tags: snippetForm.tags ? snippetForm.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
  }
  if (snippetForm.id) {
    await fetch(`${API}/dashboard/snippets/${snippetForm.id}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
  } else {
    await fetch(`${API}/dashboard/snippets`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
  }
  resetSnippetForm()
  await fetchSnippets()
}

// Remplit le formulaire à partir d'un snippet existant (input: snippet; output: form state).
const editSnippet = (snippet: Snippet) => {
  snippetForm.id = snippet.id
  snippetForm.titre = snippet.titre
  snippetForm.commande = snippet.commande
  snippetForm.description = snippet.description || ''
  snippetForm.type_shell = snippet.type_shell || ''
  snippetForm.tags = snippet.tags?.join(', ') || ''
}

// Supprime un snippet (input: snippet id; output: refresh liste).
const deleteSnippet = async (snippet: Snippet) => {
  await fetch(`${API}/dashboard/snippets/${snippet.id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  await fetchSnippets()
  if (snippetForm.id === snippet.id) resetSnippetForm()
}

// Crée ou met à jour une note (input: formulaire; output: refresh liste).
const saveNote = async () => {
  if (!noteForm.titre || !noteForm.contenu) return
  const payload = {
    titre: noteForm.titre,
    contenu: noteForm.contenu,
    contexte: noteForm.contexte || null,
  }
  if (noteForm.id) {
    await fetch(`${API}/dashboard/notes/${noteForm.id}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
  } else {
    await fetch(`${API}/dashboard/notes`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
  }
  resetNoteForm()
  await fetchNotes()
}

// Remplit le formulaire à partir d'une note (input: note; output: form state).
const editNote = (note: Note) => {
  noteForm.id = note.id
  noteForm.titre = note.titre
  noteForm.contenu = note.contenu
  noteForm.contexte = note.contexte || ''
}

// Supprime une note (input: note id; output: refresh liste).
const deleteNote = async (note: Note) => {
  await fetch(`${API}/dashboard/notes/${note.id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  await fetchNotes()
  if (noteForm.id === note.id) resetNoteForm()
}

// Crée ou met à jour un credential (input: formulaire; output: refresh liste).
const saveCredential = async () => {
  if (!credentialForm.nom || !credentialForm.secret) return
  const payload = {
    nom: credentialForm.nom,
    username: credentialForm.username || null,
    secret: credentialForm.secret,
    type_credential: credentialForm.type_credential || null,
    host: credentialForm.host || null,
    port: credentialForm.port ? Number(credentialForm.port) : null,
    note: credentialForm.note || null,
  }
  credentialError.value = ''
  if (credentialForm.id) {
    const response = await fetch(`${API}/dashboard/credentials/${credentialForm.id}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      credentialError.value = data?.error || 'Erreur lors de la mise à jour du credential.'
      return
    }
  } else {
    const response = await fetch(`${API}/dashboard/credentials`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      credentialError.value = data?.error || 'Erreur lors de la création du credential.'
      return
    }
  }
  resetCredentialForm()
  await fetchCredentials()
}

// Remplit le formulaire à partir d'un credential (input: credential; output: form state).
const editCredential = (cred: Credential) => {
  credentialForm.id = cred.id
  credentialForm.nom = cred.nom
  credentialForm.username = cred.username || ''
  credentialForm.secret = cred.secret
  credentialForm.type_credential = cred.type_credential || ''
  credentialForm.host = cred.host || ''
  credentialForm.port = cred.port ?? ''
  credentialForm.note = cred.note || ''
}

// Supprime un credential (input: credential id; output: refresh liste).
const deleteCredential = async (cred: Credential) => {
  await fetch(`${API}/dashboard/credentials/${cred.id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  await fetchCredentials()
  if (credentialForm.id === cred.id) resetCredentialForm()
}

onMounted(async () => {
  await fetchSnippets()
  await fetchNotes()
  await fetchCredentials()
})

const filteredSnippets = computed(() => {
  const q = snippetSearch.value.trim().toLowerCase()
  if (!q) return snippets.value
  return snippets.value.filter(snippet => {
    const tags = snippet.tags?.join(' ') || ''
    return (
      snippet.titre.toLowerCase().includes(q) ||
      snippet.commande.toLowerCase().includes(q) ||
      (snippet.description || '').toLowerCase().includes(q) ||
      (snippet.type_shell || '').toLowerCase().includes(q) ||
      tags.toLowerCase().includes(q)
    )
  })
})

const filteredNotes = computed(() => {
  const q = noteSearch.value.trim().toLowerCase()
  if (!q) return notes.value
  return notes.value.filter(note => {
    return (
      note.titre.toLowerCase().includes(q) ||
      note.contenu.toLowerCase().includes(q) ||
      (note.contexte || '').toLowerCase().includes(q)
    )
  })
})

const filteredCredentials = computed(() => {
  const q = credentialSearch.value.trim().toLowerCase()
  if (!q) return credentials.value
  return credentials.value.filter(cred => {
    return (
      cred.nom.toLowerCase().includes(q) ||
      (cred.username || '').toLowerCase().includes(q) ||
      (cred.type_credential || '').toLowerCase().includes(q) ||
      (cred.host || '').toLowerCase().includes(q) ||
      String(cred.port || '').toLowerCase().includes(q) ||
      (cred.note || '').toLowerCase().includes(q)
    )
  })
})
</script>

<template>
  <div id="datahub">
    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'snippets' }]" @click="activeTab = 'snippets'">
        Snippets
      </button>
      <button :class="['tab', { active: activeTab === 'notes' }]" @click="activeTab = 'notes'">
        Notes
      </button>
      <button :class="['tab', { active: activeTab === 'credentials' }]" @click="activeTab = 'credentials'">
        Credentials
      </button>
    </div>

    <div class="panel" v-if="activeTab === 'snippets'">
      <div class="form">
        <h3>Snippet</h3>
        <input v-model="snippetForm.titre" placeholder="Titre" />
        <textarea v-model="snippetForm.commande" placeholder="Commande"></textarea>
        <textarea v-model="snippetForm.description" placeholder="Description (optionnel)"></textarea>
        <input v-model="snippetForm.type_shell" placeholder="Type shell (optionnel)" />
        <input v-model="snippetForm.tags" placeholder="Tags (séparés par ,)" />
        <div class="actions">
          <button @click="saveSnippet">{{ snippetForm.id ? 'Mettre à jour' : 'Ajouter' }}</button>
          <button class="secondary" @click="resetSnippetForm">Reset</button>
        </div>
      </div>

      <div class="list">
        <h3>Mes snippets</h3>
        <input v-model="snippetSearch" class="search" placeholder="Rechercher un snippet..." />
        <div v-if="filteredSnippets.length === 0" class="empty">Aucun snippet.</div>
        <div v-for="snippet in filteredSnippets" :key="snippet.id" class="item">
          <div class="item-header">
            <strong>{{ snippet.titre }}</strong>
            <div class="item-actions">
              <button class="secondary" @click="editSnippet(snippet)">Éditer</button>
              <button class="danger" @click="deleteSnippet(snippet)">Supprimer</button>
            </div>
          </div>
          <pre class="item-body">{{ snippet.commande }}</pre>
          <div v-if="snippet.description" class="meta">{{ snippet.description }}</div>
          <div class="meta">
            <span v-if="snippet.type_shell">Type: {{ snippet.type_shell }}</span>
            <span v-if="snippet.tags?.length">Tags: {{ snippet.tags.join(', ') }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="panel" v-else-if="activeTab === 'notes'">
      <div class="form">
        <h3>Note</h3>
        <input v-model="noteForm.titre" placeholder="Titre" />
        <textarea v-model="noteForm.contenu" placeholder="Contenu"></textarea>
        <input v-model="noteForm.contexte" placeholder="Contexte (optionnel)" />
        <div class="actions">
          <button @click="saveNote">{{ noteForm.id ? 'Mettre à jour' : 'Ajouter' }}</button>
          <button class="secondary" @click="resetNoteForm">Reset</button>
        </div>
      </div>

      <div class="list">
        <h3>Mes notes</h3>
        <input v-model="noteSearch" class="search" placeholder="Rechercher une note..." />
        <div v-if="filteredNotes.length === 0" class="empty">Aucune note.</div>
        <div v-for="note in filteredNotes" :key="note.id" class="item">
          <div class="item-header">
            <strong>{{ note.titre }}</strong>
            <div class="item-actions">
              <button class="secondary" @click="editNote(note)">Éditer</button>
              <button class="danger" @click="deleteNote(note)">Supprimer</button>
            </div>
          </div>
          <pre class="item-body">{{ note.contenu }}</pre>
          <div v-if="note.contexte" class="meta">Contexte: {{ note.contexte }}</div>
        </div>
      </div>
    </div>

    <div class="panel" v-else>
      <div class="form">
        <h3>Credential</h3>
        <input v-model="credentialForm.nom" placeholder="Nom" />
        <input v-model="credentialForm.username" placeholder="Username (optionnel)" />
        <input v-model="credentialForm.secret" placeholder="Secret" />
        <input v-model="credentialForm.type_credential" placeholder="Type (ssh, api, etc.)" />
        <input v-model="credentialForm.host" placeholder="Host (optionnel)" />
        <input v-model="credentialForm.port" placeholder="Port (optionnel)" />
        <textarea v-model="credentialForm.note" placeholder="Note (optionnel)"></textarea>
        <div class="actions">
          <button @click="saveCredential">{{ credentialForm.id ? 'Mettre à jour' : 'Ajouter' }}</button>
          <button class="secondary" @click="resetCredentialForm">Reset</button>
        </div>
      </div>

      <div class="list">
        <h3>Mes credentials</h3>
        <input v-model="credentialSearch" class="search" placeholder="Rechercher un credential..." />
        <div v-if="credentialError" class="error">{{ credentialError }}</div>
        <div v-if="filteredCredentials.length === 0" class="empty">Aucun credential.</div>
        <div v-for="cred in filteredCredentials" :key="cred.id" class="item">
          <div class="item-header">
            <strong>{{ cred.nom }}</strong>
            <div class="item-actions">
              <button class="secondary" @click="editCredential(cred)">Éditer</button>
              <button class="danger" @click="deleteCredential(cred)">Supprimer</button>
            </div>
          </div>
          <div class="meta">User: {{ cred.username || '—' }}</div>
          <div class="meta">Secret: {{ cred.secret }}</div>
          <div class="meta">
            <span v-if="cred.type_credential">Type: {{ cred.type_credential }}</span>
            <span v-if="cred.host">Host: {{ cred.host }}</span>
            <span v-if="cred.port">Port: {{ cred.port }}</span>
          </div>
          <div v-if="cred.note" class="meta">Note: {{ cred.note }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#datahub {
  margin-top: 20px;
  width: 100%;
  border: 1px solid #0f0;
  border-radius: 8px;
  padding: 16px;
  box-sizing: border-box;
  font-family: monospace;
  background: #060606;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab {
  flex: 1;
  background: rgba(157, 76, 175, 0.28);
  color: white;
  border: none;
}

.tab.active {
  background: #b388ff;
  color: #101010;
}

.panel {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 16px;
}

.form,
.list {
  border: 1px solid rgba(15, 255, 15, 0.3);
  border-radius: 8px;
  padding: 12px;
  background: #0c0c0c;
}

.form input,
.form textarea {
  width: 100%;
  margin-bottom: 8px;
  padding: 8px;
  background: #111;
  color: #0f0;
  border: 1px solid rgba(15, 255, 15, 0.3);
  border-radius: 6px;
  font-family: monospace;
  box-sizing: border-box;
}

.search {
  width: 100%;
  margin-bottom: 10px;
  padding: 8px;
  background: #0f0f0f;
  color: #d6ffd6;
  border: 1px solid rgba(15, 255, 15, 0.2);
  border-radius: 6px;
  font-family: monospace;
  box-sizing: border-box;
}

.form textarea {
  min-height: 90px;
  resize: vertical;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions button {
  flex: 1;
  background: rgba(157, 76, 175, 0.38);
  color: white;
  border: none;
}

.actions button.secondary {
  background: #1c1c1c;
}

.list .item {
  border: 1px solid rgba(15, 255, 15, 0.2);
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 10px;
  background: #050505;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.item-actions {
  display: flex;
  gap: 6px;
}

.item-actions button {
  padding: 4px 8px;
  font-size: 0.85em;
  background: #1c1c1c;
  color: white;
  border: none;
}

.item-actions button.danger {
  background: #8b1c1c;
}

.item-actions button.secondary {
  background: #333;
}

.item-body {
  white-space: pre-wrap;
  color: #0f0;
  margin: 0 0 6px 0;
}

.meta {
  font-size: 0.85em;
  color: #9cff9c;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.empty {
  color: #bbb;
}

.error {
  color: #ff8a8a;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

@media (max-width: 980px) {
  .panel {
    grid-template-columns: 1fr;
  }
}
</style>
