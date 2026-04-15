<script setup>
import { onMounted, ref } from 'vue'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
const apiMessage = ref('')
const apiStatus = ref('verification...')
const apiAvailable = ref(false)

onMounted(async () => {
  try {
    const response = await fetch(`${API}/api/test`)
    const data = await response.json()
    apiMessage.value = data.message || 'API joignable'
    apiStatus.value = 'backend disponible'
    apiAvailable.value = true
  } catch (error) {
    apiMessage.value = 'Impossible de joindre l API Flask.'
    apiStatus.value = 'backend indisponible'
    apiAvailable.value = false
  }
})
</script>

<template>
  <div class="home-page">
    <header id="header">
      <a class="bouton-header" href="/signin">login</a>
      <a class="bouton-header" href="/signup">signup</a>
      <a class="bouton-header" href="/dashboard">dashboard</a>
    </header>

    <main class="home-main">
      <section class="intro-card">
        <p class="eyebrow">C2 Control Center</p>
        <h1>Interface centralisee pour piloter les shells et suivre les machines.</h1>
        <p class="intro-copy">
          Le projet regroupe l authentification, les listeners, le terminal, la collecte
          <code>system_probe</code>, le stockage rapide et la verification HIBP dans une seule interface.
        </p>
        <p class="api-line" :class="apiAvailable ? 'online' : 'offline'">
          {{ apiStatus }} | {{ apiMessage }}
        </p>
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

.home-page {
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

.home-main {
  width: min(900px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 3rem 0;
}

.intro-card {
  background: #000;
  border: 1px solid #0f0;
  border-radius: 10px;
  padding: 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.eyebrow,
.intro-copy,
.api-line {
  margin: 0;
  color: rgba(178, 255, 178, 0.78);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.82rem;
}

.intro-card h1 {
  margin: 0;
  color: #f1f5ff;
  font-size: clamp(2rem, 4vw, 3.1rem);
  line-height: 1.08;
}

.intro-copy {
  max-width: 58ch;
  margin: 0 auto;
  line-height: 1.55;
}

.intro-copy code {
  color: #fff;
}

.api-line.online {
  color: #8df0a3;
}

.api-line.offline {
  color: #ff9d9d;
}

@media (max-width: 640px) {
  #header {
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 1.25rem;
  }

  .home-main {
    padding: 2rem 0;
  }

  .intro-card {
    padding: 1.35rem;
  }
}
</style>
