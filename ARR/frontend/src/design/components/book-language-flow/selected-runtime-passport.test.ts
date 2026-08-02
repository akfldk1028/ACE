import { describe, expect, it } from 'vitest'

import {
  bindSelectedRuntimePassport,
  publishablePortfolioRunId,
} from './selected-runtime-passport'
import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
  MassExecutionPassport,
} from '../../lib/language-system-types'

const stopCertificate = {
  status: 'certified',
  hard_pass: true,
  program_hash: 'program-selected',
  final_geometry_hash: 'final-selected',
  visual_hash: 'visual-selected',
  legal_floor_field_hash: 'legal-field-shared',
  candidate_actual_gfa_stop_hash: 'actual-stop-selected',
  selected_floor_count: 7,
}

const selectedMass = {
  index: 7,
  variant_id: 'mass-07',
  program_hash: 'program-selected',
  geometry_hash: 'geometry-selected',
  visual_hash: 'visual-selected',
  floor_capacity_plan_hash: 'floor-plan-selected',
  final_geometry_hash: 'final-selected',
  legal_floor_field_hash: 'legal-field-shared',
  candidate_actual_gfa_stop_hash: 'actual-stop-selected',
  candidate_actual_gfa_stop_certificate: stopCertificate,
  candidate_floor_count: 7,
} as ExecutedMassRecord

const passport = {
  mass_id: 'mass-07',
  program_hash: 'program-selected',
  geometry_hash: 'geometry-selected',
  visual_hash: 'visual-selected',
  floor_capacity_plan_hash: 'floor-plan-selected',
  final_legal_geometry_hash: 'final-selected',
  legal_floor_field_hash: 'legal-field-shared',
  candidate_actual_gfa_stop_hash: 'actual-stop-selected',
  candidate_actual_gfa_stop_certificate: stopCertificate,
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

  it('rejects a passport from a different floor capacity plan', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, floor_capacity_plan_hash: 'floor-plan-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('FLOOR CAPACITY PLAN HASH')
  })

  it('rejects a passport from a different certified visual mesh', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, visual_hash: 'visual-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('VISUAL HASH')
  })

  it('rejects a passport from a different final legal geometry', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, final_legal_geometry_hash: 'final-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('FINAL GEOMETRY HASH')
  })

  it('rejects a passport from a different shared legal floor field', () => {
    const result = bindSelectedRuntimePassport(
      { ...passport, legal_floor_field_hash: 'legal-field-stale' },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('LEGAL FLOOR FIELD HASH')
  })

  it('rejects a passport with a stale candidate actual GFA stop', () => {
    const result = bindSelectedRuntimePassport(
      {
        ...passport,
        candidate_actual_gfa_stop_hash: 'actual-stop-stale',
      },
      selectedMass,
    )

    expect(result.passport).toBeNull()
    expect(result.error).toContain('ACTUAL GFA STOP HASH')
  })

  it('rejects a selected production record without a floor capacity plan hash', () => {
    const result = bindSelectedRuntimePassport(passport, {
      ...selectedMass,
      floor_capacity_plan_hash: '',
    })

    expect(result.passport).toBeNull()
    expect(result.error).toContain('FLOOR CAPACITY PLAN HASH')
  })

  it('binds a passport only when every certified identity matches the selected mass', () => {
    expect(bindSelectedRuntimePassport(passport, selectedMass)).toEqual({
      passport,
      error: '',
    })
  })
})

describe('publishablePortfolioRunId', () => {
  it('keeps the backend-selected passing 20-card run instead of a stale replay', () => {
    const archive = {
      run_id: 'book-program-portfolios-pnu20',
      selected_run_id: 'book-program-portfolios-pnu20',
      run_status: 'pass',
      numeric_status: 'pass',
      mass_count: 20,
      publishable_20: true,
      publishable_target_count: 20,
      publishable_20_manifest: {
        status: 'pass',
        target_count: 20,
        typed_failure_deficits: [],
        shared_legal_floor_field_hash: 'legal-field-shared',
        shared_legal_floor_field_hash_count: 1,
        candidate_actual_gfa_stop_valid_count: 20,
      },
      runs: [
        {
          run_id: 'book-program-portfolios-pnu20',
          created_at: '2026-07-29T01:00:00Z',
          replayable: true,
        },
        {
          run_id: 'single-execution:stale-replay',
          created_at: '2026-07-29T02:00:00Z',
          replayable: true,
        },
      ],
    } as unknown as ExecutedMassManifest

    expect(publishablePortfolioRunId(archive)).toBe(
      'book-program-portfolios-pnu20',
    )
  })

  it('allows candidate-local plans and N to differ inside one trusted legal field', () => {
    const secondCertificate = {
      ...stopCertificate,
      candidate_actual_gfa_stop_hash: 'actual-stop-second',
      selected_floor_count: 23,
    }
    const secondMass = {
      ...selectedMass,
      floor_capacity_plan_hash: 'floor-plan-second',
      candidate_actual_gfa_stop_hash: 'actual-stop-second',
      candidate_actual_gfa_stop_certificate: secondCertificate,
      candidate_floor_count: 23,
    }
    const secondPassport = {
      ...passport,
      floor_capacity_plan_hash: 'floor-plan-second',
      candidate_actual_gfa_stop_hash: 'actual-stop-second',
      candidate_actual_gfa_stop_certificate: secondCertificate,
    }

    expect(bindSelectedRuntimePassport(passport, selectedMass).passport)
      .toBe(passport)
    expect(bindSelectedRuntimePassport(
      secondPassport,
      secondMass,
    ).passport).toBe(secondPassport)
  })

  it('does not claim a failed or incomplete archive is publishable', () => {
    const archive = {
      run_id: 'diagnostic-three',
      selected_run_id: 'diagnostic-three',
      run_status: 'diagnostic_only',
      numeric_status: 'fail',
      mass_count: 3,
      runs: [],
    } as unknown as ExecutedMassManifest

    expect(publishablePortfolioRunId(archive)).toBe('')
  })

  it('rejects a 20-card archive whose publishable manifest has deficits', () => {
    const archive = {
      run_id: 'twenty-with-deficit',
      selected_run_id: 'twenty-with-deficit',
      run_status: 'pass',
      numeric_status: 'pass',
      mass_count: 20,
      publishable_20: true,
      publishable_target_count: 20,
      publishable_20_manifest: {
        status: 'fail',
        target_count: 20,
        typed_failure_deficits: [{ code: 'gestalt.duplicate' }],
      },
      runs: [],
    } as unknown as ExecutedMassManifest

    expect(publishablePortfolioRunId(archive)).toBe('')
  })
})

describe('legacy passport binding scope', () => {
  it('keeps an old single execution browsable without claiming four-hash certification', () => {
    const legacyPassport = {
      ...passport,
      visual_hash: '',
      floor_capacity_plan_hash: '',
      final_legal_geometry_hash: '',
      legal_floor_field_hash: '',
      candidate_actual_gfa_stop_hash: '',
      candidate_actual_gfa_stop_certificate: undefined,
    }
    const legacyMass = {
      ...selectedMass,
      visual_hash: '',
      floor_capacity_plan_hash: '',
      final_geometry_hash: '',
      legal_floor_field_hash: '',
      candidate_actual_gfa_stop_hash: '',
      candidate_actual_gfa_stop_certificate: undefined,
    }

    expect(bindSelectedRuntimePassport(
      legacyPassport,
      legacyMass,
      { requireCertifiedIdentity: false },
    )).toEqual({ passport: legacyPassport, error: '' })
  })

  it('keeps one-sided optional hashes browsable for legacy diagnostics', () => {
    const legacyPassport = {
      ...passport,
      visual_hash: 'passport-only-visual',
      floor_capacity_plan_hash: 'passport-only-capacity',
      final_legal_geometry_hash: 'passport-only-final',
      legal_floor_field_hash: 'passport-only-legal',
      candidate_actual_gfa_stop_hash: 'passport-only-stop',
      candidate_actual_gfa_stop_certificate: undefined,
    }
    const legacyMass = {
      ...selectedMass,
      visual_hash: '',
      floor_capacity_plan_hash: '',
      final_geometry_hash: '',
      legal_floor_field_hash: '',
      candidate_actual_gfa_stop_hash: '',
      candidate_actual_gfa_stop_certificate: undefined,
    }

    expect(bindSelectedRuntimePassport(
      legacyPassport,
      legacyMass,
      { requireCertifiedIdentity: false },
    )).toEqual({ passport: legacyPassport, error: '' })
  })
})
