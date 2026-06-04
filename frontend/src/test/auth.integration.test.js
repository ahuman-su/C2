import { beforeEach, describe, expect, it, vi } from 'vitest'

import { checkTokenValidity } from '../utils/auth'


function jsonResponse(status, payload) {
  return {
    status,
    json: vi.fn().mockResolvedValue(payload),
  }
}


describe('checkTokenValidity integration', () => {
  beforeEach(() => {
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('returns false without calling the API when no token is stored', async () => {
    const fetchMock = vi.fn()
    globalThis.fetch = fetchMock

    await expect(checkTokenValidity()).resolves.toBe(false)

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('keeps the token when the backend validates it', async () => {
    sessionStorage.setItem('token', 'valid-token')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { valid: true }))
    globalThis.fetch = fetchMock

    await expect(checkTokenValidity()).resolves.toBe(true)

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:5000/api/check-token',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer valid-token' },
      }),
    )
    expect(sessionStorage.getItem('token')).toBe('valid-token')
  })

  it('removes the token when the backend rejects it', async () => {
    sessionStorage.setItem('token', 'expired-token')
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(403, { valid: false }))

    await expect(checkTokenValidity()).resolves.toBe(false)

    expect(sessionStorage.getItem('token')).toBeNull()
  })
})
