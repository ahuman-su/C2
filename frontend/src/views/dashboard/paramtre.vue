<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'

const modelValue = defineModel()

const router = useRouter()

type AffichageType = 'listener' | 'list'
const affichage = ref<AffichageType>('listener')

async function listener(e: Event, valeur: AffichageType) {
  e.preventDefault()
  affichage.value = valeur
  if (affichage.value === 'list') fetchShells()
}

const nom = ref('')
const port = ref<number | null>(null)
const type = ref('')
const portError = ref('')
const typeError = ref('')

const isShell = computed(() => type.value === 'reverse shell')
const isForume = computed(() => type.value === 'forume')

// FORUME
const forumeIp = ref('')
const forumeUser = ref('')
const forumePassword = ref('')
const ipError = ref('')
const userError = ref('')
const passwordError = ref('')

// Validations utiles uniquement
const validateType = () => {
  if (!type.value) { typeError.value = 'Le type est requis'; return false }
  typeError.value = ''; return true
}
const validatePort = () => {
  if (!(isShell.value || isForume.value)) { portError.value = ''; return true }
  if (port.value === null) { portError.value = 'Le port est requis'; return false }
  portError.value = ''; return true
}
const validateIp = () => {
  if (!isForume.value) { ipError.value = ''; return true }
  const ipRegex = /^(?:\d{1,3}\.){3}\d{1,3}$/
  if (!forumeIp.value || !ipRegex.test(forumeIp.value)) { ipError.value = 'IP invalide'; return false }
  ipError.value = ''; return true
}
const validateUser = () => {
  if (!isForume.value) { userError.value = ''; return true }
  if (!forumeUser.value) { userError.value = "L'utilisateur est requis"; return false }
  userError.value = ''; return true
}
const validatePassword = () => {
  if (!isForume.value) { passwordError.value = ''; return true }
  if (!forumePassword.value) { passwordError.value = 'Le mot de passe est requis'; return false }
  passwordError.value = ''; return true
}

// Reset propres au switch
watch(type, (nv) => {
  validateType()
  if (nv === 'reverse shell') {
    forumeIp.value = ''; forumeUser.value = ''; forumePassword.value = ''
    ipError.value = ''; userError.value = ''; passwordError.value = ''
  } else if (nv === 'forume') {
    // rien de spécial
  }
})

async function Submit() {
  const ok =
    (validateType() ? 1 : 0) &
    ((isShell.value || isForume.value) ? +validatePort() : 1) &
    (isForume.value ? +(validateIp() && validateUser() && validatePassword()) : 1)

  if (!ok) return

  const token = sessionStorage.getItem('token')
  const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'

  try {
    await fetch(`${API}/dashboard/listener`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        nom: nom.value,
        type: type.value,
        port: (isShell.value || isForume.value) ? port.value : null,
        host: isForume.value ? forumeIp.value : '',
        user: isForume.value ? forumeUser.value : '',
        password: isForume.value ? forumePassword.value : '',
      })
    })
  } catch (e) {
    console.error('Erreur lors de la soumission du formulaire :', e)
  }
}

// Liste
interface Shell { id: number; nom: string }
const shells = ref<Shell[]>([])

async function fetchShells() {
  const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'
  try {
    const response = await fetch(`${API}/dashboard/shells_list`, {
      headers: {
        Authorization: `Bearer ${sessionStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })
    if (response.ok) shells.value = await response.json()
    else console.error('Erreur HTTP :', response.status)
  } catch (e) {
    console.error('Erreur réseau :', e)
  }
}

const selectionnes = ref<any[]>([])
watch(selectionnes, () => {
  modelValue.value = selectionnes.value.map((s: any) => s.nom)
})

const Submit_delete = async (shell: Shell) => {
  const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5000'
  const token = sessionStorage.getItem('token')
  try {
    await fetch(`${API}/dashboard/supprimer_shell`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ id: shell.id })
    })
  } catch (e) {
    console.error('Erreur lors de la suppression :', e)
  }
}
</script>

<template>
  <div id="paramtre">
    <div id="les-bouton">
      <form class="les-bouton-form" @submit="(e) => listener(e, 'listener')">
        <button class="bouton" :class="{ 'bouton-actif': affichage === 'listener' }" type="submit">
          listener
        </button>
      </form>
      <form class="les-bouton-form" @submit="(e) => listener(e, 'list')">
        <button class="bouton" :class="{ 'bouton-actif': affichage === 'list' }" type="submit">
          liste
        </button>
      </form>
    </div>

    <div id="test">
      <div v-if="affichage === 'listener'">
        <form @submit.prevent="Submit">
          <div class="form-group">
            <label for="nom">nom</label>
            <input id="nom" v-model="nom" type="text" required class="form-control" placeholder="nom" />
          </div>

          <div class="form-group">
            <label>type connexion</label>
            <select v-model="type" @input="validateType" class="form-control" required>
              <option value=""></option>
              <option value="reverse shell">reverse shell</option>
              <option value="forume">forume</option>
            </select>
            <small v-if="typeError" class="error-message">{{ typeError }}</small>
          </div>

          <div class="form-group" v-if="isShell">
            <label for="port">Port</label>
            <input id="port" v-model="port" type="number" min="0" max="65535" class="form-control" placeholder="3000" @input="validatePort" />
            <small v-if="portError" class="error-message">{{ portError }}</small>
          </div>

          <div v-if="isForume">
            <div class="form-group">
              <label for="forume-ip">IP</label>
              <input id="forume-ip" v-model="forumeIp" type="text" class="form-control" placeholder="192.168.1.10" @input="validateIp" />
              <small v-if="ipError" class="error-message">{{ ipError }}</small>
            </div>
            <div class="form-group">
              <label for="forume-port">Port</label>
              <input id="forume-port" v-model="port" type="number" min="0" max="65535" class="form-control" placeholder="3000" @input="validatePort" />
              <small v-if="portError" class="error-message">{{ portError }}</small>
            </div>
            <div class="form-group">
              <label for="forume-user">Utilisateur</label>
              <input id="forume-user" v-model="forumeUser" type="text" class="form-control" placeholder="user" @input="validateUser" />
              <small v-if="userError" class="error-message">{{ userError }}</small>
            </div>
            <div class="form-group">
              <label for="forume-password">Mot de passe</label>
              <input id="forume-password" v-model="forumePassword" type="password" class="form-control" placeholder="mot de passe" @input="validatePassword" />
              <small v-if="passwordError" class="error-message">{{ passwordError }}</small>
            </div>
          </div>

          <button type="submit" class="submit-button">listener</button>
        </form>
      </div>

      <div v-else-if="affichage ==='list'" class="liste-view">
        <table v-if="shells.length > 0">
          <thead>
            <tr><th>ID</th><th>Nom</th><th>Actif</th><th>Action</th></tr>
          </thead>
          <tbody>
            <tr v-for="shell in shells" :key="shell.id">
              <td>{{ shell.id }}</td>
              <td>{{ shell.nom }}</td>
              <td><input type="checkbox" :value="shell" v-model="selectionnes" /></td>
              <td>
                <button class="table-button" @click.prevent="Submit_delete(shell)">supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-state">Aucun shell disponible.</p>
      </div>

      <div v-else class="empty-state">probleme</div>
    </div>
  </div>
</template>

<style scoped>
#paramtre {
  width: 100%;
  max-width: 340px;
  flex: 0 0 340px;
  height: 500px;
  font-family: monospace;
  padding: 10px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #0f0;
  border-radius: 8px;
  background: #000;
  color: #0f0;
}

#les-bouton {
  display: flex;
  width: 100%;
  gap: 0.5rem;
  margin-bottom: 0.9rem;
}

.les-bouton-form {
  width: 50%;
}

.bouton,
.submit-button,
.table-button {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  transition: background-color 0.25s, border-color 0.25s, color 0.25s;
}

.bouton {
  width: 100%;
  padding: 10px;
  background: rgba(157, 76, 175, 0.22);
  color: rgba(230, 230, 255, 0.92);
  border: 1px solid rgba(179, 136, 255, 0.22);
}

.bouton:hover,
.submit-button:hover,
.table-button:hover {
  background-color: #b388ff;
  color: #fff;
}

.bouton-actif {
  background: rgba(157, 76, 175, 0.52);
  border-color: rgba(179, 136, 255, 0.6);
  color: #fff;
}

#test {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 0.15rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.85rem;
}

.form-group label {
  color: #fff;
}

.form-control {
  width: 100%;
  box-sizing: border-box;
  padding: 0.75rem;
  border: 1px solid rgba(0, 255, 0, 0.28);
  border-radius: 6px;
  background: rgba(12, 12, 12, 0.95);
  color: #d3ffd3;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: #0f0;
  box-shadow: 0 0 0 2px rgba(0, 255, 0, 0.12);
}

.submit-button {
  width: 100%;
  padding: 0.8rem 1rem;
  background: rgba(157, 76, 175, 0.38);
  color: #fff;
  margin-top: 0.35rem;
}

.error-message {
  color: #ff9d9d;
}

.liste-view {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(7, 18, 7, 0.9);
  border: 1px solid rgba(0, 255, 0, 0.28);
  border-radius: 8px;
  overflow: hidden;
}

thead {
  background: rgba(157, 76, 175, 0.18);
}

th,
td {
  padding: 0.7rem 0.55rem;
  text-align: left;
  border-bottom: 1px solid rgba(0, 255, 0, 0.14);
  color: #d6ffd6;
}

th {
  color: #fff;
  font-weight: 700;
}

tbody tr:last-child td {
  border-bottom: none;
}

tbody tr:hover {
  background: rgba(0, 255, 0, 0.05);
}

input[type='checkbox'] {
  accent-color: #b388ff;
}

.table-button {
  padding: 0.45rem 0.75rem;
  background: rgba(165, 38, 38, 0.45);
  color: #fff;
}

.table-button:hover {
  background: rgba(219, 80, 80, 0.85);
}

.empty-state {
  margin: 0;
  color: rgba(178, 255, 178, 0.72);
}

@media (max-width: 980px) {
  #paramtre {
    max-width: none;
    flex: 1 1 auto;
    height: auto;
    min-height: 420px;
  }
}
</style>
