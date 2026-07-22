import { afterEach, describe, expect, it, vi } from 'vitest'

import { executeArchivedMass, executeArchivedMassAndLoad } from '../../../src/design/lib/api-client'


describe('executeArchivedMass', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('posts the selected existing run and MASS index to the one-MASS endpoint', async () => {
    const payload = {
      execution_id: 'mass-fast',
      archive_run_id: 'single-execution:mass-fast',
      status: 'geometry_ready',
      geometry_ready: true,
      full_flow_status: 'in_progress',
      geometry_hash: 'hash',
      timings_ms: { total: 42 },
      preview_url: '/preview/',
      passport_url: '/passport/',
      manifest_url: '/manifest/',
    }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => payload,
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await executeArchivedMass('source-run', 3)

    expect(result.archive_run_id).toBe('single-execution:mass-fast')
    expect(fetchMock).toHaveBeenCalledWith(
      '/design/maas/single-executions/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ source_run_id: 'source-run', source_mass_index: 3 }),
      }),
    )
  })

  it('loads the returned run through the existing archive endpoint', async () => {
    const execution = {
      execution_id: 'mass-fast',
      archive_run_id: 'single-execution:mass-fast',
      status: 'geometry_ready',
      geometry_ready: true,
      full_flow_status: 'in_progress',
      geometry_hash: 'hash',
      timings_ms: { total: 42 },
      preview_url: '/preview/',
      passport_url: '/passport/',
      manifest_url: '/manifest/',
    }
    const archive = { run_id: execution.archive_run_id, selected_run_id: execution.archive_run_id }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => execution })
      .mockResolvedValueOnce({ ok: true, json: async () => archive })
    vi.stubGlobal('fetch', fetchMock)

    const result = await executeArchivedMassAndLoad('source-run', 1)

    expect(result.execution).toEqual(execution)
    expect(result.archive).toEqual(archive)
    expect(fetchMock.mock.calls[1][0]).toContain('run_id=single-execution%3Amass-fast')
  })
})
