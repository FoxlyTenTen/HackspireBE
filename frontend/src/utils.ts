// Mirrors the backend's submission URL validation (app/services/submissions.py)
const GITHUB_RE = /^https:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+(\/.*)?$/
const URL_RE = /^https:\/\/\S+$/

export function isValidGithubUrl(url: string): boolean {
  return GITHUB_RE.test(url)
}

export function isValidLinkUrl(url: string): boolean {
  return URL_RE.test(url)
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

/** datetime-local input value → ISO string for the API */
export function localInputToIso(value: string): string {
  return new Date(value).toISOString()
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')

/** Resolves a backend-relative file path (e.g. `/uploads/xyz.png`) to an absolute URL. */
export function resolveFileUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (/^https?:\/\//.test(path)) return path
  return `${API_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`
}

export function downloadBlob(data: Blob, filename: string): void {
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
