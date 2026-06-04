import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'

import Signin from '../views/signin.vue'
import Signup from '../views/signup.vue'


function buildRouter(initialPath = '/') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/dashboard', component: { template: '<div>dashboard</div>' } },
      { path: '/signin', component: { template: '<div>signin</div>' } },
      { path: '/signup', component: { template: '<div>signup</div>' } },
    ],
  })
  router.push(initialPath)
  return router
}


function jsonResponse(payload) {
  return {
    json: vi.fn().mockResolvedValue(payload),
  }
}


describe('auth views integration', () => {
  it('submits signin credentials, stores the JWT and navigates to the dashboard', async () => {
    const router = buildRouter('/signin')
    await router.isReady()
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ success: true, token: 'jwt-signin' }))
    globalThis.fetch = fetchMock

    const wrapper = mount(Signin, {
      global: { plugins: [router] },
    })

    await wrapper.get('#email').setValue('alice@example.test')
    await wrapper.get('#password').setValue('secret123')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:5000/auth/signin',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      email: 'alice@example.test',
      password: 'secret123',
    })
    expect(sessionStorage.getItem('token')).toBe('jwt-signin')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('shows the signin backend error without navigating', async () => {
    const router = buildRouter('/signin')
    await router.isReady()
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(jsonResponse({ success: false, message: 'Compte bloque' }))

    const wrapper = mount(Signin, {
      global: { plugins: [router] },
    })

    await wrapper.get('#email').setValue('blocked@example.test')
    await wrapper.get('#password').setValue('secret123')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Compte bloque')
    expect(sessionStorage.getItem('token')).toBeNull()
    expect(router.currentRoute.value.path).toBe('/signin')
  })

  it('submits signup data, stores the JWT and navigates to signin', async () => {
    const router = buildRouter('/signup')
    await router.isReady()
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ success: true, token: 'jwt-signup' }))
    globalThis.fetch = fetchMock

    const wrapper = mount(Signup, {
      global: { plugins: [router] },
    })

    await wrapper.get('#nom').setValue('Admin')
    await wrapper.get('#prenom').setValue('Alice')
    await wrapper.get('#username').setValue('alice')
    await wrapper.get('#email').setValue('alice@example.test')
    await wrapper.get('#password').setValue('secret123')
    await wrapper.get('#expiration_hours').setValue('2')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:5000/auth/signup',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      nom: 'Admin',
      prenom: 'Alice',
      username: 'alice',
      email: 'alice@example.test',
      password: 'secret123',
      expiration_hours: 2,
    })
    expect(sessionStorage.getItem('token')).toBe('jwt-signup')
    expect(router.currentRoute.value.path).toBe('/signin')
  })
})
