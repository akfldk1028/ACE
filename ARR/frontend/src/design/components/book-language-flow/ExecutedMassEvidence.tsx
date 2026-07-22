import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
  MassExecutionPassport,
} from '../../lib/language-system-types';

interface ExecutedMassEvidenceProps {
  archive: ExecutedMassManifest;
  mass: ExecutedMassRecord;
  passport: MassExecutionPassport | null;
  passportError: string;
  onExecute: () => void;
  executionState: 'idle' | 'running' | 'complete' | 'failed';
  executionError: string;
  onVlmReview: () => void;
  vlmReviewState: 'idle' | 'running' | 'complete' | 'failed';
  vlmReviewError: string;
}

function percent(value: number | null): string {
  return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'NOT RECORDED';
}

function referenceCount(passport: MassExecutionPassport | null): number {
  const vlm = passport?.stages.find((stage) => stage.id === 'vlm');
  const inputs = vlm?.evidence.image_inputs;
  if (!inputs || typeof inputs !== 'object' || Array.isArray(inputs)) return 0;
  const references = (inputs as { references?: unknown }).references;
  return Array.isArray(references) ? references.length : 0;
}

function scoreMean(evidence: Record<string, unknown> | undefined): string {
  const scores = evidence?.concept_scores;
  if (!scores || typeof scores !== 'object' || Array.isArray(scores)) return 'NOT RECORDED';
  const values = Object.values(scores).filter((value): value is number => typeof value === 'number');
  if (!values.length) return 'NOT RECORDED';
  return (values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(4);
}

function criticActions(evidence: Record<string, unknown> | undefined): string {
  const actions = evidence?.critic_actions;
  return Array.isArray(actions) && actions.length
    ? actions.map(String).join(' · ')
    : 'NONE RECORDED';
}

function passportDisplayStatus(
  passport: MassExecutionPassport | null,
  mass: ExecutedMassRecord,
): string {
  if (!passport) return 'LOADING';
  const selector = passport.stages.find((stage) => stage.id === 'selector');
  const vlm = passport.stages.find((stage) => stage.id === 'vlm');
  if (
    mass.hard_pass
    && selector?.status === 'passed'
    && vlm?.status === 'not_evaluated'
  ) {
    return 'COMPLETE · VLM NOT EVALUATED';
  }
  return passport.status.replaceAll('_', ' ').toUpperCase();
}

export function ExecutedMassEvidence({
  archive,
  mass,
  passport,
  passportError,
  onExecute,
  executionState,
  executionError,
  onVlmReview,
  vlmReviewState,
  vlmReviewError,
}: ExecutedMassEvidenceProps) {
  const vlmStage = passport?.stages.find((stage) => stage.id === 'vlm');
  const selectorStage = passport?.stages.find((stage) => stage.id === 'selector');
  const vlmProgramFit = vlmStage?.evidence.program_fit_hard_pass;
  const cost = vlmStage?.evidence.cost_observation as {
    max_http_attempts?: number;
    usage?: { total_tokens?: number };
  } | undefined;

  return (
    <aside className="book-evidence executed-mass-evidence">
      <div className="book-evidence__heading">
        <span>ACTUAL EXECUTED MASS · {mass.variant_id}</span>
        <h4>{mass.label}</h4>
        <code>{mass.geometry_hash}</code>
      </div>
      <div className="book-evidence__sources geometry-contract__preview">
        <figure>
          <img src={mass.preview_url} alt={`${mass.label} actual archived run render`} />
          <figcaption>
            <strong>ACTUAL RUN CANDIDATE PNG</strong>
            <span>BOOK raster 0 · {archive.run_id}</span>
          </figcaption>
        </figure>
      </div>
      <div className="executed-mass-evidence__execute">
        <button
          type="button"
          onClick={onExecute}
          disabled={executionState === 'running'}
          aria-label="Execute selected MASS"
        >
          <span>{executionState === 'running' ? 'EXECUTING AST / GATE / PNG' : 'EXECUTE SELECTED MASS'}</span>
          <strong>{executionState === 'complete' ? 'NEW RUN ADDED TO THIS GRAPH' : 'FAST SINGLE-MASS FLOW'}</strong>
        </button>
        {executionError && <p role="alert">{executionError}</p>}
        {archive.selected_run_id.startsWith('single-execution:') && (
          <button
            type="button"
            onClick={onVlmReview}
            disabled={vlmReviewState === 'running'}
            aria-label="Run bounded paid VLM"
          >
            <span>{vlmReviewState === 'running' ? 'REVIEWING GENERATED MASS' : 'RUN BOUNDED PAID VLM'}</span>
            <strong>{vlmReviewState === 'complete' ? 'PASSPORT + GRAPH UPDATED' : '1 MASS · MAX 2 REFERENCES · 0 RETRIES'}</strong>
          </button>
        )}
        {vlmReviewError && <p role="alert">{vlmReviewError}</p>}
      </div>
      <dl className="book-evidence__attributes">
        <div><dt>PNU</dt><dd>{archive.pnu}</dd></div>
        <div><dt>OPERATION</dt><dd>{mass.operation_label}</dd></div>
        <div><dt>BOOK RULE</dt><dd>{mass.book_principle_id}</dd></div>
        <div><dt>BASE VOLUME</dt><dd>{mass.book_scope}</dd></div>
        <div><dt>PROGRAM</dt><dd>{mass.program_label || mass.program_type}</dd></div>
        <div><dt>FAR</dt><dd>{mass.far_pct == null ? 'NOT RECORDED' : `${mass.far_pct.toFixed(3)}%`}</dd></div>
        <div><dt>CAPACITY ALT</dt><dd>{mass.capacity_alternative_id}</dd></div>
        <div><dt>TARGET / ACHIEVED</dt><dd>{percent(mass.capacity_target_utilization)} / {percent(mass.capacity_achieved_utilization)}</dd></div>
        <div><dt>GEOMETRY READY</dt><dd>{mass.geometry_ready === false ? 'FAIL' : 'PASS'}</dd></div>
        <div><dt>FULL HARD GATES</dt><dd>{mass.hard_pass ? 'PASS' : 'PENDING / FAIL'}</dd></div>
        <div><dt>VLM</dt><dd>{vlmStage?.status?.replaceAll('_', ' ').toUpperCase() ?? 'LOADING'}</dd></div>
        <div><dt>VLM PROGRAM FIT</dt><dd>{typeof vlmProgramFit === 'boolean' ? (vlmProgramFit ? 'PASS' : 'FAIL') : 'NOT RECORDED'}</dd></div>
        <div><dt>VLM VISUAL MEAN</dt><dd>{scoreMean(vlmStage?.evidence)}</dd></div>
        <div><dt>VLM INPUTS</dt><dd>{referenceCount(passport)} REFERENCES + GENERATED MASS</dd></div>
        <div><dt>VLM ACTIONS</dt><dd>{criticActions(vlmStage?.evidence)}</dd></div>
        <div><dt>VLM RESPONSE</dt><dd>{String(vlmStage?.evidence.response_id || 'NOT RECORDED')}</dd></div>
        <div><dt>VLM TOKENS</dt><dd>{cost?.usage?.total_tokens?.toLocaleString() ?? 'NOT RECORDED'}</dd></div>
        <div><dt>VLM HTTP CEILING</dt><dd>{cost?.max_http_attempts ?? 'NOT RECORDED'}</dd></div>
        <div><dt>SELECTOR</dt><dd>{selectorStage?.status?.toUpperCase() ?? 'LOADING'}</dd></div>
        <div><dt>PASSPORT</dt><dd>{passport ? passportDisplayStatus(passport, mass) : (passportError || 'LOADING')}</dd></div>
        <div><dt>PROGRAM HASH</dt><dd>{mass.program_hash.slice(0, 18)}</dd></div>
        <div><dt>GEOMETRY HASH</dt><dd>{mass.geometry_hash.slice(0, 18)}</dd></div>
      </dl>
      <div className="geometry-contract__passport geometry-contract__passport--summary">
        <span>SINGLE GRAPH AUTHORITY</span>
        <p>The central graph is the only causal view. Every bright edge is backed by this MASS passport; unevaluated VLM nodes remain inactive.</p>
      </div>
      <div className="geometry-contract__program">
        <span>ARCHIVED EXECUTED GEOMETRY DSL · {mass.node_count} NODES</span>
        <pre>{mass.dsl}</pre>
      </div>
    </aside>
  );
}
