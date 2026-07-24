export interface SelectedMassIdentity {
  executionId: string;
  programHash: string;
  geometryHash: string;
}

export interface ElevationProposalEvidence {
  status: string;
  previewUrl: string;
  sha256: string;
  provider: string;
  model: string;
  strategyId: string;
  primarySystem: string;
}

type UnknownRecord = Record<string, unknown>;

function record(value: unknown): UnknownRecord | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as UnknownRecord
    : null;
}

export function extractElevationProposal(
  passport: unknown,
  selected: SelectedMassIdentity,
): ElevationProposalEvidence | null {
  const passportRecord = record(passport);
  const elevation = record(passportRecord?.elevation_evidence);
  const proposal = record(elevation?.image_proposal);
  const identity = record(proposal?.identity);
  const artifact = record(proposal?.artifact);
  const strategy = record(proposal?.strategy);
  const providerMetadata = record(proposal?.provider_metadata);
  if (!proposal || !identity || !artifact || !strategy) return null;
  if (
    passportRecord?.program_hash !== selected.programHash
    || passportRecord?.geometry_hash !== selected.geometryHash
    || identity.execution_id !== selected.executionId
    || identity.program_hash !== selected.programHash
    || identity.geometry_hash !== selected.geometryHash
  ) {
    return null;
  }
  const previewUrl = typeof artifact.preview_url === 'string'
    ? artifact.preview_url
    : '';
  if (!previewUrl.startsWith('/')) return null;
  return {
    status: typeof proposal.status === 'string' ? proposal.status : 'not_evaluated',
    previewUrl,
    sha256: typeof artifact.sha256 === 'string' ? artifact.sha256 : '',
    provider: typeof proposal.provider === 'string' ? proposal.provider : '',
    model: typeof providerMetadata?.model === 'string' ? providerMetadata.model : '',
    strategyId: typeof strategy.strategy_id === 'string' ? strategy.strategy_id : '',
    primarySystem: typeof strategy.primary_system === 'string'
      ? strategy.primary_system
      : '',
  };
}
