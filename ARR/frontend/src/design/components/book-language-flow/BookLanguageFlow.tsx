import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Maximize2, Minimize2, RotateCcw } from 'lucide-react';

import {
  getExecutedMassManifest,
  getExecutedMassPassport,
  getMaasLanguageSystem,
  getMaasOutcomeGraphSlice,
} from '../../lib/api-client';
import type {
  ExecutedMassManifest,
  ExecutedMassRecord,
  MaasLanguageSystemManifest,
  MassExecutionPassport,
  OutcomeGraphSlice,
} from '../../lib/language-system-types';
import { ExecutedMassEvidence } from './ExecutedMassEvidence';
import {
  LanguageNetworkCanvas,
  type NetworkEdge,
  type NetworkNode,
} from './LanguageNetworkCanvas';
import './book-language-flow.css';

interface BookLanguageFlowProps {
  pnu?: string;
  compact?: boolean;
  standalone?: boolean;
}

const EXECUTION_STAGE_ORDER = [
  'base', 'book_scope', 'book_orientation', 'book_family', 'book_cardinality',
  'book_rule', 'book_apply', 'geometry', 'program', 'compiler', 'gate', 'site', 'capacity',
  'law', 'parking', 'program_fit', 'render', 'reference', 'vlm', 'repair', 'selector', 'result',
];

const FULL_GRAPH_STAGE_ORDER = [
  'base_model', 'orientation', 'operation_family', 'cardinality', 'operation',
  'book_extension', 'variation', 'reference_corpus', 'reference_query',
  'execution_reference', 'reference_distill', 'execution_geometry', 'execution_program',
  'execution_compiler', 'execution_gates', 'execution_render',
  'execution_vlm', 'execution_repair', 'execution_selector', 'execution_run', 'executed_mass',
  'memory_geometry', 'memory_render', 'memory_portfolio', 'memory_vlm', 'memory_outcome',
];

type GraphView = 'full' | 'selected' | 'archive';

function executedMassNodeId(mass: ExecutedMassRecord): string {
  return `executed:mass:${mass.run_id}:${mass.index}:${mass.geometry_hash.slice(0, 12)}`;
}

interface BookSemanticPath {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  entryId: string;
  targetId: string;
}

function bookStage(stage: string): string {
  if (stage === 'base_model') return 'book_scope';
  if (stage === 'orientation') return 'book_orientation';
  if (stage === 'operation_family') return 'book_family';
  if (stage === 'cardinality') return 'book_cardinality';
  return 'book_rule';
}

function selectedBookSemanticPath(
  manifest: MaasLanguageSystemManifest | null,
  mass: ExecutedMassRecord | null,
): BookSemanticPath | null {
  if (!manifest || !mass) return null;
  const graph = manifest.exploration_graph;
  const nodesById = new Map(graph.nodes.map((node) => [node.id, node]));
  const scopeId = `book:base-model:${mass.book_scope.replace('/', '-')}`;
  const orientationId = `book:orientation:${mass.book_orientation || 'long_axis'}`;
  const principleId = mass.book_principle_id;
  if (!nodesById.has(scopeId) || !nodesById.has(orientationId) || !nodesById.has(principleId)) return null;
  const usableEdges = graph.edges.filter((edge) => (
    !edge.source.startsWith('book:page:')
    && !edge.source.startsWith('book:document:')
    && (edge.scope === 'execution' || edge.kind === 'participates_in')
  ));

  const findPath = (startId: string, targetId: string) => {
    const queue = [startId];
    const previous = new Map<string, typeof usableEdges[number]>();
    const visited = new Set(queue);
    while (queue.length > 0 && !visited.has(targetId)) {
      const current = queue.shift()!;
      usableEdges.forEach((edge) => {
        if (edge.source !== current || visited.has(edge.target)) return;
        visited.add(edge.target);
        previous.set(edge.target, edge);
        queue.push(edge.target);
      });
    }
    if (!visited.has(targetId)) return [];
    const path: typeof usableEdges = [];
    let cursor = targetId;
    while (cursor !== startId) {
      const edge = previous.get(cursor);
      if (!edge) return [];
      path.unshift(edge);
      cursor = edge.source;
    }
    return path;
  };

  let semanticEdges = findPath(orientationId, principleId);
  if (semanticEdges.length === 0 && principleId.startsWith('book:case:')) {
    const verbs = principleId.split(':').at(-1)?.split('+') ?? [];
    const operativeId = [...verbs]
      .reverse()
      .map((verb) => `book:operative:${verb}`)
      .find((nodeId) => nodesById.has(nodeId));
    if (operativeId) {
      semanticEdges = findPath(orientationId, operativeId);
      semanticEdges.push({
        id: `semantic:${operativeId}:${principleId}`,
        source: operativeId,
        target: principleId,
        kind: 'case_application',
        scope: 'execution',
        authority: 'book',
      });
    }
  }
  if (semanticEdges.length === 0) return null;
  const baseEdge = graph.edges.find((edge) => (
    edge.source === scopeId && edge.target === orientationId && edge.scope === 'execution'
  )) ?? {
    id: `semantic:${scopeId}:${orientationId}`,
    source: scopeId,
    target: orientationId,
    kind: 'orients_base_volume',
    scope: 'execution',
    authority: 'book',
  };
  const pathEdges = [baseEdge, ...semanticEdges];
  const pathNodeIds = new Set([scopeId, orientationId, principleId]);
  pathEdges.forEach((edge) => {
    pathNodeIds.add(edge.source);
    pathNodeIds.add(edge.target);
  });
  const nodes = [...pathNodeIds]
    .map((id) => nodesById.get(id))
    .filter((node): node is NonNullable<typeof node> => Boolean(node))
    .map((node) => ({
      id: node.id,
      kind: `book_semantic_${node.kind}`,
      stage: bookStage(node.stage),
      label: node.label,
      authority: 'book',
      attributes: {
        ...node.attributes,
        source_authority: 'BOOK typed language graph',
        selected_for_mass: true,
      },
    }));
  return {
    nodes,
    edges: pathEdges.map((edge) => ({
      id: `book-path:${edge.id}`,
      source: edge.source,
      target: edge.target,
      kind: edge.kind,
      scope: 'execution',
    })),
    entryId: scopeId,
    targetId: principleId,
  };
}

function fullGraph(
  manifest: MaasLanguageSystemManifest | null,
  archive: ExecutedMassManifest | null,
): { nodes: NetworkNode[]; edges: NetworkEdge[] } {
  if (!manifest) return { nodes: [], edges: [] };
  const graph = manifest.exploration_graph;
  const resultPrincipleIds = new Set(archive?.masses.map((mass) => mass.book_principle_id) ?? []);
  const allowedStages = new Set(FULL_GRAPH_STAGE_ORDER);
  const includedBookNodes = graph.nodes.filter((node) => (
    (node.visible && allowedStages.has(node.stage)) || resultPrincipleIds.has(node.id)
  ));
  const includedIds = new Set(includedBookNodes.map((node) => node.id));
  const nodes: NetworkNode[] = includedBookNodes.map((node) => ({
    id: node.id,
    kind: node.kind,
    stage: allowedStages.has(node.stage) ? node.stage : 'book_extension',
    label: node.label,
    authority: node.authority,
    attributes: {
      ...node.attributes,
      source_authority: 'BOOK typed language graph',
    },
  }));
  const edges: NetworkEdge[] = graph.edges
    .filter((edge) => (
      includedIds.has(edge.source)
      && includedIds.has(edge.target)
      && edge.scope !== 'evidence'
      && edge.scope !== 'detail'
    ))
    .map((edge) => ({
      id: `full:${edge.id}`,
      source: edge.source,
      target: edge.target,
      kind: edge.kind,
      scope: edge.scope,
    }));

  archive?.runs.forEach((run, runIndex) => {
    const runNodeId = `execution:run:${run.run_id}`;
    nodes.push({
      id: runNodeId,
      kind: 'execution_run_archive',
      stage: 'execution_run',
      label: `${String(runIndex + 1).padStart(2, '0')} · ${run.run_id.replace('book-program-portfolios-', '')}`,
      authority: 'observed',
      attributes: {
        ...run,
        chronological_order: runIndex + 1,
        selected_run: run.run_id === archive.selected_run_id,
      },
    });
    const previous = archive.runs[runIndex - 1];
    if (previous) {
      edges.push({
        id: `execution:run-order:${previous.run_id}:${run.run_id}`,
        source: `execution:run:${previous.run_id}`,
        target: runNodeId,
        kind: 'followed_by_execution',
        scope: 'feedback',
      });
    }
  });

  archive?.masses.forEach((mass) => {
    const resultId = executedMassNodeId(mass);
    nodes.push({
      id: resultId,
      kind: 'executed_mass_result',
      stage: 'executed_mass',
      label: `${String(mass.index).padStart(2, '0')} · ${massLabel(mass.label)}`,
      authority: 'observed',
      attributes: {
        preview_url: mass.preview_url,
        variant_id: mass.variant_id,
        run_id: mass.run_id,
        program_hash: mass.program_hash,
        geometry_hash: mass.geometry_hash,
        book_principle_id: mass.book_principle_id,
        base_volume: mass.book_scope,
        orientation: mass.book_orientation || 'long_axis',
        capacity_alternative_id: mass.capacity_alternative_id,
        far_pct: mass.far_pct,
        hard_pass: mass.hard_pass,
        vlm_evaluated: mass.vlm_evaluated,
      },
    });
    if (includedIds.has(mass.book_principle_id)) {
      edges.push({
        id: `full:produced:${mass.index}`,
        source: mass.book_principle_id,
        target: resultId,
        kind: 'produced_executed_mass',
        scope: 'execution',
      });
    }
    edges.push({
      id: `execution:run-produced:${mass.archive_key}`,
      source: `execution:run:${mass.run_id}`,
      target: resultId,
      kind: 'archived_mass_in_run',
      scope: 'execution',
    });
  });
  return { nodes, edges };
}

function runtimeStage(column: string): string {
  if (column === 'base' || column === 'book' || column === 'geometry') return 'execution_geometry';
  if (column === 'program') return 'execution_program';
  if (column === 'compiler') return 'execution_compiler';
  if (['gate', 'site', 'capacity', 'law', 'parking', 'program_fit'].includes(column)) return 'execution_gates';
  if (column === 'render') return 'execution_render';
  if (column === 'reference') return 'execution_reference';
  if (column === 'vlm') return 'execution_vlm';
  if (column === 'repair') return 'execution_repair';
  if (column === 'selector') return 'execution_selector';
  return 'execution_geometry';
}

function selectedRuntimeGraph(
  passport: MassExecutionPassport | null,
  mass: ExecutedMassRecord | null,
): { nodes: NetworkNode[]; edges: NetworkEdge[]; edgeIds: string[]; entryId: string } {
  if (!passport || !mass) return { nodes: [], edges: [], edgeIds: [], entryId: '' };
  const mappedId = (nodeId: string) => (
    nodeId === 'result:mass' ? executedMassNodeId(mass) : `runtime:${mass.index}:${nodeId}`
  );
  const nodes = passport.activation_graph.nodes
    .filter((node) => node.id !== 'result:mass')
    .map((node): NetworkNode => {
      const imageBacked = node.kind === 'mass_render_result' || node.kind === 'vlm_reference_image';
      return {
        id: mappedId(node.id),
        kind: node.kind,
        stage: runtimeStage(node.column),
        label: node.label,
        authority: 'observed',
        attributes: {
          ...node.evidence,
          source_node_id: node.id,
          status: node.status,
          activation: node.activation,
          preview_url: imageBacked
            ? (evidenceImageUrl(node.evidence) || mass.preview_url)
            : undefined,
          vlm_input_truth: node.kind === 'vlm_reference_image'
            ? 'image actually submitted to recorded VLM call'
            : undefined,
        },
      };
    });
  const edges = passport.activation_graph.edges.map((edge): NetworkEdge => ({
    id: `runtime:${mass.index}:${edge.id}`,
    source: mappedId(edge.source),
    target: mappedId(edge.target),
    kind: edge.relation,
    scope: edge.activation > 0 ? 'execution' : 'pending',
  }));
  const retrieval = passport.reference_retrieval;
  const corpusNodeId = `runtime:${mass.index}:reference-corpus`;
  const queryNodeId = `runtime:${mass.index}:reference-query`;
  const distillerNodeId = `runtime:${mass.index}:reference-distiller`;
  if (retrieval) {
    nodes.push(
      {
        id: corpusNodeId,
        kind: 'reference_corpus',
        stage: 'reference_corpus',
        label: `ArchDaily · ${retrieval.image_count} images`,
        authority: 'observed',
        attributes: retrieval,
      },
      {
        id: queryNodeId,
        kind: 'program_reference_query',
        stage: 'reference_query',
        label: `${retrieval.program_id} · ${retrieval.geometry_family}`,
        authority: 'observed',
        attributes: {
          ...retrieval,
          selected_mass: mass.variant_id,
        },
      },
      {
        id: distillerNodeId,
        kind: 'reference_vlm_distiller',
        stage: 'reference_distill',
        label: 'Reference VLM · relation distiller',
        authority: 'experimental',
        attributes: {
          status: 'not_evaluated_for_this_mass',
          geometry_authority: false,
          output_contract: 'typed relations and operators, never mesh coordinates',
        },
      },
    );
    edges.push({
      id: `runtime:${mass.index}:corpus-query`,
      source: corpusNodeId,
      target: queryNodeId,
      kind: 'queries_by_program_and_geometry',
      scope: 'execution',
    });
  }
  const activeReferenceSourceIds = new Set(
    passport.activation_graph.nodes
      .filter((node) => node.kind === 'vlm_reference_image')
      .map((node) => String(node.evidence.source_id || '')),
  );
  (passport.retrieved_references ?? []).forEach((reference) => {
    if (activeReferenceSourceIds.has(reference.source_id)) return;
    const nodeId = `runtime:${mass.index}:retrieved:${reference.source_id}`;
    nodes.push({
      id: nodeId,
      kind: 'retrieved_reference_image',
      stage: 'execution_reference',
      label: reference.title,
      authority: 'experimental',
      attributes: {
        ...reference,
        preview_url: reference.preview_url,
        status: reference.used_by_vlm ? 'submitted_to_vlm' : 'retrieved_not_submitted',
        vlm_input_truth: reference.used_by_vlm
          ? 'image actually submitted to recorded VLM call'
          : 'retrieved candidate only; not a VLM input',
      },
    });
    edges.push({
      id: `runtime:${mass.index}:query-match:${reference.source_id}`,
      source: queryNodeId,
      target: nodeId,
      kind: 'retrieved_program_match',
      scope: 'execution',
    });
    edges.push({
      id: `runtime:${mass.index}:reference-distill:${reference.source_id}`,
      source: nodeId,
      target: distillerNodeId,
      kind: reference.used_by_vlm ? 'reference_vlm_input' : 'available_for_reference_vlm',
      scope: reference.used_by_vlm ? 'execution' : 'pending',
    });
    edges.push({
      id: `runtime:${mass.index}:retrieved-input:${reference.source_id}`,
      source: nodeId,
      target: mappedId('flow:vlm'),
      kind: reference.used_by_vlm ? 'visual_reference_input' : 'retrieved_reference_candidate',
      scope: reference.used_by_vlm ? 'execution' : 'pending',
    });
  });
  if (retrieval) {
    edges.push({
      id: `runtime:${mass.index}:distilled-author-context`,
      source: distillerNodeId,
      target: mappedId(passport.activation_graph.nodes[0]?.id ?? ''),
      kind: 'proposes_typed_author_context',
      scope: 'pending',
    });
  }
  return {
    nodes,
    edges,
    // Pending edges stay visible as dashed provenance: they describe retrieved
    // references and candidate images that were available but not submitted.
    edgeIds: edges.map((edge) => edge.id),
    entryId: mappedId(passport.activation_graph.nodes[0]?.id ?? ''),
  };
}

function memoryStage(kind: string): string {
  if (kind === 'compiled_geometry' || kind === 'projected_geometry_program') return 'memory_geometry';
  if (kind === 'render_artifact') return 'memory_render';
  if (kind === 'geometry_portfolio') return 'memory_portfolio';
  if (kind.includes('vlm')) return 'memory_vlm';
  return 'memory_outcome';
}

function agentMemoryGraph(
  outcome: OutcomeGraphSlice | null,
  archive: ExecutedMassManifest | null,
): { nodes: NetworkNode[]; edges: NetworkEdge[] } {
  if (!outcome || outcome.status !== 'ready') return { nodes: [], edges: [] };
  const nodes: NetworkNode[] = outcome.nodes.map((node) => ({
    id: `memory:${node.id}`,
    kind: `agent_memory_${node.kind}`,
    stage: memoryStage(node.kind),
    label: node.label,
    authority: 'observed',
    attributes: {
      ...node.attributes,
      source_graph: 'GeometryOutcomeGraph',
      pnu: outcome.pnu,
    },
  }));
  const edges: NetworkEdge[] = outcome.edges.map((edge) => ({
    id: `memory:${edge.id}`,
    source: `memory:${edge.source}`,
    target: `memory:${edge.target}`,
    kind: edge.kind,
    scope: 'feedback',
  }));
  const memoryNodeByHash = new Map(
    outcome.nodes
      .filter((node) => Boolean(node.attributes.geometry_hash))
      .map((node) => [String(node.attributes.geometry_hash || ''), node.id]),
  );
  archive?.masses.forEach((mass) => {
    const memoryNodeId = memoryNodeByHash.get(mass.geometry_hash);
    if (!memoryNodeId) return;
    edges.push({
      id: `memory:join:${mass.geometry_hash}`,
      source: executedMassNodeId(mass),
      target: `memory:${memoryNodeId}`,
      kind: 'persisted_by_exact_geometry_hash',
      scope: 'feedback',
    });
  });
  return { nodes, edges };
}

function evidenceImageUrl(evidence: Record<string, unknown>): string {
  const keys = ['preview_url', 'image_url', 'asset_url', 'local_url'];
  for (const key of keys) {
    const value = evidence[key];
    if (typeof value === 'string' && /^(https?:|data:|\/)/.test(value)) return value;
  }
  return '';
}

function massLabel(label: string): string {
  return label.replace(/^MASS \d+\s*[·•-]\s*/, '');
}

export function BookLanguageFlow({ compact = false, standalone = false }: BookLanguageFlowProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [languageManifest, setLanguageManifest] = useState<MaasLanguageSystemManifest | null>(null);
  const [archive, setArchive] = useState<ExecutedMassManifest | null>(null);
  const [passport, setPassport] = useState<MassExecutionPassport | null>(null);
  const [outcomeGraph, setOutcomeGraph] = useState<OutcomeGraphSlice | null>(null);
  const [graphView, setGraphView] = useState<GraphView>('full');
  const [selectedMassIndex, setSelectedMassIndex] = useState(1);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [archiveError, setArchiveError] = useState('');
  const [passportError, setPassportError] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [lastSyncAt, setLastSyncAt] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    getMaasLanguageSystem(controller.signal)
      .then(setLanguageManifest)
      .catch(() => setLanguageManifest(null));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!archive?.pnu) return undefined;
    const geometryHash = archive.masses.find((mass) => mass.index === selectedMassIndex)?.geometry_hash;
    let active = true;
    let inFlight = false;
    const controller = new AbortController();
    const refresh = () => {
      if (inFlight) return;
      inFlight = true;
      getMaasOutcomeGraphSlice(
        archive.pnu,
        controller.signal,
        geometryHash,
        archive.selected_run_id,
      )
        .then((payload) => { if (active) setOutcomeGraph(payload); })
        .catch(() => undefined)
        .finally(() => { inFlight = false; });
    };
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      active = false;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [archive?.pnu, archive?.selected_run_id, selectedMassIndex]);

  useEffect(() => {
    const controller = new AbortController();
    getExecutedMassManifest(controller.signal)
      .then((payload) => {
        setArchive(payload);
        setSelectedMassIndex(payload.masses[0]?.index ?? 1);
        setLastSyncAt(new Date().toLocaleTimeString('ko-KR', { hour12: false }));
        setArchiveError('');
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setArchiveError(reason instanceof Error ? reason.message : '실행 MASS 아카이브를 불러오지 못했습니다.');
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    let active = true;
    let inFlight = false;
    let currentController: AbortController | null = null;
    const refresh = () => {
      if (inFlight) return;
      inFlight = true;
      currentController = new AbortController();
      getExecutedMassManifest(currentController.signal)
        .then((payload) => {
          if (!active) return;
          setArchive((current) => (
            current?.archive_revision === payload.archive_revision
              ? current
              : current && current.selected_run_id !== payload.selected_run_id
                ? {
                  ...current,
                  runs: payload.runs,
                  run_count: payload.run_count,
                  archive_revision: payload.archive_revision,
                }
                : payload
          ));
          setArchiveError('');
          setLastSyncAt(new Date().toLocaleTimeString('ko-KR', { hour12: false }));
        })
        .catch(() => undefined)
        .finally(() => { inFlight = false; });
    };
    const timer = window.setInterval(refresh, 3000);
    return () => {
      active = false;
      currentController?.abort();
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!archive) return undefined;
    if (archive.masses.length === 0) {
      setPassport(null);
      setPassportError('');
      return undefined;
    }
    const controller = new AbortController();
    setPassport(null);
    setPassportError('');
    getExecutedMassPassport(selectedMassIndex, controller.signal, archive.selected_run_id)
      .then((payload) => {
        setPassport(payload);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setPassportError(reason instanceof Error ? reason.message : 'MASS 실행 passport를 불러오지 못했습니다.');
        }
      });
    return () => controller.abort();
  }, [archive?.mass_count, archive?.selected_run_id, selectedMassIndex]);

  useEffect(() => {
    const selected = archive?.masses.find((mass) => mass.index === selectedMassIndex);
    setSelectedNodeId(
      graphView === 'full' && selected
        ? executedMassNodeId(selected)
        : graphView === 'selected'
          ? 'result:mass'
          : null,
    );
  }, [archive, graphView, selectedMassIndex]);

  useEffect(() => {
    if (!isFullscreen) return undefined;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsFullscreen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [isFullscreen]);

  const selectedMass = archive?.masses.find((mass) => mass.index === selectedMassIndex) ?? null;
  const bookSemanticPath = useMemo(
    () => selectedBookSemanticPath(languageManifest, selectedMass),
    [languageManifest, selectedMass],
  );
  const completeGraph = useMemo(
    () => fullGraph(languageManifest, archive),
    [archive, languageManifest],
  );
  const runtimeGraph = useMemo(
    () => selectedRuntimeGraph(passport, selectedMass),
    [passport, selectedMass],
  );
  const memoryGraph = useMemo(
    () => agentMemoryGraph(outcomeGraph, archive),
    [archive, outcomeGraph],
  );
  const graphNodes = useMemo<NetworkNode[]>(() => (
    [
      ...(bookSemanticPath?.nodes ?? []),
      ...(passport?.activation_graph.nodes.map((node) => {
      const materializedMassImage = node.kind === 'mass_result' || node.kind === 'mass_render_result';
      const evaluatedVlmInput = node.id === 'flow:vlm' && node.status !== 'not_evaluated';
      return {
        id: node.id,
        kind: node.kind,
        stage: node.column === 'book' ? 'book_apply' : node.column,
        label: node.label,
        authority: 'observed',
        attributes: {
          ...node.evidence,
          activation: node.activation,
          status: node.status,
          operator: node.operator,
          preview_url: materializedMassImage || evaluatedVlmInput
            ? selectedMass?.preview_url
            : evidenceImageUrl(node.evidence),
        },
      };
    }) ?? []),
    ]
  ), [bookSemanticPath, passport, selectedMass?.preview_url]);
  const graphEdges = useMemo<NetworkEdge[]>(() => (
    [
      ...(bookSemanticPath?.edges ?? []),
      ...(passport?.activation_graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      kind: edge.relation,
      scope: edge.activation > 0 ? 'execution' : 'pending',
    })) ?? []),
      ...(() => {
        if (!passport || !bookSemanticPath) return [];
        const firstBookNode = passport.activation_graph.nodes.find((node) => node.column === 'book');
        if (!firstBookNode) return [];
        const solidInput = passport.activation_graph.edges.find((edge) => edge.target === firstBookNode.id);
        return [
          ...(solidInput ? [{
            id: `book-path:solid:${solidInput.source}:${bookSemanticPath.entryId}`,
            source: solidInput.source,
            target: bookSemanticPath.entryId,
            kind: 'selects_book_base_volume',
            scope: 'execution',
          }] : []),
          {
            id: `book-path:materialize:${bookSemanticPath.targetId}:${firstBookNode.id}`,
            source: bookSemanticPath.targetId,
            target: firstBookNode.id,
            kind: 'materializes_book_rule',
            scope: 'execution',
          },
        ];
      })(),
    ]
  ), [bookSemanticPath, passport]);
  const stageOrder = useMemo(
    () => EXECUTION_STAGE_ORDER.filter((stage) => graphNodes.some((node) => node.stage === stage)),
    [graphNodes],
  );
  const runtimeBridge: NetworkEdge[] = graphView === 'full' && bookSemanticPath && runtimeGraph.entryId
    ? [{
      id: `runtime:${selectedMassIndex}:book-materialization`,
      source: bookSemanticPath.targetId,
      target: runtimeGraph.entryId,
      kind: 'materializes_selected_execution',
      scope: 'execution',
    }]
    : [];
  const displayedNodes = graphView === 'full'
    ? [...completeGraph.nodes, ...runtimeGraph.nodes, ...memoryGraph.nodes]
    : graphNodes;
  const displayedEdges = graphView === 'full'
    ? [
      ...completeGraph.edges.filter((edge) => edge.id !== `full:produced:${selectedMassIndex}`),
      ...(bookSemanticPath?.edges.filter((pathEdge) => (
        !completeGraph.edges.some((edge) => edge.source === pathEdge.source && edge.target === pathEdge.target)
      )) ?? []),
      ...runtimeBridge,
      ...runtimeGraph.edges,
      ...memoryGraph.edges,
    ]
    : graphEdges;
  const displayedStageOrder = graphView === 'full'
    ? FULL_GRAPH_STAGE_ORDER.filter((stage) => displayedNodes.some((node) => node.stage === stage))
    : stageOrder;
  const fullSelectionEdgeIds = graphView === 'full'
    && selectedMass
    && selectedNodeId === executedMassNodeId(selectedMass)
    && bookSemanticPath
    ? [
      ...bookSemanticPath.edges.map((pathEdge) => (
        displayedEdges.find((edge) => edge.source === pathEdge.source && edge.target === pathEdge.target)?.id
      )).filter((edgeId): edgeId is string => Boolean(edgeId)),
      ...runtimeBridge.map((edge) => edge.id),
      ...runtimeGraph.edgeIds,
      ...memoryGraph.edges.map((edge) => edge.id),
    ]
    : undefined;
  const vlmStage = passport?.stages.find((stage) => stage.id === 'vlm');
  const portfolioVlmAudit = archive?.portfolio_vlm_audit;
  const portfolioVlmEvaluated = Boolean(portfolioVlmAudit?.status && portfolioVlmAudit.status !== 'not_requested');
  const vlmStatusLabel = portfolioVlmEvaluated
    ? `PAID ${portfolioVlmAudit?.hard_pass ? 'PASS' : 'FAIL'}`
    : !vlmStage || vlmStage.status === 'not_evaluated' ? 'OFF' : 'ON';
  const retrievedReferenceCount = passport?.retrieved_references?.length ?? 0;
  const activeVlmReferenceCount = passport?.activation_graph.nodes.filter(
    (node) => node.kind === 'vlm_reference_image',
  ).length ?? 0;

  const resetView = () => {
    setSelectedNodeId(graphView === 'selected' ? 'result:mass' : null);
    viewportRef.current?.scrollTo({ left: 0, top: 0, behavior: 'smooth' });
  };

  const changeGraphView = (nextView: GraphView) => {
    setGraphView(nextView);
    setSelectedNodeId(
      nextView === 'full' && selectedMass
        ? executedMassNodeId(selectedMass)
        : nextView === 'selected'
          ? 'result:mass'
          : null,
    );
    viewportRef.current?.scrollTo({ left: 0, top: 0 });
  };

  const handleSelectNode = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    const mass = archive?.masses.find((item) => executedMassNodeId(item) === nodeId);
    if (mass) setSelectedMassIndex(mass.index);
  };

  const selectRun = (runId: string) => {
    const controller = new AbortController();
    getExecutedMassManifest(controller.signal, runId)
      .then((payload) => {
        setArchive(payload);
        setSelectedMassIndex(payload.masses[0]?.index ?? 1);
        setArchiveError('');
      })
      .catch((reason: unknown) => {
        setArchiveError(reason instanceof Error ? reason.message : '실행 run을 불러오지 못했습니다.');
      });
  };

  const content = (
    <section
      className={`maas-language-flow${isFullscreen ? ' maas-language-flow--fullscreen' : ''}${standalone ? ' maas-language-flow--standalone' : ''}${compact ? ' maas-language-flow--compact' : ''}`}
      data-testid="maas-book-language-flow"
    >
      <header className="maas-language-flow__header">
        <div>
          <div className="maas-language-flow__kicker">MAAS / SINGLE CAUSAL GEOMETRY GRAPH</div>
          <h1>One MASS · one executable provenance graph</h1>
          <p>BOOK is typed geometry language, never image evidence. Select one generated MASS to trace its actual program, gates, render, VLM evidence and final selection.</p>
        </div>
        <div className="maas-language-flow__header-actions">
          <button type="button" onClick={resetView} aria-label="선택 경로 초기화" title="Reset selected path"><RotateCcw size={15} /></button>
          <button type="button" onClick={() => setIsFullscreen((current) => !current)} aria-label={isFullscreen ? '전체 화면 종료' : '전체 화면'}>
            {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        </div>
      </header>

      <div className="maas-language-flow__toolbar maas-language-flow__toolbar--single">
        <div className="maas-language-flow__graph-modes" role="tablist" aria-label="Geometry graph view">
          <button
            type="button"
            role="tab"
            aria-selected={graphView === 'full'}
            data-selected={graphView === 'full'}
            onClick={() => changeGraphView('full')}
          >FULL GRAPH</button>
          <button
            type="button"
            role="tab"
            aria-selected={graphView === 'selected'}
            data-selected={graphView === 'selected'}
            onClick={() => changeGraphView('selected')}
          >SELECTED MASS PATH</button>
          <button
            type="button"
            role="tab"
            aria-selected={graphView === 'archive'}
            data-selected={graphView === 'archive'}
            onClick={() => changeGraphView('archive')}
          >MASS ARCHIVE</button>
        </div>
        <div className="maas-language-flow__single-graph-label">
          <span>{
            graphView === 'full'
              ? 'FULL BOOK LANGUAGE + EXECUTED MASS RESULTS'
              : graphView === 'selected'
                ? 'SELECTED EXECUTION PASSPORT'
                : 'ACTUAL MASS RESULTS ONLY'
          }</span>
          <strong>{selectedMass?.variant_id ?? 'LOADING'}</strong>
        </div>
        {archive && (
          <div className="maas-language-flow__counts">
            <span><b>{String(archive.mass_count).padStart(2, '0')}</b> EXECUTED</span>
            <span><b>{String(archive.run_count).padStart(2, '0')}</b> RUNS</span>
            <span><b>{archive.run_status.toUpperCase()}</b> PORTFOLIO</span>
            <span><b>0</b> BOOK RASTERS</span>
            <span><b>{vlmStatusLabel}</b> VLM</span>
            <span><b>{retrievedReferenceCount}</b> RETRIEVED / <b>{activeVlmReferenceCount}</b> USED</span>
            <span><b>LIVE</b> SYNC {lastSyncAt || '--:--:--'}</span>
          </div>
        )}
      </div>

      {archiveError && <div className="maas-language-flow__state" role="alert">{archiveError}</div>}
      {archive && (
        <nav className="execution-run-timeline" aria-label="MASS 실행 시간순 아카이브">
          <header><span>EXECUTION RUN TIMELINE</span><strong>NEWEST → OLDEST · CLICK TO REPLAY</strong></header>
          <div>
            {[...archive.runs].reverse().map((run, runIndex) => (
              <button
                type="button"
                key={run.run_id}
                data-selected={run.run_id === archive.selected_run_id}
                data-replayable={run.replayable}
                onClick={() => selectRun(run.run_id)}
                title={run.run_id}
              >
                <span>{String(runIndex + 1).padStart(2, '0')}</span>
                <b>{run.run_id.replace('book-program-portfolios-', '')}</b>
                <em>{run.selected_mass_count} MASS · {run.replayable ? 'REPLAY' : 'NO FINAL'}</em>
              </button>
            ))}
          </div>
        </nav>
      )}
      {archive && archive.masses.length === 0 && (
        <div className="maas-language-flow__state" role="status">
          이 run은 실행 기록은 보존됐지만 최종 선택 MASS가 없습니다. 실행 상태: {archive.run_status}.
        </div>
      )}
      {!archiveError && !archive && <div className="maas-language-flow__state" role="status">실행 MASS 아카이브를 불러오는 중입니다.</div>}

      {archive && graphView === 'archive' && (
        <section className="mass-only-archive" aria-label="실제 MASS 결과만 보기">
          <header>
            <div><span>ACTUAL MASS ARCHIVE</span><strong>{archive.selected_run_id}</strong></div>
            <b>{archive.mass_count} REPLAYABLE MASS RESULTS</b>
          </header>
          <div>
            {archive.masses.map((mass) => (
              <button
                type="button"
                key={mass.archive_key}
                data-selected={mass.index === selectedMassIndex}
                onClick={() => setSelectedMassIndex(mass.index)}
              >
                <img src={mass.preview_url} alt={`${mass.label} actual MASS`} />
                <span>{String(mass.index).padStart(2, '0')}</span>
                <strong>{massLabel(mass.label)}</strong>
                <em>{mass.operation_label} · FAR {mass.far_pct?.toFixed(1) ?? '--'}%</em>
              </button>
            ))}
          </div>
        </section>
      )}

      {archive && graphView !== 'archive' && (selectedMass || graphView === 'full') && (
        <div className="maas-language-flow__workspace maas-language-flow__workspace--geometry">
          <div className="maas-language-flow__viewport" ref={viewportRef} tabIndex={0} aria-label="선택한 MASS의 단일 인과 실행 그래프">
            {languageManifest && (graphView === 'full' || passport) ? (
              <LanguageNetworkCanvas
                nodes={displayedNodes}
                edges={displayedEdges}
                stageOrder={displayedStageOrder}
                selectedNodeId={selectedNodeId}
                onSelectNode={handleSelectNode}
                selectionEdgeIds={fullSelectionEdgeIds}
                axisLabels={['GEOMETRY LANGUAGE', 'MEASURED HARD GATES', 'VISUAL EVIDENCE · FINAL MASS']}
              />
            ) : <div className="maas-language-flow__state">{passportError || '선택한 MASS 실행 경로를 재생하는 중입니다.'}</div>}
          </div>

          {!compact && selectedMass && (
            <ExecutedMassEvidence
              archive={archive}
              mass={selectedMass}
              passport={passport}
              passportError={passportError}
            />
          )}

          {!compact && selectedMass && (
            <nav className="geometry-result-gallery" aria-label="실제로 실행된 MASS 결과 선택">
              <header><span>ACTUAL EXECUTED MASS RESULTS</span><strong>{archive.mass_count} ARCHIVED · SELECT ONE TO TRACE</strong></header>
              <div>
                {archive.masses.map((mass) => (
                  <button
                    type="button"
                    key={`${mass.run_id}:${mass.variant_id}`}
                    data-selected={mass.index === selectedMassIndex}
                    onClick={() => {
                      setSelectedMassIndex(mass.index);
                      setSelectedNodeId(graphView === 'full' ? executedMassNodeId(mass) : 'result:mass');
                    }}
                    aria-label={`${mass.variant_id} ${mass.label} 실행 경로 보기`}
                  >
                    <img src={mass.preview_url} alt={`${mass.label} 실제 실행 MASS`} />
                    <span>{String(mass.index).padStart(2, '0')}</span>
                    <b>{massLabel(mass.label)}</b>
                  </button>
                ))}
              </div>
            </nav>
          )}
        </div>
      )}

      <footer className="maas-language-flow__footer">
        <span>ONE GRAPH · SELECTED MASS PATH ONLY · BOOK LANGUAGE → GEOMETRY → GATES → RENDER → VLM → SELECTOR</span>
        <strong>{portfolioVlmEvaluated
          ? `PORTFOLIO VLM ${portfolioVlmAudit?.status?.toUpperCase()} · ${portfolioVlmAudit?.model || 'MODEL RECORDED'}`
          : !vlmStage || vlmStage.status === 'not_evaluated'
            ? 'VLM NOT EVALUATED · NO CLAIM'
            : `VLM ${vlmStage.status.toUpperCase()}`}</strong>
      </footer>
    </section>
  );

  return isFullscreen ? createPortal(content, document.body) : content;
}
