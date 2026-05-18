import { createClient } from "@/lib/supabase/client";

/**
 * Browser-side helper to call the FastAPI backend with the operator's
 * Supabase JWT. Backend's get_current_operator_id() verifies the token.
 *
 * Returns parsed JSON or throws an Error with the backend's detail field.
 */
export async function callBackend<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Not authenticated");
  }

  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL;
  if (!baseUrl) {
    throw new Error("NEXT_PUBLIC_BACKEND_API_URL is not configured");
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = `Backend ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // body not JSON
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}
