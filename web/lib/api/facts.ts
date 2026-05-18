import { callBackend } from "@/lib/api/backend";

export type SourceSpan = { event_id: string; snippet: string };

export type Fact = {
  id: string;
  client_id: string;
  type: string;
  value: string;
  confidence_score: number;
  visibility: "operator_only" | "client_facing_safe" | "agency_visible";
  provenance: string;
  user_stance: "unreviewed" | "accepted" | "rejected" | "reframed" | "operator_curated";
  source_event_ids: string[];
  source_spans: SourceSpan[];
  superseded_by: string | null;
  created_at: string;
  updated_at: string;
};

export function listFacts(clientId: string): Promise<Fact[]> {
  const params = new URLSearchParams({ client_id: clientId });
  return callBackend<Fact[]>(`/facts?${params.toString()}`);
}

export function updateStance(
  factId: string,
  stance: "accepted" | "rejected" | "reframed" | "operator_curated",
  value?: string,
): Promise<Fact> {
  return callBackend<Fact>(`/facts/${factId}/stance`, {
    method: "POST",
    body: JSON.stringify(value ? { stance, value } : { stance }),
  });
}
