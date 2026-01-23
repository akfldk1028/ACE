import { Bot, Network, RefreshCw, Loader2, CheckCircle2, AlertCircle, Circle } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Switch } from '../../ui/switch';
import { Separator } from '../../ui/separator';
import type { ProjectEnvConfig, A2ASyncStatus } from '../../../../shared/types';

interface A2AIntegrationProps {
  envConfig: ProjectEnvConfig | null;
  updateEnvConfig: (updates: Partial<ProjectEnvConfig>) => void;
  a2aConnectionStatus: A2ASyncStatus | null;
  isCheckingA2A: boolean;
  onRefresh?: () => void;
}

/**
 * A2A (Agent-to-Agent) integration settings component.
 * Manages A2A agents from AG-ACE-BRIDGE via Google ADK protocol.
 */
export function A2AIntegration({
  envConfig,
  updateEnvConfig,
  a2aConnectionStatus,
  isCheckingA2A,
  onRefresh
}: A2AIntegrationProps) {
  if (!envConfig) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <Label className="font-normal text-foreground">Enable A2A Agents</Label>
          <p className="text-xs text-muted-foreground">
            Use specialized agents (poetry, math, GPU) from AutoGen Studio
          </p>
        </div>
        <Switch
          checked={envConfig.a2aEnabled || false}
          onCheckedChange={(checked) => updateEnvConfig({ a2aEnabled: checked })}
        />
      </div>

      {envConfig.a2aEnabled && (
        <>
          <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">AutoGen Studio URL</Label>
            <p className="text-xs text-muted-foreground">
              Base URL of the A2A agents (ports 8003-8120)
            </p>
            <Input
              placeholder="http://127.0.0.1"
              value={envConfig.a2aAutogenStudioUrl || 'http://127.0.0.1'}
              onChange={(e) => updateEnvConfig({ a2aAutogenStudioUrl: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">A2A Demo Path (Optional)</Label>
            <p className="text-xs text-muted-foreground">
              Path to a2a_demo folder for direct agent discovery
            </p>
            <Input
              placeholder="D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo"
              value={envConfig.a2aDemoPath || ''}
              onChange={(e) => updateEnvConfig({ a2aDemoPath: e.target.value })}
            />
          </div>

          {/* Connection Status */}
          <ConnectionStatus
            isChecking={isCheckingA2A}
            connectionStatus={a2aConnectionStatus}
            onRefresh={onRefresh}
          />

          {/* Agent List */}
          {a2aConnectionStatus?.agents && a2aConnectionStatus.agents.length > 0 && (
            <AgentList agents={a2aConnectionStatus.agents} />
          )}

          <Separator />

          {/* Auto Discovery Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-info" />
                <Label className="font-normal text-foreground">Auto Discovery</Label>
              </div>
              <p className="text-xs text-muted-foreground pl-6">
                Automatically discover new agents on startup
              </p>
            </div>
            <Switch
              checked={envConfig.a2aAutoDiscovery || false}
              onCheckedChange={(checked) => updateEnvConfig({ a2aAutoDiscovery: checked })}
            />
          </div>

          {/* Info Box */}
          <InfoBox />
        </>
      )}
    </div>
  );
}

interface ConnectionStatusProps {
  isChecking: boolean;
  connectionStatus: A2ASyncStatus | null;
  onRefresh?: () => void;
}

function ConnectionStatus({ isChecking, connectionStatus, onRefresh }: ConnectionStatusProps) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-foreground">Agent Status</p>
          <p className="text-xs text-muted-foreground">
            {isChecking ? 'Discovering agents...' :
              connectionStatus?.connected
                ? `${connectionStatus.onlineAgentCount}/${connectionStatus.agentCount} agents online`
                : connectionStatus?.error || 'Not connected'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onRefresh}
              disabled={isChecking}
            >
              <RefreshCw className={`h-4 w-4 ${isChecking ? 'animate-spin' : ''}`} />
            </Button>
          )}
          {isChecking ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : connectionStatus?.connected ? (
            <CheckCircle2 className="h-4 w-4 text-success" />
          ) : (
            <AlertCircle className="h-4 w-4 text-warning" />
          )}
        </div>
      </div>
    </div>
  );
}

interface AgentListProps {
  agents: A2ASyncStatus['agents'];
}

function AgentList({ agents }: AgentListProps) {
  if (!agents || agents.length === 0) return null;

  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground flex items-center gap-2">
        <Network className="h-4 w-4" />
        Available Agents
      </Label>
      <div className="rounded-lg border border-border bg-muted/20 p-2 space-y-1 max-h-48 overflow-y-auto">
        {agents.map((agent) => (
          <div
            key={agent.name}
            className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50"
          >
            <div className="flex items-center gap-2">
              <Circle
                className={`h-2 w-2 ${agent.isOnline ? 'fill-success text-success' : 'fill-muted-foreground text-muted-foreground'}`}
              />
              <span className="text-sm font-medium">{agent.displayName}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {agent.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function InfoBox() {
  return (
    <div className="rounded-lg border border-info/30 bg-info/5 p-3">
      <div className="flex items-start gap-3">
        <Bot className="h-5 w-5 text-info mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">How it works</p>
          <p className="text-xs text-muted-foreground mt-1">
            When enabled, the Coder agent can call specialized A2A agents for tasks like
            poetry generation, mathematical calculations, GPU processing, and more.
            Agents are discovered from ports 8003-8120 using the Google ADK A2A protocol.
          </p>
        </div>
      </div>
    </div>
  );
}
