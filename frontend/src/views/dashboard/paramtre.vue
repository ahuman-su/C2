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

const isPastbin = computed(() => type.value === 'Pastbin')
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
  if (nv === 'Pastbin') {
    port.value = null; portError.value = ''
    forumeIp.value = ''; forumeUser.value = ''; forumePassword.value = ''
    ipError.value = ''; userError.value = ''; passwordError.value = ''
  } else if (nv === 'reverse shell') {
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
        <button class="bouton" type="submit">listener</button>
      </form>
      <form class="les-bouton-form" @submit="(e) => listener(e, 'list')">
        <button class="bouton" type="submit">list</button>
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
              <option value="Pastbin">Pastbin</option>
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

      <div v-else-if="affichage ==='list'">
        <table v-if="shells.length > 0">
          <thead>
            <tr><th>ID</th><th>Nom</th></tr>
          </thead>
          <tbody>
            <tr v-for="shell in shells" :key="shell.id">
              <td>{{ shell.id }}</td>
              <td>{{ shell.nom }}</td>
              <td><input type="checkbox" :value="shell" v-model="selectionnes" /></td>
              <td><button class="bouton" @click.prevent="Submit_delete(shell)">supprimer</button></td>
            </tr>
          </tbody>
        </table>
        <p v-else>Aucun shell disponible.</p>
      </div>

      <div v-else>probleme</div>
    </div>
  </div>
</template>

<style scoped>
#paramtre { width: 30%; height: 500px; font-family: monospace; padding: 10px; box-sizing: border-box; display: flex; flex-direction: column; overflow: hidden; border: 1px solid #0f0; border-radius: 8px; background: #060606; color: #d6ffd6; }
#les-bouton { display: flex; width: 100%; }
.les-bouton-form { width: 50%; }
.bouton { width: 100%; padding: 10px; background-color: rgba(157, 76, 175, 0.38); color: white; border: none; cursor: pointer; font-size: 1em; font-weight: 500; font-family: inherit; transition: background-color 0.25s; }
.bouton:hover { background-color: #b388ff; }

.form-control {
  width: 100%;
  margin-bottom: 8px;
  padding: 8px;
  background: #111;
  color: #d6ffd6;
  border: 1px solid rgba(15, 255, 15, 0.3);
  border-radius: 6px;
  box-sizing: border-box;
  font-family: monospace;
}

.submit-button {
  width: 100%;
  padding: 10px;
  background: rgba(157, 76, 175, 0.38);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.submit-button:hover {
  background-color: #b388ff;
}

.error-message {
  color: #ff8a8a;
  font-size: 0.85em;
}
</style>
