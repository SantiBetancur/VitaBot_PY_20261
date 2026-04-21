import { useCallback } from 'react'

/**
 * Returns a ref-callback that auto-resizes a textarea to its content.
 * @param {number} maxHeight - Max height in px before scrolling (default 140).
 */
export function useAutoResize(maxHeight = 140) {
  const resize = useCallback((el) => {
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, maxHeight) + 'px'
  }, [maxHeight])

  return resize
}