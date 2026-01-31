"""
AG-ACE-BRIDGE Dashboard Server

24/7 Web Dashboard for monitoring the AI Project Factory.
Shows real-time status of orchestrator, agents, and tasks.

Features:
- Real-time orchestrator status
- Agent health monitoring
- Task queue visualization
- A2A agent connection status
- Metrics and statistics
- Project progress timeline
- Pipeline stage visualization

Run:
    python -m src.server.dashboard
    # Open http://localhost:8080
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import httpx

from src.coordinator.orchestrator import Orchestrator, OrchestratorState
from src.adapters import A2AAdapterManager, A2AAgentType
from src.utils.logger import get_logger
from src.utils.config import get_settings

# Pattern automation imports
from src.watcher.pattern_watcher import PatternWatcher, PatternEvent
from src.registry.pattern_registry import PatternRegistry
from src.scheduler.trigger import ScheduleTrigger
from src.server import pattern_routes
from src.server import project_routes
from src.server import workflow_routes
from src.server import pipeline_routes

# AG-CLI Message Bus configuration
AG_CLI_MESSAGE_BUS_URL = "http://localhost:8100"


# FastAPI app
app = FastAPI(
    title="AG-ACE-BRIDGE Dashboard",
    description="24/7 AI Project Factory Monitoring Dashboard",
    version="1.0.0",
)

# Include pattern routes
app.include_router(pattern_routes.router)

# Include project routes
app.include_router(project_routes.router)

# Include workflow routes (Bridge Module)
app.include_router(workflow_routes.router)

# Include pipeline routes (E2E Project Pipeline)
app.include_router(pipeline_routes.router)

# Global instances
orchestrator: Optional[Orchestrator] = None
a2a_manager: Optional[A2AAdapterManager] = None
pattern_registry: Optional[PatternRegistry] = None
pattern_watcher: Optional[PatternWatcher] = None
schedule_trigger: Optional[ScheduleTrigger] = None
websocket_clients: List[WebSocket] = []
logger = get_logger("dashboard")
settings = get_settings()

# Project state tracking
current_project: Optional[Dict[str, Any]] = None
project_events: List[Dict[str, Any]] = []


class ProjectSubmission(BaseModel):
    """Project submission request"""
    name: str
    description: str
    project_type: str = "calculator"  # calculator, webapp, api, etc.


# HTML Template with enhanced UI
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AG-ACE-BRIDGE Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .status-running { color: #10B981; }
        .status-stopped { color: #EF4444; }
        .status-paused { color: #F59E0B; }
        .agent-healthy { background-color: #D1FAE5; }
        .agent-unhealthy { background-color: #FEE2E2; }
        .agent-working { background-color: #DBEAFE; animation: pulse 1s infinite; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .stage-pending { background-color: #F3F4F6; border-color: #D1D5DB; }
        .stage-running { background-color: #DBEAFE; border-color: #3B82F6; animation: pulse 1s infinite; }
        .stage-completed { background-color: #D1FAE5; border-color: #10B981; }
        .stage-failed { background-color: #FEE2E2; border-color: #EF4444; }
        .timeline-line { width: 2px; background: linear-gradient(to bottom, #3B82F6, #10B981); }
        .code-output {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            background: #1E293B;
            color: #E2E8F0;
            padding: 16px;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
        }
        .code-output .success { color: #10B981; }
        .code-output .error { color: #EF4444; }
        .code-output .info { color: #3B82F6; }
        .code-output .warning { color: #F59E0B; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">AG-ACE-BRIDGE</h1>
                    <p class="text-gray-600">24/7 AI Project Factory Dashboard</p>
                </div>
                <div class="text-right">
                    <div id="status-badge" class="text-2xl font-semibold status-stopped">
                        ● STOPPED
                    </div>
                    <div id="uptime" class="text-sm text-gray-500">Uptime: 0s</div>
                </div>
            </div>
        </header>

        <!-- Controls -->
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex flex-wrap gap-3">
                <button id="btn-start" onclick="startOrchestrator()"
                    class="bg-green-500 hover:bg-green-600 text-white px-5 py-2 rounded-lg font-semibold transition">
                    ▶ Start
                </button>
                <button id="btn-stop" onclick="stopOrchestrator()"
                    class="bg-red-500 hover:bg-red-600 text-white px-5 py-2 rounded-lg font-semibold transition">
                    ⏹ Stop
                </button>
                <button id="btn-pause" onclick="pauseOrchestrator()"
                    class="bg-yellow-500 hover:bg-yellow-600 text-white px-5 py-2 rounded-lg font-semibold transition">
                    ⏸ Pause
                </button>
                <button id="btn-resume" onclick="resumeOrchestrator()"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2 rounded-lg font-semibold transition">
                    ↻ Resume
                </button>
                <div class="flex-grow"></div>
                <button onclick="checkA2AHealth()"
                    class="bg-purple-500 hover:bg-purple-600 text-white px-5 py-2 rounded-lg font-semibold transition">
                    🔍 Check Agents
                </button>
            </div>
        </div>

        <!-- Project Submission -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">📁 Submit New Project</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                    <input type="text" id="project-name" value="Calculator"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Project Type</label>
                    <select id="project-type"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        <option value="calculator">Calculator App</option>
                        <option value="webapp">Web Application</option>
                        <option value="api">REST API</option>
                        <option value="cli">CLI Tool</option>
                    </select>
                </div>
                <div class="flex items-end">
                    <button onclick="submitProject()"
                        class="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2 rounded-lg font-semibold transition">
                        🚀 Submit Project
                    </button>
                </div>
            </div>
            <div class="mt-3">
                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea id="project-description" rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Describe the project requirements...">Create a Python calculator with basic operations (add, subtract, multiply, divide) and comprehensive unit tests.</textarea>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-lg shadow-md p-5">
                <h3 class="text-gray-500 text-sm">Tasks Processed</h3>
                <p id="tasks-processed" class="text-3xl font-bold text-gray-800">0</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-5">
                <h3 class="text-gray-500 text-sm">Tasks Succeeded</h3>
                <p id="tasks-succeeded" class="text-3xl font-bold text-green-600">0</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-5">
                <h3 class="text-gray-500 text-sm">Tasks Failed</h3>
                <p id="tasks-failed" class="text-3xl font-bold text-red-600">0</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-5">
                <h3 class="text-gray-500 text-sm">Queue Size</h3>
                <p id="queue-size" class="text-3xl font-bold text-blue-600">0</p>
            </div>
        </div>

        <!-- Pipeline Progress -->
        <div id="pipeline-section" class="bg-white rounded-lg shadow-md p-6 mb-6 hidden">
            <h2 class="text-xl font-bold text-gray-800 mb-4">🔄 Pipeline Progress</h2>
            <div id="current-project-info" class="mb-4 p-3 bg-blue-50 rounded-lg">
                <span class="font-semibold">Current Project:</span>
                <span id="current-project-name" class="text-blue-600">-</span>
            </div>

            <!-- Pipeline Stages -->
            <div id="pipeline-stages" class="flex flex-wrap gap-2 mb-6">
                <!-- Stages will be inserted here -->
            </div>

            <!-- Current Agent Activity -->
            <div id="agent-activity" class="mb-4">
                <h3 class="font-semibold text-gray-700 mb-2">🤖 Active Agent</h3>
                <div id="active-agent-card" class="p-4 bg-blue-50 rounded-lg border-2 border-blue-300 hidden">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold pulse">
                            AI
                        </div>
                        <div>
                            <div id="active-agent-name" class="font-semibold text-blue-700">-</div>
                            <div id="active-agent-task" class="text-sm text-gray-600">-</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Code Output -->
            <div>
                <h3 class="font-semibold text-gray-700 mb-2">📄 Output</h3>
                <div id="code-output" class="code-output">
                    <span class="text-gray-500">Waiting for project...</span>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Auto-Claude Agents -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">🧠 Auto-Claude Agents</h2>
                <div class="space-y-2" id="auto-claude-agents">
                    <div id="agent-planner" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">Planner</span>
                            <p class="text-xs text-gray-500">Project planning, task decomposition</p>
                        </div>
                        <span class="text-sm">● Idle</span>
                    </div>
                    <div id="agent-coder" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">Coder</span>
                            <p class="text-xs text-gray-500">Code implementation</p>
                        </div>
                        <span class="text-sm">● Idle</span>
                    </div>
                    <div id="agent-qa-reviewer" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">QA Reviewer</span>
                            <p class="text-xs text-gray-500">Code review, quality check</p>
                        </div>
                        <span class="text-sm">● Idle</span>
                    </div>
                    <div id="agent-qa-fixer" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">QA Fixer</span>
                            <p class="text-xs text-gray-500">Bug fixes, refactoring</p>
                        </div>
                        <span class="text-sm">● Idle</span>
                    </div>
                </div>
            </div>

            <!-- A2A Agents -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">🌐 AG A2A Agents</h2>
                <div class="space-y-2" id="a2a-agents">
                    <div id="a2a-poetry-card" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">Poetry (8003)</span>
                            <p class="text-xs text-gray-500">Creative writing</p>
                        </div>
                        <span id="a2a-poetry" class="text-sm">● Offline</span>
                    </div>
                    <div id="a2a-philosophy-card" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">Philosophy (8004)</span>
                            <p class="text-xs text-gray-500">Reasoning, analysis</p>
                        </div>
                        <span id="a2a-philosophy" class="text-sm">● Offline</span>
                    </div>
                    <div id="a2a-history-card" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">History (8005)</span>
                            <p class="text-xs text-gray-500">Historical context</p>
                        </div>
                        <span id="a2a-history" class="text-sm">● Offline</span>
                    </div>
                    <div id="a2a-calculator-card" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">Calculator (8006)</span>
                            <p class="text-xs text-gray-500">Math operations</p>
                        </div>
                        <span id="a2a-calculator" class="text-sm">● Offline</span>
                    </div>
                    <div id="a2a-gui-test-card" class="p-3 rounded border-2 agent-unhealthy flex justify-between items-center">
                        <div>
                            <span class="font-semibold">GUI Test (8120)</span>
                            <p class="text-xs text-gray-500">UI testing</p>
                        </div>
                        <span id="a2a-gui-test" class="text-sm">● Offline</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Activity Timeline -->
        <div class="bg-white rounded-lg shadow-md p-6 mt-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">📋 Activity Timeline</h2>
            <div id="activity-log" class="space-y-2 max-h-80 overflow-y-auto">
                <p class="text-gray-500 text-center py-4">No activity yet. Submit a project to get started!</p>
            </div>
        </div>

        <!-- Footer -->
        <footer class="mt-8 text-center text-gray-500 text-sm">
            <p>AG-ACE-BRIDGE v1.0 | 24/7 AI Project Factory</p>
            <p>Auto-Claude + AG autogen_a2a_kit Integration</p>
        </footer>
    </div>

    <script>
        let ws = null;
        let projectRunning = false;

        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = function() {
                console.log('WebSocket closed, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'status') {
                updateDashboard(data);
            } else if (data.type === 'project_event') {
                handleProjectEvent(data);
            } else if (data.type === 'agent_activity') {
                updateAgentActivity(data);
            } else {
                // Legacy status update
                updateDashboard(data);
            }
        }

        function updateDashboard(data) {
            // Update status badge
            const badge = document.getElementById('status-badge');
            const state = data.state || 'stopped';
            badge.innerHTML = '● ' + state.toUpperCase();
            badge.className = 'text-2xl font-semibold status-' + state;

            // Update uptime
            document.getElementById('uptime').textContent =
                'Uptime: ' + formatUptime(data.uptime_seconds);

            // Update metrics
            document.getElementById('tasks-processed').textContent =
                data.metrics?.tasks_processed || 0;
            document.getElementById('tasks-succeeded').textContent =
                data.metrics?.tasks_succeeded || 0;
            document.getElementById('tasks-failed').textContent =
                data.metrics?.tasks_failed || 0;
            document.getElementById('queue-size').textContent =
                data.queue_stats?.pending || 0;
        }

        function handleProjectEvent(data) {
            const event = data.event;

            // Show pipeline section
            document.getElementById('pipeline-section').classList.remove('hidden');
            document.getElementById('current-project-name').textContent = event.project_name || '-';

            // Update stages
            if (event.stages) {
                updatePipelineStages(event.stages);
            }

            // Update code output
            if (event.output) {
                appendCodeOutput(event.output, event.output_type || 'info');
            }

            // Log activity
            logActivity(event.icon || '📌', event.message, event.type || 'info');
        }

        function updatePipelineStages(stages) {
            const container = document.getElementById('pipeline-stages');
            container.innerHTML = '';

            stages.forEach((stage, index) => {
                const stageEl = document.createElement('div');
                stageEl.className = `px-4 py-2 rounded-lg border-2 stage-${stage.status}`;
                stageEl.innerHTML = `
                    <div class="text-xs text-gray-500">Stage ${index + 1}</div>
                    <div class="font-semibold">${stage.name}</div>
                    <div class="text-xs">${stage.agent || ''}</div>
                `;
                container.appendChild(stageEl);

                // Add arrow between stages
                if (index < stages.length - 1) {
                    const arrow = document.createElement('div');
                    arrow.className = 'flex items-center text-gray-400';
                    arrow.innerHTML = '→';
                    container.appendChild(arrow);
                }
            });
        }

        function updateAgentActivity(data) {
            const card = document.getElementById('active-agent-card');
            const nameEl = document.getElementById('active-agent-name');
            const taskEl = document.getElementById('active-agent-task');

            if (data.active) {
                card.classList.remove('hidden');
                nameEl.textContent = data.agent_name;
                taskEl.textContent = data.task_description;

                // Highlight the active agent card
                highlightAgent(data.agent_id);
            } else {
                card.classList.add('hidden');
                clearAgentHighlights();
            }
        }

        function highlightAgent(agentId) {
            clearAgentHighlights();
            const agentCard = document.getElementById(`agent-${agentId}`);
            if (agentCard) {
                agentCard.className = agentCard.className.replace('agent-unhealthy', 'agent-working');
            }
        }

        function clearAgentHighlights() {
            document.querySelectorAll('[id^="agent-"]').forEach(el => {
                el.className = el.className.replace('agent-working', 'agent-unhealthy');
            });
        }

        function appendCodeOutput(text, type = 'info') {
            const output = document.getElementById('code-output');
            const span = document.createElement('span');
            span.className = type;
            span.textContent = text + '\\n';
            output.appendChild(span);
            output.scrollTop = output.scrollHeight;
        }

        function clearCodeOutput() {
            document.getElementById('code-output').innerHTML = '';
        }

        function formatUptime(seconds) {
            if (!seconds) return '0s';
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            if (h > 0) return `${h}h ${m}m ${s}s`;
            if (m > 0) return `${m}m ${s}s`;
            return `${s}s`;
        }

        function logActivity(icon, message, type = 'info') {
            const log = document.getElementById('activity-log');

            // Remove placeholder if present
            const placeholder = log.querySelector('.text-gray-500.text-center');
            if (placeholder) {
                placeholder.remove();
            }

            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');

            let bgColor = 'bg-gray-50';
            if (type === 'success') bgColor = 'bg-green-50';
            if (type === 'error') bgColor = 'bg-red-50';
            if (type === 'warning') bgColor = 'bg-yellow-50';
            if (type === 'agent') bgColor = 'bg-blue-50';

            entry.className = `p-2 rounded ${bgColor}`;
            entry.innerHTML = `
                <span class="text-gray-400 text-xs">[${time}]</span>
                <span class="ml-2">${icon} ${message}</span>
            `;
            log.insertBefore(entry, log.firstChild);

            if (log.children.length > 100) {
                log.removeChild(log.lastChild);
            }
        }

        async function startOrchestrator() {
            const resp = await fetch('/api/start', { method: 'POST' });
            const data = await resp.json();
            logActivity('🚀', data.message, 'success');
        }

        async function stopOrchestrator() {
            const resp = await fetch('/api/stop', { method: 'POST' });
            const data = await resp.json();
            logActivity('🛑', data.message, 'warning');
        }

        async function pauseOrchestrator() {
            const resp = await fetch('/api/pause', { method: 'POST' });
            const data = await resp.json();
            logActivity('⏸️', data.message, 'warning');
        }

        async function resumeOrchestrator() {
            const resp = await fetch('/api/resume', { method: 'POST' });
            const data = await resp.json();
            logActivity('▶️', data.message, 'success');
        }

        async function submitProject() {
            const name = document.getElementById('project-name').value;
            const type = document.getElementById('project-type').value;
            const description = document.getElementById('project-description').value;

            if (!name || !description) {
                logActivity('⚠️', 'Please fill in project name and description', 'warning');
                return;
            }

            logActivity('📤', `Submitting project: ${name}`, 'info');
            clearCodeOutput();
            appendCodeOutput(`[${new Date().toLocaleTimeString()}] Submitting project: ${name}`, 'info');

            try {
                const resp = await fetch('/api/project/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, project_type: type, description })
                });
                const data = await resp.json();

                if (data.status === 'submitted') {
                    logActivity('✅', `Project submitted: ${name}`, 'success');
                    appendCodeOutput(`[${new Date().toLocaleTimeString()}] Project submitted successfully!`, 'success');
                    projectRunning = true;

                    // Show pipeline section
                    document.getElementById('pipeline-section').classList.remove('hidden');
                    document.getElementById('current-project-name').textContent = name;
                } else {
                    logActivity('❌', data.message, 'error');
                    appendCodeOutput(`Error: ${data.message}`, 'error');
                }
            } catch (e) {
                logActivity('❌', `Failed to submit project: ${e.message}`, 'error');
                appendCodeOutput(`Error: ${e.message}`, 'error');
            }
        }

        async function checkA2AHealth() {
            logActivity('🔍', 'Checking A2A agents...', 'info');

            try {
                const resp = await fetch('/api/a2a/health');
                const data = await resp.json();

                const agentMappings = {
                    'poetry_agent': { id: 'a2a-poetry', card: 'a2a-poetry-card' },
                    'philosophy_agent': { id: 'a2a-philosophy', card: 'a2a-philosophy-card' },
                    'history_agent': { id: 'a2a-history', card: 'a2a-history-card' },
                    'calculator_agent': { id: 'a2a-calculator', card: 'a2a-calculator-card' },
                    'gui_test_agent': { id: 'a2a-gui-test', card: 'a2a-gui-test-card' }
                };

                let online = 0;
                for (const [agent, mapping] of Object.entries(agentMappings)) {
                    const elem = document.getElementById(mapping.id);
                    const card = document.getElementById(mapping.card);
                    const isHealthy = data[agent];

                    elem.textContent = isHealthy ? '● Online' : '● Offline';
                    elem.style.color = isHealthy ? '#10B981' : '#EF4444';

                    if (isHealthy) {
                        card.className = 'p-3 rounded border-2 agent-healthy flex justify-between items-center';
                        online++;
                    } else {
                        card.className = 'p-3 rounded border-2 agent-unhealthy flex justify-between items-center';
                    }
                }

                logActivity('✅', `A2A Agents: ${online}/5 online`, online > 0 ? 'success' : 'warning');
            } catch (e) {
                logActivity('❌', `Failed to check A2A health: ${e.message}`, 'error');
            }
        }

        // Simulate project progress for demo
        async function simulateProjectProgress() {
            const stages = [
                { name: 'Planning', agent: 'Planner', status: 'running' },
                { name: 'Coding', agent: 'Coder', status: 'pending' },
                { name: 'Review', agent: 'QA Reviewer', status: 'pending' },
                { name: 'Testing', agent: 'QA Fixer', status: 'pending' }
            ];

            for (let i = 0; i < stages.length; i++) {
                // Mark current stage as running
                stages[i].status = 'running';
                updatePipelineStages(stages);

                handleProjectEvent({
                    event: {
                        project_name: document.getElementById('project-name').value,
                        stages: stages,
                        icon: '🤖',
                        message: `${stages[i].agent} is working on ${stages[i].name}...`,
                        type: 'agent'
                    }
                });

                await new Promise(resolve => setTimeout(resolve, 3000));

                // Mark stage as completed
                stages[i].status = 'completed';
                updatePipelineStages(stages);

                handleProjectEvent({
                    event: {
                        project_name: document.getElementById('project-name').value,
                        stages: stages,
                        icon: '✅',
                        message: `${stages[i].name} completed by ${stages[i].agent}`,
                        type: 'success'
                    }
                });

                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        // Initialize
        connectWebSocket();

        // Poll status every 2 seconds
        setInterval(async () => {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                updateDashboard(data);
            } catch (e) {}
        }, 2000);

        // Initial A2A health check
        setTimeout(checkA2AHealth, 1000);
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve main dashboard"""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/status")
async def get_status():
    """Get current orchestrator status"""
    global orchestrator

    if not orchestrator:
        return {
            "state": "stopped",
            "uptime_seconds": 0,
            "metrics": {},
            "queue_stats": {},
        }

    return orchestrator.get_status()


@app.post("/api/start")
async def start_orchestrator_endpoint():
    """Start the orchestrator"""
    global orchestrator

    if orchestrator and orchestrator.state == OrchestratorState.RUNNING:
        return {"status": "already_running", "message": "Orchestrator is already running"}

    # Create new orchestrator if needed
    if not orchestrator or orchestrator.state == OrchestratorState.STOPPED:
        orchestrator = Orchestrator()

    # Start in background
    asyncio.create_task(orchestrator.start())

    return {"status": "starting", "message": "Orchestrator is starting..."}


@app.post("/api/stop")
async def stop_orchestrator_endpoint():
    """Stop the orchestrator"""
    global orchestrator

    if not orchestrator or orchestrator.state != OrchestratorState.RUNNING:
        return {"status": "not_running", "message": "Orchestrator is not running"}

    await orchestrator.stop()
    return {"status": "stopped", "message": "Orchestrator stopped"}


@app.post("/api/pause")
async def pause_orchestrator_endpoint():
    """Pause the orchestrator"""
    global orchestrator

    if not orchestrator or orchestrator.state != OrchestratorState.RUNNING:
        return {"status": "not_running", "message": "Orchestrator is not running"}

    orchestrator.pause()
    return {"status": "paused", "message": "Orchestrator paused"}


@app.post("/api/resume")
async def resume_orchestrator_endpoint():
    """Resume the orchestrator"""
    global orchestrator

    if not orchestrator or orchestrator.state != OrchestratorState.PAUSED:
        return {"status": "not_paused", "message": "Orchestrator is not paused"}

    orchestrator.resume()
    return {"status": "running", "message": "Orchestrator resumed"}


@app.post("/api/project/submit")
async def submit_project(project: ProjectSubmission):
    """Submit a new project for processing"""
    global current_project, project_events

    project_id = str(uuid.uuid4())[:8]

    current_project = {
        "id": project_id,
        "name": project.name,
        "type": project.project_type,
        "description": project.description,
        "status": "submitted",
        "submitted_at": datetime.now().isoformat(),
    }

    # Clear previous events
    project_events = []

    # Add submission event
    project_events.append({
        "timestamp": datetime.now().isoformat(),
        "type": "submitted",
        "message": f"Project '{project.name}' submitted for processing",
    })

    # Broadcast to WebSocket clients
    await broadcast_project_event({
        "project_name": project.name,
        "icon": "📥",
        "message": f"Project '{project.name}' submitted",
        "type": "info",
        "stages": [
            {"name": "Planning", "agent": "Planner", "status": "pending"},
            {"name": "Coding", "agent": "Coder", "status": "pending"},
            {"name": "Review", "agent": "QA Reviewer", "status": "pending"},
            {"name": "Testing", "agent": "QA Fixer", "status": "pending"},
        ]
    })

    # Start project processing in background
    asyncio.create_task(process_project_demo(project))

    return {
        "status": "submitted",
        "project_id": project_id,
        "message": f"Project '{project.name}' submitted successfully"
    }


async def process_project_demo(project: ProjectSubmission):
    """Demo: Simulate project processing through pipeline stages"""
    global current_project, project_events

    stages = [
        {"name": "Planning", "agent": "Planner", "status": "pending", "duration": 2},
        {"name": "Coding", "agent": "Coder", "status": "pending", "duration": 4},
        {"name": "Review", "agent": "QA Reviewer", "status": "pending", "duration": 2},
        {"name": "Testing", "agent": "QA Fixer", "status": "pending", "duration": 2},
    ]

    # Send initial message to AG-CLI Message Bus
    await send_to_ag_cli_message_bus(
        "Orchestrator", "all",
        f"Starting project: {project.name} ({project.project_type})",
        "say"
    )

    for i, stage in enumerate(stages):
        # Mark stage as running
        stages[i]["status"] = "running"

        await broadcast_project_event({
            "project_name": project.name,
            "icon": "🔄",
            "message": f"Stage '{stage['name']}' started - {stage['agent']} working...",
            "type": "agent",
            "stages": [{"name": s["name"], "agent": s["agent"], "status": s["status"]} for s in stages],
            "output": f"[{stage['agent']}] Starting {stage['name'].lower()} phase...",
            "output_type": "info"
        })

        # Send to AG-CLI Message Bus
        await send_to_ag_cli_message_bus(
            "Orchestrator", stage["agent"],
            f"Please start {stage['name'].lower()} for project: {project.name}",
            "ask"
        )

        await asyncio.sleep(0.5)

        # Agent starts working
        await send_to_ag_cli_message_bus(
            stage["agent"], "Orchestrator",
            f"Starting {stage['name'].lower()} phase...",
            "work"
        )

        # Simulate work
        await asyncio.sleep(stage["duration"])

        # Generate some demo output
        if stage["name"] == "Planning":
            planning_msg = f"Analyzing requirements for {project.name}...\nCreating task breakdown:\n  - Task 1: Create main module\n  - Task 2: Implement core functions\n  - Task 3: Add error handling\n  - Task 4: Write unit tests"
            await broadcast_project_event({
                "project_name": project.name,
                "output": f"[Planner] {planning_msg}",
                "output_type": "info"
            })
            await send_to_ag_cli_message_bus("Planner", "Coder", planning_msg, "say")

        elif stage["name"] == "Coding":
            coding_msg = f"Generating code for {project.name}...\nCreating main.py...\nImplementing Calculator class...\nAdding add(), subtract(), multiply(), divide() methods..."
            await broadcast_project_event({
                "project_name": project.name,
                "output": f"[Coder] {coding_msg}",
                "output_type": "info"
            })
            await send_to_ag_cli_message_bus("Coder", "QA Reviewer", coding_msg, "say")

        elif stage["name"] == "Review":
            review_msg = "Reviewing code quality...\nChecking for best practices...\nVerifying error handling...\nCode review passed with suggestions"
            await broadcast_project_event({
                "project_name": project.name,
                "output": f"[QA Reviewer] {review_msg}",
                "output_type": "info"
            })
            await send_to_ag_cli_message_bus("QA Reviewer", "QA Fixer", review_msg, "say")

        elif stage["name"] == "Testing":
            testing_msg = "Running unit tests...\ntest_add: PASSED\ntest_subtract: PASSED\ntest_multiply: PASSED\ntest_divide: PASSED\ntest_divide_by_zero: PASSED\nAll 5 tests passed!"
            await broadcast_project_event({
                "project_name": project.name,
                "output": f"[QA Fixer] {testing_msg}",
                "output_type": "success"
            })
            await send_to_ag_cli_message_bus("QA Fixer", "Orchestrator", testing_msg, "say")

        await asyncio.sleep(0.5)

        # Mark stage as completed
        stages[i]["status"] = "completed"

        # Send completion to AG-CLI Message Bus
        await send_to_ag_cli_message_bus(
            stage["agent"], "Orchestrator",
            f"{stage['name']} completed successfully!",
            "say"
        )

        await broadcast_project_event({
            "project_name": project.name,
            "icon": "✅",
            "message": f"Stage '{stage['name']}' completed",
            "type": "success",
            "stages": [{"name": s["name"], "agent": s["agent"], "status": s["status"]} for s in stages],
        })

    # Project completed
    await send_to_ag_cli_message_bus(
        "Orchestrator", "all",
        f"Project '{project.name}' completed successfully! All tests passed.",
        "say"
    )

    await broadcast_project_event({
        "project_name": project.name,
        "icon": "🎉",
        "message": f"Project '{project.name}' completed successfully!",
        "type": "success",
        "output": f"\n{'='*50}\n  PROJECT COMPLETED SUCCESSFULLY!\n  Name: {project.name}\n  Type: {project.project_type}\n  Status: All tests passed\n{'='*50}",
        "output_type": "success"
    })


async def broadcast_project_event(event: Dict[str, Any]):
    """Broadcast project event to all WebSocket clients"""
    message = {
        "type": "project_event",
        "event": event
    }

    for client in websocket_clients:
        try:
            await client.send_json(message)
        except Exception:
            pass


async def send_to_ag_cli_message_bus(from_agent: str, to_agent: str, message: str, event_type: str = "say"):
    """Send agent dialogue to AG-CLI Message Bus for visualization in Studio Viewer"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message": message,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat()
            }
            await client.post(
                f"{AG_CLI_MESSAGE_BUS_URL}/publish",
                json=payload,
                timeout=5.0
            )
    except Exception as e:
        logger.debug(f"Could not send to AG-CLI Message Bus: {e}")


@app.get("/api/project/status")
async def get_project_status():
    """Get current project status"""
    global current_project, project_events

    return {
        "project": current_project,
        "events": project_events[-20:] if project_events else []
    }


@app.get("/api/a2a/health")
async def check_a2a_health():
    """Check health of all A2A agents"""
    global a2a_manager

    if not a2a_manager:
        a2a_manager = A2AAdapterManager()
        await a2a_manager.initialize_all()

    health = await a2a_manager.health_check_all()

    # Convert enum keys to strings
    return {agent.value: status for agent, status in health.items()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_clients.append(websocket)

    try:
        while True:
            # Send status every 2 seconds
            status = orchestrator.get_status() if orchestrator else {
                "state": "stopped",
                "uptime_seconds": 0,
            }
            status["type"] = "status"
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
    except Exception:
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)


async def broadcast_status():
    """Broadcast status to all connected clients"""
    while True:
        status = orchestrator.get_status() if orchestrator else {}
        status["type"] = "status"
        for client in websocket_clients:
            try:
                await client.send_json(status)
            except Exception:
                pass
        await asyncio.sleep(2)


@app.on_event("startup")
async def startup_event():
    """Initialize pattern automation and project design on startup"""
    global pattern_registry, pattern_watcher, schedule_trigger, orchestrator

    logger.info("Initializing AG-ACE-BRIDGE systems...")

    # Initialize Orchestrator (24/7 task execution)
    orchestrator = Orchestrator()
    logger.info("Orchestrator initialized")

    # Initialize Auto-Claude Adapters
    from src.adapters import AutoClaudeAdapter, A2AAdapterManager

    planner_adapter = None
    try:
        planner_adapter = AutoClaudeAdapter(agent_type="AUTO_CLAUDE_PLANNER")
        await planner_adapter.initialize()
        logger.info("Auto-Claude Planner adapter initialized")
    except Exception as e:
        logger.warning(f"Auto-Claude Planner init failed (will use template fallback): {e}")

    # Initialize A2A adapters for AutoGen Studio agents
    a2a_adapters = None
    try:
        a2a_adapters = A2AAdapterManager()
        await a2a_adapters.initialize_all()
        logger.info("A2A adapters initialized")
    except Exception as e:
        logger.warning(f"A2A adapters init failed: {e}")

    # Initialize PatternRegistry
    pattern_registry = PatternRegistry(
        shared_memory_url="http://localhost:8101",
        enable_shared_memory=True,
    )
    await pattern_registry.initialize()

    # Initialize ScheduleTrigger
    schedule_trigger = ScheduleTrigger(
        registry=pattern_registry,
        orchestrator=orchestrator,
        shared_memory_url="http://localhost:8101",
        enable_shared_memory=True,
    )
    await schedule_trigger.start()

    # Set dependencies for pattern routes
    pattern_routes.set_dependencies(
        registry=pattern_registry,
        scheduler=schedule_trigger,
    )

    # Initialize project routes with Auto-Claude Planner
    project_routes.initialize(
        registry=pattern_registry,
        scheduler=schedule_trigger,
        orchestrator=orchestrator,
        planner_adapter=planner_adapter,
        a2a_adapters=a2a_adapters,
    )

    # Initialize workflow routes for Bridge Module
    workflow_routes.initialize(auto_claude_path="D:/Data/25_ACE/Auto-Claude")

    # Initialize PatternWatcher
    async def on_pattern_detected(event: PatternEvent):
        """Handle detected patterns from AutoGen Studio"""
        logger.info(
            "pattern_detected",
            pattern_name=event.pattern_name,
            file_path=event.file_path,
        )
        # Auto-register pattern
        pattern = await pattern_registry.register(event)
        if pattern:
            # Broadcast to WebSocket clients
            await broadcast_project_event({
                "icon": "📦",
                "message": f"New pattern detected: {event.pattern_name}",
                "type": "info",
            })

    pattern_watcher = PatternWatcher(
        watch_paths=[
            "./patterns",
            "~/.autogenstudio/patterns",
            "~/.autogenstudio/workflows",
        ],
        on_pattern_detected=on_pattern_detected,
    )
    await pattern_watcher.start()

    # Scan existing patterns
    existing = await pattern_watcher.scan_existing()
    for event in existing:
        await pattern_registry.register(event)

    logger.info(
        "pattern_automation_initialized",
        patterns_loaded=len(existing),
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global pattern_registry, pattern_watcher, schedule_trigger

    if pattern_watcher:
        await pattern_watcher.stop()
    if schedule_trigger:
        await schedule_trigger.stop()
    if pattern_registry:
        await pattern_registry.shutdown()

    logger.info("pattern_automation_shutdown")


def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """
    Run the dashboard server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    print("=" * 60)
    print("AG-ACE-BRIDGE Dashboard")
    print("=" * 60)
    print(f"Starting dashboard server at http://{host}:{port}")
    print("")
    print("Pattern Automation:")
    print("  - Watches: ./patterns, ~/.autogenstudio/*")
    print("  - REST API: /patterns/*")
    print("")
    print("Project Design System:")
    print("  - REST API: /projects/*")
    print("  - Design: POST /projects/design")
    print("  - Execute: POST /projects/{id}/execute")
    print("")
    print("SharedMemory: http://localhost:8101")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_dashboard()
