import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { adminDeleteMaterial, adminUploadMaterial, getMaterials } from '../../api/endpoints'
import type { MaterialCategory, MaterialRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAdminAction } from '../../hooks/useAdminAction'
import { formatDateTime } from '../../utils'

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<MaterialRead[]>([])
  const [materialCategory, setMaterialCategory] = useState<MaterialCategory>('general')
  const { error, message, act } = useAdminAction()

  const load = useCallback(async () => {
    setMaterials(await getMaterials())
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await act(() => adminUploadMaterial(file, materialCategory), `Uploaded ${file.name}.`, load)
    e.target.value = ''
  }

  return (
    <div>
      <h1>Materials</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <section>
        <h2>Materials</h2>
        <select
          value={materialCategory}
          onChange={(e) => setMaterialCategory(e.target.value as MaterialCategory)}
        >
          <option value="general">General</option>
          <option value="submission_template">Submission template</option>
        </select>{' '}
        <input type="file" onChange={(e) => void handleUpload(e)} />
        <ul>
          {materials.map((material) => (
            <li key={material.id}>
              {material.file_name}{' '}
              <span className="badge">{material.category}</span>{' '}
              <span className="muted">({formatDateTime(material.uploaded_at)})</span>{' '}
              <button
                className="danger"
                onClick={() =>
                  window.confirm(`Remove ${material.file_name}?`) &&
                  void act(() => adminDeleteMaterial(material.id), 'Material removed.', load)
                }
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
