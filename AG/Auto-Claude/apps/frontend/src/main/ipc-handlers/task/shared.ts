import type { Task, Project } from '../../../shared/types';
import { projectStore } from '../../project-store';

/**
 * Check if a task ID belongs to an ephemeral (memory-only) task.
 * Ephemeral tasks (AutoGen/Pipeline) have no disk spec directory,
 * no worktree, and cannot be started/stopped/recovered.
 */
export function isEphemeralTaskId(taskId: string): boolean {
  return taskId.startsWith('autogen_') || taskId.startsWith('pipeline_');
}

/**
 * Helper function to find task and project by taskId
 */
export const findTaskAndProject = (taskId: string): { task: Task | undefined; project: Project | undefined } => {
  const projects = projectStore.getProjects();
  let task: Task | undefined;
  let project: Project | undefined;

  for (const p of projects) {
    const tasks = projectStore.getTasks(p.id);
    // Prioritize exact id match to prevent collisions
    task = tasks.find((t) => t.id === taskId) || tasks.find((t) => t.specId === taskId);
    if (task) {
      project = p;
      break;
    }
  }

  return { task, project };
};
