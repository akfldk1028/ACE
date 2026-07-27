import { describe, expect, it } from 'vitest'

import { LatestRunRequest } from '../../../src/design/components/book-language-flow/run-selection-request'

describe('LatestRunRequest', () => {
  it('aborts and invalidates an older run request when a newer selection starts', () => {
    const requests = new LatestRunRequest()

    const first = requests.start()
    const second = requests.start()

    expect(first.aborted).toBe(true)
    expect(requests.isCurrent(first)).toBe(false)
    expect(requests.isCurrent(second)).toBe(true)
  })

  it('clears only the request that still owns the latest selection', () => {
    const requests = new LatestRunRequest()
    const first = requests.start()
    const second = requests.start()

    requests.finish(first)
    expect(requests.isCurrent(second)).toBe(true)

    requests.finish(second)
    expect(requests.isCurrent(second)).toBe(false)
  })
})
