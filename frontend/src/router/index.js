// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import About from '../views/about.vue'
import signin from '../views/signin.vue'
import signup from '../views/signup.vue'
import dashbord from '../views/dashboard.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/about', component: About },
  { path: '/Home', component: Home },
  { path: '/signin', component: signin },
  { path: '/signup', component: signup },
  { path: '/dashboard', component: dashbord },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
