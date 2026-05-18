import { callBackend } from "@/lib/api/backend";

export type PendingState = "pending" | "confirmed" | "discarded" | "expired";

export type PendingForward = {
  id: string;
  operator_id: string;
  wa_message_id: string;
  sender_wa_id: string;
  forwarded_text: string;
  caption_text: string | null;
  wa_timestamp: string;
  suggested_client_id: string | null;
  suggested_client_name: string | null;
  suggested_confidence: number | null;
  state: PendingState;
  committed_client_id: string | null;
  committed_event_id: string | null;
  committed_at: string | null;
  discarded_reason: string | null;
  created_at: string;
  updated_at: string;
};

export function listPending(pendingOnly: boolean = true): Promise<PendingForward[]> {
  const params = new URLSearchParams({ pending_only: String(pendingOnly) });
  return callBackend<PendingForward[]>(`/pending-forwards?${params.toString()}`);
}

export function confirmForward(id: string, clientId: string): Promise<PendingForward> {
  return callBackend<PendingForward>(`/pending-forwards/${id}/confirm`, {
    method: "POST",
    body: JSON.stringify({ client_id: clientId }),
  });
}

export function discardForward(id: string, reason?: string): Promise<PendingForward> {
  return callBackend<PendingForward>(`/pending-forwards/${id}/discard`, {
    method: "POST",
    body: JSON.stringify(reason ? { reason } : {}),
  });
}
