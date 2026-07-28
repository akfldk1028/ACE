import type {
  ExecutedMassRecord,
  MassExecutionPassport,
} from '../../lib/language-system-types';

interface SelectedRuntimePassportBinding {
  passport: MassExecutionPassport | null;
  error: string;
}

export function bindSelectedRuntimePassport(
  passport: MassExecutionPassport | null,
  mass: ExecutedMassRecord | null,
): SelectedRuntimePassportBinding {
  if (!passport || !mass) return { passport: null, error: '' };

  const mismatches = [
    passport.program_hash !== mass.program_hash ? 'PROGRAM HASH' : '',
    passport.geometry_hash !== mass.geometry_hash ? 'GEOMETRY HASH' : '',
  ].filter(Boolean);

  if (mismatches.length > 0) {
    return {
      passport: null,
      error: `선택 MASS와 실행 passport의 ${mismatches.join(' / ')}가 일치하지 않아 실행 그래프와 elevation 증거를 결합하지 않았습니다.`,
    };
  }

  return { passport, error: '' };
}
