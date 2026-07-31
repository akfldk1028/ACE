import { describe, expect, it } from 'vitest'

import { bindSelectedRuntimePassport } from './selected-runtime-passport'
import type {
  ExecutedMassRecord,
  MassExecutionPassport,
} from '../../lib/language-system-types'

const selectedMass = {
  index: 7,
  variant_id: 'mass-07',
  program_hash: 'program-selected',
  geometry_hash: 'geometry-selected',
} as ExecutedMassRecord

const passport = {
  mass_id: 'mass-07',
  program_hash: 'program-selected',
  geometry_hash: 'geometry-selected',
  activation_graph: {
    nodes: [],
    edges: [],
  },
} as unknown as MassExecutionPassport

describe('bindSelectedRuntimePassport', () => {
  it('rejects a passport from a different program before graph composition', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, program_hash: 'program-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('PROGRAM HASH')
    expect(result.error).toContain('선택 MASS')
  })

  it('rejects a passport from different geometry before graph composition', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, geometry_hash: 'geometry-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('GEOMETRY HASH')
    expect(result.error).toContain('선택 MASS')
  })

  it('binds a passport only when both identities match the selected mass', () => {
    expect(bindSelectedRuntimePassport(passport, selectedMass)).toEqual({
      passport,
      error: '',
    })
  })
})
