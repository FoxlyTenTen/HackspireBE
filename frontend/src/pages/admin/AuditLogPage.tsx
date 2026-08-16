import { useCallback, useEffect, useState } from 'react'
import { adminGetAuditLog } from '../../api/endpoints'
import type { AuditLogRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { formatDateTime } from '../../utils'

export default function AdminAuditLogPage() {
  const [entries, setEntries] = useState<AuditLogRead[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    adminGetAuditLog().then(setEntries).catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div>
      <h1>Audit Log</h1>
      <ErrorBanner message={error} />
      <p className="muted">Most recent admin actions first.</p>
      <table>
        <thead>
          <tr>
            <th>When</th>
            <th>Admin</th>
            <th>Action</th>
            <th>Target</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id}>
              <td>{formatDateTime(e.created_at)}</td>
              <td>{e.admin_name ?? e.admin_id}</td>
              <td>{e.action}</td>
              <td>
                {e.target_table ? `${e.target_table}${e.target_id ? ` / ${e.target_id}` : ''}` : '—'}
              </td>
              <td>{e.details ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {entries.length === 0 && <p>No admin actions recorded yet.</p>}
    </div>
  )
}
