/** Shared React Query keys, so independent components dedupe onto one fetch/poll. */
export const queryKeys = {
  notifications: ['notifications'] as const,
  participants: (search?: string) => ['participants', search ?? ''] as const,
  invitations: ['invitations'] as const,
  joinRequests: ['join-requests'] as const,
}
