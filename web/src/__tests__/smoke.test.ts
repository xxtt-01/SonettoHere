import { describe, it, expect } from 'vitest'

describe('smoke test', () => {
  it('localStorage mock works', () => {
    localStorage.setItem('test', 'value')
    expect(localStorage.getItem('test')).toBe('value')
    localStorage.removeItem('test')
    expect(localStorage.getItem('test')).toBeNull()
  })

  it('crypto.randomUUID works', () => {
    const id = crypto.randomUUID()
    expect(id).toBeTruthy()
    expect(typeof id).toBe('string')
  })
})
