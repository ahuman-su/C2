<template>
  <div id="header">
    <a class="bouton-header" href="/signin">login</a>
    <a class="bouton-header" href="/signup">signup</a>
    <a class="bouton-header" href="/dashboard">dashboard</a>
  </div>


  <div id="corp">
    <h1>Accueil</h1>
    <p>{{ message }}</p>
    <p>Bienvenue sur un C2 publique</p>

    <img src="../assets/C2R2MAX.png" alt="logo"></img>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'Home',
  data() {
    return {
      message: ''
    }
  },
  mounted() {
    axios.get('http://127.0.0.1:5000/api/test')
      .then(res => {
        this.message = res.data.message
      })
  }
}
</script>

<style scoped>
#header{
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


#corp{
  text-align: center;
}



</style>
