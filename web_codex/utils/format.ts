export function asciiProgress(pct: number, width = 30) {
  const p = Math.max(0, Math.min(1, pct))
  const filled = Math.round(p * width)
  const bar = '#'.repeat(filled) + '-'.repeat(width - filled)
  return `[${bar}] ${(p * 100).toFixed(0)}%`
}

export function prettyBytes(kb?: number | null) {
  if (!kb || kb <= 0) return '0KB'
  if (kb < 1024) return `${kb.toFixed(0)}KB`
  return `${(kb / 1024).toFixed(2)}MB`
}

export function domainFromUrl(u: string) {
  try { return new URL(u).host } catch { return u }
}

