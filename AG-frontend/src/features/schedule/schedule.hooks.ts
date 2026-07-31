import { useEffect, useRef } from 'react'
import { useScheduleStore } from './schedule.store'

const CHANNEL_NAME = 'ag-schedule-leader'

/**
 * Elect a single tab as the schedule runner using BroadcastChannel.
 * The first tab to claim leadership runs timers; others defer.
 * When the leader tab closes, another tab takes over.
 */
export function useScheduleRunner(onExecute: (jobId: string, teamId: number, task: string) => void) {
  const isLeaderRef = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined)

  useEffect(() => {
    // BroadcastChannel for leader election
    let channel: BroadcastChannel | null = null
    try {
      channel = new BroadcastChannel(CHANNEL_NAME)
    } catch {
      // BroadcastChannel not supported — this tab is always leader
      isLeaderRef.current = true
    }

    // Claim leadership
    const leaderId = `tab-${Date.now()}-${Math.random()}`

    if (channel) {
      // Announce candidacy
      channel.postMessage({ type: 'claim', id: leaderId })
      isLeaderRef.current = true

      channel.onmessage = (e) => {
        if (e.data?.type === 'claim' && e.data.id !== leaderId) {
          // Another tab is claiming — only the earliest wins
          if (e.data.id < leaderId) {
            isLeaderRef.current = false
          }
        }
      }
    }

    // Timer loop: check every 30s for jobs that need execution
    intervalRef.current = setInterval(() => {
      if (!isLeaderRef.current) return

      const now = new Date()
      const jobs = useScheduleStore.getState().jobs

      for (const job of jobs) {
        if (!job.enabled || !job.nextRunAt) continue
        const nextRun = new Date(job.nextRunAt)
        if (nextRun <= now) {
          onExecute(job.id, job.teamId, job.task)
          useScheduleStore.getState().refreshNextRun(job.id)
        }
      }
    }, 30_000)

    return () => {
      clearInterval(intervalRef.current)
      channel?.close()
    }
  }, [onExecute])
}
