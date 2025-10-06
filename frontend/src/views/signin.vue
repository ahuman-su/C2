<script setup>
import {ref, resolveDirective} from "vue";
import { useRouter } from 'vue-router'; // N'oubliez pas d'importer le router

const router = useRouter();

const formData = ref({
  email: '',
  password: '',
})

// Définir error_login comme une ref
const error_login = ref(false)
const errorMessage = ref('')

const submit = async (e) => {
  e.preventDefault()
  try {

    // Ici vous pouvez traiter les données du formulaire
    console.log('Données du formulaire:', formData.value)

    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      })
    })

    const reponse_login = await response.json()

    if (reponse_login.success && reponse_login.token) {
      sessionStorage.setItem('token', reponse_login.token)
      error_login.value = false
      router.push('/dashboard')
    } else {
      error_login.value = true
      errorMessage.value = "Mauvais email ou mot de passe"
    }

  }catch (error)
    {
      error_login.value = true;
      errorMessage.value = "Erreur lors de la connexion";
    }
};

const submit_signup = async (e) => {
  e.preventDefault()

  resolveDirective('router-link')
  router.push('/signup')

};

</script>

<template>
  <form @submit="submit" class="form">
    <div id="login">
          <label for="email">email :</label>
          <input
            id="email"
            type="text"
            v-model="formData.email"
            required
            class="form-control"
          />

          <label for="password">password :</label>
          <input
            id="password"
             type="password"
            v-model="formData.password"
            required
            class="form-control"
          />


          <button type="submit" class="submit-btn">Envoyer</button>
      </div>

      <div v-if="error_login" class="error-message">
        {{ errorMessage }}
      </div>

  </form>

  <form @submit="submit_signup" class="form">
    <button type="submit" class="submit-btn">crée un compte</button>
  </form>
</template>

<style scoped>

.form {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
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
  margin-top: 10px;
}

.submit-btn:hover {
  background-color: #b388ff;
}

.error-message {
  color: red;
}
</style>