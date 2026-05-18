import { createClient } from "@/lib/supabase/client";
import { callBackend } from "@/lib/api/backend";

export type UploadType = "transcript" | "voice_memo";

export type IngestionState =
  | "queued"
  | "transcribing"
  | "extracting"
  | "done"
  | "failed";

export type ErrorCode =
  | "transcription_failed"
  | "extraction_failed"
  | "storage_failed"
  | "unknown";

export type IngestionJob = {
  id: string;
  client_id: string;
  upload_type: UploadType;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  state: IngestionState;
  error_message: string | null;
  error_code: ErrorCode | null;
  transcript_text: string | null;
  event_id: string | null;
  transcription_metadata: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

/**
 * POST /uploads — multipart form. callBackend only handles JSON, so we
 * grab the Supabase JWT directly here and fetch with FormData.
 */
export async function createUpload(
  file: File,
  clientId: string,
  uploadType: UploadType,
): Promise<IngestionJob> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error("Not authenticated");

  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL;
  if (!baseUrl) throw new Error("NEXT_PUBLIC_BACKEND_API_URL is not configured");

  const form = new FormData();
  form.append("file", file);
  form.append("client_id", clientId);
  form.append("upload_type", uploadType);

  const response = await fetch(`${baseUrl}/uploads`, {
    method: "POST",
    headers: { Authorization: `Bearer ${session.access_token}` },
    body: form,
  });

  if (!response.ok) {
    let detail = `Upload ${response.status}`;
    try {
      detail = (await response.json()).detail || detail;
    } catch {
      /* response body not JSON */
    }
    throw new Error(detail);
  }
  return response.json();
}

export function getUpload(jobId: string): Promise<IngestionJob> {
  return callBackend<IngestionJob>(`/uploads/${jobId}`);
}

export function listUploads(clientId: string): Promise<IngestionJob[]> {
  const params = new URLSearchParams({ client_id: clientId });
  return callBackend<IngestionJob[]>(`/uploads?${params.toString()}`);
}
