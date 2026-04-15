<template>
  <div id="terminal">
    <div id="output">
      <div v-for="(entry, index) in history" :key="index" class="entry">
        <div class="command">{{ entry.shell_used }}&gt;&gt; {{ entry.command }}</div>
        <div class="result">
          <!-- on affiche le resultat de toute les execution avec une fonctione car des fois c'est juste une chaine de caractére  -->
          <div
            v-if="typeof entry.result === 'string'"
          >
            <pre>{{ formatResult(entry.result) }}</pre>
          </div>
          <div
            v-else
            v-for="(res, shell) in entry.result"
            :key="shell"
            class="shell-output"
          >
            <strong>{{ shell }}:</strong>
            <pre>{{ formatResult(res) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <form @submit.prevent="onSubmit">
      <div id="input-line">
        <span class="prompt">{{ message_shell }}&gt;</span>
        <input v-model="command" id="command" autocomplete="off" autofocus />
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';

const { message_shell } = defineProps<{ message_shell: string }>();

const command = ref('');
const history = ref<
  Array<{ command: string; result: string | Record<string, string>; shell_used: string }>
>([]);

function formatResult(result: string): string {
  return result.replace(/<br\s*\/?>/gi, '\n');
}

async function send_command(command: string) {
  const token = sessionStorage.getItem('token');
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/dashboard/terminal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        shell: message_shell,
        commande: command,
      }),
    });

    const json = await response.json();
    console.log(json);
    return json.resulat;
  } catch (error) {
    console.error('Erreur lors de l’envoi de la commande :', error);
    return '[ERREUR] Impossible de contacter le serveur';
  }
}

async function onSubmit() {
  const trimmed = command.value.trim();
  if (!trimmed) return;

  const result = await send_command(trimmed);
  if (trimmed.toLowerCase() === 'system_probe') {
    window.dispatchEvent(new Event('machine-info-updated'))
  }

  history.value.push({ command: trimmed, result, shell_used: message_shell });
  command.value = '';

  await nextTick(() => {
    const el = document.getElementById('output');
    if (el) el.scrollTop = el.scrollHeight;
  });
}
</script>

<style scoped>
#terminal {
  width: 100%;
  flex: 1 1 0;
  min-width: 0;
  height: 500px;
  background: #000;
  color: #0f0;
  font-family: monospace;
  padding: 10px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #0f0;
  border-radius: 8px;
}

#output {
  flex-grow: 1;
  overflow-y: auto;
  margin-bottom: 10px;
}

.entry {
  margin-bottom: 10px;
}

.command {
  font-weight: bold;
}

.result {
  margin-left: 10px;
  white-space: pre-wrap;
}

.shell-output {
  margin-top: 5px;
  margin-left: 15px;
}

#input-line {
  display: flex;
  align-items: center;
}

.prompt {
  margin-right: 5px;
}

#command {
  background: none;
  border: none;
  outline: none;
  color: #0f0;
  font-family: monospace;
  font-size: 1em;
  flex-grow: 1;
}

@media (max-width: 980px) {
  #terminal {
    height: 420px;
  }
}
</style>
