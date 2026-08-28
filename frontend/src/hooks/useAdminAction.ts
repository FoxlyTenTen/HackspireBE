import { useState } from 'react'

export function useAdminAction() {
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const act = async (
    action: () => Promise<unknown>,
    successMessage: string,
    onSuccess?: () => Promise<unknown>,
  ) => {
    setError(null)
    setMessage(null)
    try {
      await action()
      if (onSuccess) await onSuccess()
      setMessage(successMessage)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return { error, message, setError, setMessage, act }
}
