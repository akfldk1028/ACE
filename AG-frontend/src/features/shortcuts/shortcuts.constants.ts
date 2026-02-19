import type { ShortcutGroup } from './shortcuts.types'

export const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    label: 'Navigation',
    shortcuts: [
      { keys: ['G', 'P'], description: 'Go to Playground' },
      { keys: ['G', 'B'], description: 'Go to Team Builder' },
      { keys: ['G', 'M'], description: 'Go to MCP' },
      { keys: ['G', 'A'], description: 'Go to A2A Agents' },
      { keys: ['G', 'L'], description: 'Go to Gallery' },
      { keys: ['G', 'H'], description: 'Go to History' },
      { keys: ['G', 'S'], description: 'Go to Settings' },
    ],
  },
  {
    label: 'Playground',
    shortcuts: [
      { keys: ['Enter'], description: 'Send message / Run task' },
      { keys: ['Ctrl', 'K'], description: 'Focus task input' },
      { keys: ['Escape'], description: 'Stop execution' },
    ],
  },
  {
    label: 'General',
    shortcuts: [
      { keys: ['?'], description: 'Show keyboard shortcuts' },
      { keys: ['Ctrl', '/'], description: 'Toggle sidebar' },
    ],
  },
]
