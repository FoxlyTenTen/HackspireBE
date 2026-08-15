// Mirrors the backend's submission URL validation (app/services/submissions.py)
const GITHUB_RE = /^https:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+(\/.*)?$/
const DRIVE_RE = /^https:\/\/(drive|docs)\.google\.com\/\S+$/

export function isValidGithubUrl(url: string): boolean {
  return GITHUB_RE.test(url)
}

export function isValidGdriveUrl(url: string): boolean {
  return DRIVE_RE.test(url)
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

/** datetime-local input value → ISO string for the API */
export function localInputToIso(value: string): string {
  return new Date(value).toISOString()
}

export function downloadBlob(data: Blob, filename: string): void {
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
