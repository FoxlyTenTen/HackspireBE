import { useEffect } from 'react'

/**
 * Polls `fn` immediately and then every `intervalMs`, pausing while the tab
 * is hidden (notifications are polling-based per the spec — no websockets).
 * `fn` should be wrapped in useCallback by the caller.
 */
export function usePolling(fn: () => void | Promise<void>, intervalMs: number): void {
  useEffect(() => {
    const tick = () => {
      if (!document.hidden) void fn()
    }
    tick()
    const timer = window.setInterval(tick, intervalMs)
    const onVisibility = () => {
      if (!document.hidden) void fn()
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [fn, intervalMs])
}
