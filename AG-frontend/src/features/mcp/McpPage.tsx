import { Card, Badge, Button, Input } from '@/shared/ui'
import { Wrench, Plus, Play, Server } from 'lucide-react'

export function McpPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">MCP</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Model Context Protocol workbench
          </p>
          <div className="mt-2"><Badge variant="warning">Experimental</Badge></div>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Workbench
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Server className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">MCP Servers</h2>
          </div>
          <p className="text-body-medium text-(--color-text-tertiary) mb-4">
            Configure MCP tool servers for agent integration.
          </p>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Input placeholder="Server URL (e.g., stdio://...)" className="flex-1" />
              <Button size="sm" variant="secondary">
                <Plus className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Wrench className="w-5 h-5 text-(--color-text-secondary)" />
            <h2 className="text-heading-small">Available Tools</h2>
          </div>
          <p className="text-body-medium text-(--color-text-tertiary) mb-4">
            Tools discovered from connected MCP servers.
          </p>
          <div className="text-center py-8">
            <Wrench className="w-12 h-12 mx-auto text-(--color-text-tertiary) mb-3" />
            <p className="text-body-small text-(--color-text-tertiary)">
              Connect an MCP server to discover tools
            </p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Play className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Test Workbench</h2>
        </div>
        <p className="text-body-medium text-(--color-text-tertiary)">
          Test MCP tool calls interactively. Select a tool above and provide input to test.
        </p>
      </Card>
    </div>
  )
}
