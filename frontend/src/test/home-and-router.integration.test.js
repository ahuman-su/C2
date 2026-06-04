import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import router from '../router'
import Home from '../views/Home.vue'


describe('router integration', () => {
  it('exposes the main application routes', () => {
    const paths = router.getRoutes().map((route) => route.path)

    expect(paths).toEqual(
      expect.arrayContaining(['/', '/Home', '/about', '/signin', '/signup', '/dashboard']),
    )
    expect(router.resolve('/dashboard').matched).toHaveLength(1)
  })
})


describe('home view integration', () => {
  it('calls the Flask health endpoint and renders its status', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      json: vi.fn().mockResolvedValue({ message: 'route de test' }),
    })

    const wrapper = mount(Home)
    await flushPromises()

    expect(globalThis.fetch).toHaveBeenCalledWith('http://127.0.0.1:5000/api/test')
    expect(wrapper.text()).toContain('backend disponible')
    expect(wrapper.text()).toContain('route de test')
  })
})
