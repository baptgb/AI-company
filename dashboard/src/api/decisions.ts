import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface DecisionEvent {
  id: string;
  type: string;
  source: string;
  data: Record<string, any>;
  timestamp: string;
}

export function useDecisions(teamId: string, limit = 50) {
  return useQuery({
    queryKey: ['decisions', teamId],
    queryFn: () => apiFetch<{ data: DecisionEvent[] }>(`/api/decisions?team_id=${teamId}&limit=${limit}`),
    enabled: !!teamId,
    refetchInterval: 15000,
  });
}
