import { callBackend } from "@/lib/api/backend";

export type ProfileView = "internal" | "client_facing";

export type ProfileResponse = {
  client_id: string;
  view: ProfileView;
  markdown: string;
  profile_regenerated_at: string | null;
};

export type RegenerateResponse = {
  client_id: string;
  profile_regenerated_at: string;
  internal_chars: number;
  client_facing_chars: number;
};

export function getProfile(
  clientId: string,
  view: ProfileView = "internal",
): Promise<ProfileResponse> {
  const params = new URLSearchParams({ view });
  return callBackend<ProfileResponse>(
    `/clients/${clientId}/profile?${params.toString()}`,
  );
}

export function regenerateProfile(clientId: string): Promise<RegenerateResponse> {
  return callBackend<RegenerateResponse>(
    `/clients/${clientId}/profile/regenerate`,
    { method: "POST" },
  );
}
