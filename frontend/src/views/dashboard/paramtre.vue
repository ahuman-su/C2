<script setup lang="ts">
import { ref, watch} from 'vue'
import { useRouter } from 'vue-router'; // N'oubliez pas d'importer le router


const modelValue = defineModel() // pour send le shell demandé par le user

const router = useRouter();

type AffichageType = 'listener' | 'list'

const affichage = ref<AffichageType>('listener')

async function listener(e: Event, valeur: AffichageType): Promise<void> {
  e.preventDefault()

  affichage.value = valeur
  if (affichage.value == 'list'){
    fetchShells()
  }
}

const nom = ref('')
const host = ref('')
const port = ref<number | null>(null)
const hostError = ref('')
const portError = ref('')

const validateHost = () => {
  const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/
  const hostnameRegex = /^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])*$/

  if (!host.value) {
    hostError.value = 'Le host est requis'
    return false
  }

  if (!ipRegex.test(host.value) && !hostnameRegex.test(host.value) && host.value !== 'localhost') {
    hostError.value = 'Format de host invalide'
    return false
  }

  hostError.value = ''
  return true
}

const validatePort = () => {
  if (port.value === null) {
    portError.value = 'Le port est requis'
    return false
  }

  return true
}


async function Submit() {
  const token = sessionStorage.getItem('token');
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/dashboard/listener`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        nom: nom.value,
        host: host.value,
        port: port.value,
      })
    })
  }
  catch (error) {
    console.error('Erreur lors de la soumission du formulaire :', error)
  }
}





//
//
//
//
//
//partie pour liste
interface Shell {
  id: number
  nom: string
}


const shells = ref<Shell[]>([])

async function fetchShells() {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/dashboard/shells_list`, {
      headers: {
        Authorization: `Bearer ${sessionStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data: Shell[] = await response.json()
      shells.value = data
    } else {
      console.error("Erreur HTTP :", response.status)
    }
  } catch (error) {
    console.error("Erreur réseau :", error)
  }
}


const selectionnes = ref([])

// Met à jour le modelValue à chaque modification
watch(selectionnes, () => {
  modelValue.value = selectionnes.value.map(shell => shell.nom)
})


//bouton de suppresion de shell
const Submit_delete = async (shell: Shell) => {
  console.log(shell.id)
    const token = sessionStorage.getItem('token');
  try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/dashboard/supprimer_shell`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        id: shell.id
      })
    })
  }
  catch (error) {
    console.error('Erreur lors de la soumission du formulaire de suppresion :', error)
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

    <!-- afficher avec des condition les différentes fenêtres -->
    <div id="test">
      <div v-if="affichage === 'listener'">
        <form @submit.prevent="Submit">
          <div class="form-group">

            <label for="nom">nom</label>
            <input
              id="nom"
              v-model="nom"
              type="text"
              required
              class="form-control"
              placeholder="nom"
            />
          </div>


          <div class="form-group">

            <label for="host">Host</label>
            <input
              id="host"
              v-model="host"
              type="text"
              required
              class="form-control"
              placeholder="localhost ou 127.0.0.1"
              pattern="^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])*$|^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
              @input="validateHost"
            />
            <small v-if="hostError" class="error-message">{{ hostError }}</small>
          </div>

          <div class="form-group">
            <label for="port">Port</label>
            <input
              id="port"
              v-model="port"
              type="number"
              required
              min="0"
              max="65535"
              class="form-control"
              placeholder="3000"
              @input="validatePort"
            />
            <small v-if="portError" class="error-message">{{ portError }}</small>
          </div>

          <button type="submit" class="submit-button">listener</button>
        </form>

      </div>







      <div v-else-if="affichage ==='list'">
        <table v-if="shells.length > 0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nom</th>
            </tr>
          </thead>
          <tbody>
             <tr v-for="shell in shells" :key="shell.id">
              <td>{{ shell.id }}</td>
              <td>{{ shell.nom }}</td>
              <td>
                <input
                  type="checkbox"
                  :value="shell"
                  v-model="selectionnes"
                />
              </td>
               <td>
                <button class="bouton" @click.prevent="Submit_delete(shell)">supprimer</button>
                </td>
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
#paramtre {
  width: 30%;
  height: 500px;
  font-family: monospace;
  padding: 10px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #0f0;
  border-radius: 8px;
}
#les-bouton {
  display: flex;
  width: 100%;
}

.les-bouton-form {
  width: 50%;
}

.bouton {
  width: 100%;
  padding: 10px;
  background-color: rgba(157, 76, 175, 0.38);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  transition: background-color 0.25s;
}

.bouton:hover {
    background-color: #b388ff;
}



</style>