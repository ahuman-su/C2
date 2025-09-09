<script setup>
// Importation de ref pour la réactivité
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Création des variables réactives pour le formulaire
const formData = ref({
  nom: '',
  prenom: '',
  username: '',
  email: '',
  password: '',
  ville : '',
})

// Fonction pour gérer la soumission du formulaire

const onSubmit = async (e) => {
  e.preventDefault() //stoper le reloading de la page
  // Ici vous pouvez traiter les données du formulaire
  console.log('Données du formulaire:', formData.value)

  const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      nom: nom.value,
      prenom: prenom.value,
      username: username.value,
      email: email.value,
      password: password.value,
      ville: ville.value,
    })
  })

  const reponse_login = await response.json()

  if (reponse_login.success && reponse_login.token) {
    // Stocker le token (localStorage ou sessionStorage)
    sessionStorage.setItem('token', reponse_login.token)

    // Redirection ou changement d'état
    router.push('/signin')
  } else {
    console.error("Échec de la creation de compte :", reponse_login.message)
  }

}

</script>

<template>
  <form @submit="onSubmit" class="form">
    <div id="nom-prenom">
      <div class="form-group">
        <label for="nom">Nom :</label>
        <input
          id="nom"
          type="text"
          v-model="formData.nom"
          required
          class="form-control"
        />
      </div>

      <div class="form-group">
        <label for="prenom">prenom :</label>
        <input
          id="prenom"
          type="text"
          v-model="formData.prenom"
          required
          class="form-control"
        />
      </div>
    </div>

    <div class="form-group">
      <label for="username">Username:</label>
      <input
        id="username"
        type="text"
        v-model="formData.username"
        required
        class="form-control"
      />
    </div>

    <div class="form-group">
      <label for="email">Email :</label>
      <input 
        id="email"
        type="email" 
        v-model="formData.email"
        required
        class="form-control"
      />
    </div>

        <div class="form-group">
      <label for="password">Password :</label>
      <input
        id="password"
        type="password"
        v-model="formData.password"
        required
        class="form-control"
      />
    </div>

    <div class="form-group">
      <label for="ville">Ville :</label>
      <input
        id="ville"
        type="ville"
        v-model="formData.ville"
        required
        class="form-control"
      />
    </div>

    <button type="submit" class="submit-btn">Envoyer</button>
  </form>
</template>

<style scoped>


.form {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-control {
  width: 100%;
  padding: 8px;
  border: 1px solid #2c2c2c;
  border-radius: 4px;
  margin-top: 4px;
  background-color: #2c2c2c;
  color: white;
}

label {
  display: block;
  margin-bottom: 4px;
}

.submit-btn {
  background-color: rgba(157, 76, 175, 0.38);
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:hover {
  background-color: #b388ff;
}


#nom-prenom {
  display: flex;
  justify-content: space-between;
}
</style>