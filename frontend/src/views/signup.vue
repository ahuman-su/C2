<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
const router = useRouter()

const formData = ref({
  nom: '',
  prenom: '',
  username: '',
  email: '',
  password: '',
})

const errorMessage = ref('')
const loading = ref(false)

const onSubmit = async (event) => {
  event.preventDefault()
  errorMessage.value = ''
  loading.value = true

  try {
    const response = await fetch(`${API}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData.value),
    })

    const data = await response.json()

    if (data.success && data.token) {
      sessionStorage.setItem('token', data.token)
      router.push('/signin')
      return
    }

    errorMessage.value = "Echec de la creation de compte."
  } catch (error) {
    errorMessage.value = "Erreur lors de la creation du compte."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <header id="header">
      <a class="bouton-header" href="/signin">login</a>
      <a class="bouton-header" href="/signup">signup</a>
      <a class="bouton-header" href="/dashboard">dashboard</a>
    </header>

    <main class="auth-main">
      <section class="auth-card">
        <div class="auth-copy">
          <p class="eyebrow">Inscription</p>
          <h1>Cree ton acces.</h1>
          <p>
            Prepare un compte pour acceder au dashboard, configurer les listeners et exploiter les
            modules de collecte et de stockage.
          </p>
        </div>

        <form @submit="onSubmit" class="auth-form">
          <div class="name-row">
            <div class="field-group">
              <label for="nom">nom</label>
              <input id="nom" type="text" v-model="formData.nom" required class="form-control" />
            </div>

            <div class="field-group">
              <label for="prenom">prenom</label>
              <input
                id="prenom"
                type="text"
                v-model="formData.prenom"
                required
                class="form-control"
              />
            </div>
          </div>

          <label for="username">username</label>
          <input
            id="username"
            type="text"
            v-model="formData.username"
            required
            class="form-control"
          />

          <label for="email">email</label>
          <input id="email" type="email" v-model="formData.email" required class="form-control" />

          <label for="password">password</label>
          <input
            id="password"
            type="password"
            v-model="formData.password"
            required
            class="form-control"
          />

          <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? 'creation...' : 'envoyer' }}
          </button>

          <a class="secondary-link" href="/signin">deja un compte ? login</a>
        </form>
      </section>
    </main>
  </div>
</template>

<style scoped>
:global(body) {
  display: block;
  min-height: 100vh;
  background: #101010;
}

:global(#app) {
  width: 100%;
  max-width: none;
  padding: 0;
  text-align: left;
}

.auth-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(179, 136, 255, 0.12), transparent 28%),
    radial-gradient(circle at 14% 78%, rgba(0, 255, 128, 0.12), transparent 34%),
    #101010;
  color: #fff;
  font-family: monospace;
}

#header {
  display: flex;
  justify-content: space-around;
  background-color: #242424;
  padding: 2rem;
  border-bottom: 1px solid #646cff;
}

.bouton-header {
  color: #646cff;
  text-decoration: none;
  font-size: 1.2em;
  border: 1px solid #646cff;
  padding: 0.5em 1em;
  border-radius: 8px;
}

.bouton-header:hover {
  background: rgba(100, 108, 255, 0.12);
}

.auth-main {
  width: min(960px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 3rem 0;
}

.auth-card {
  background: #000;
  border: 1px solid #0f0;
  border-radius: 10px;
  padding: 2rem;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.95fr);
  gap: 2rem;
}

.auth-copy {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  justify-content: center;
}

.eyebrow,
.auth-copy p {
  margin: 0;
  color: rgba(178, 255, 178, 0.78);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.82rem;
}

.auth-copy h1 {
  margin: 0;
  color: #f1f5ff;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.08;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  border: 1px solid rgba(0, 255, 0, 0.22);
  border-radius: 8px;
  background: rgba(7, 18, 7, 0.9);
}

.name-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.auth-form label {
  color: #fff;
}

.form-control {
  width: 100%;
  padding: 0.8rem 0.9rem;
  border: 1px solid rgba(0, 255, 0, 0.22);
  border-radius: 6px;
  background-color: #111;
  color: white;
  box-sizing: border-box;
}

.submit-btn {
  background-color: rgba(157, 76, 175, 0.38);
  color: white;
  padding: 0.85rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  background-color: #b388ff;
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.secondary-link {
  color: rgba(178, 255, 178, 0.88);
  text-decoration: none;
  margin-top: 0.35rem;
}

.secondary-link:hover {
  color: #fff;
}

.error-message {
  margin: 0;
  color: #ff9d9d;
}

@media (max-width: 760px) {
  #header {
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 1.25rem;
  }

  .auth-main {
    padding: 2rem 0;
  }

  .auth-card,
  .name-row {
    grid-template-columns: 1fr;
  }

  .auth-card {
    padding: 1.35rem;
    gap: 1.25rem;
  }
}
</style>
