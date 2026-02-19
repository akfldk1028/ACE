export interface Shortcut {
  keys: string[]
  description: string
}

export interface ShortcutGroup {
  label: string
  shortcuts: Shortcut[]
}
