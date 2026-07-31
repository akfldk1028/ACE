import { describe, it, expect } from 'vitest'
import { truncateError } from './utils'

describe('truncateError', () => {
  it('returns short messages unchanged', () => {
    expect(truncateError('short')).toBe('short')
  })

  it('returns exactly 200-char messages unchanged', () => {
    const msg = 'a'.repeat(200)
    expect(truncateError(msg)).toBe(msg)
  })

  it('truncates messages longer than 200 chars with ellipsis', () => {
    const msg = 'a'.repeat(250)
    expect(truncateError(msg)).toBe('a'.repeat(200) + '...')
  })

  it('accepts custom max length', () => {
    expect(truncateError('hello world', 5)).toBe('hello...')
  })

  it('handles empty string', () => {
    expect(truncateError('')).toBe('')
  })
})
