"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  getProfile,
  regenerateProfile,
  type ProfileResponse,
  type ProfileView,
} from "@/lib/api/profile";
import { Button } from "@/components/ui/button";

const VIEW_LABELS: Record<ProfileView, string> = {
  internal: "Internal (operator-only)",
  client_facing: "Client-facing (shareable)",
};

export function ProfileViewer({ clientId }: { clientId: string }) {
  const [view, setView] = useState<ProfileView>("internal");
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setProfile(null);
    setError(null);
    getProfile(clientId, view)
      .then((data) => {
        if (!cancelled) setProfile(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [clientId, view]);

  async function handleRegenerate() {
    setRegenerating(true);
    setError(null);
    try {
      await regenerateProfile(clientId);
      const data = await getProfile(clientId, view);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to regenerate");
    } finally {
      setRegenerating(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-2">
          {(Object.keys(VIEW_LABELS) as ProfileView[]).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className={`px-3 py-1.5 text-sm rounded-md border ${
                v === view
                  ? "bg-gray-900 text-white border-gray-900"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
            >
              {VIEW_LABELS[v]}
            </button>
          ))}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={regenerating}
          onClick={handleRegenerate}
        >
          {regenerating ? "Regenerating…" : "Regenerate"}
        </Button>
      </div>

      {profile?.profile_regenerated_at && (
        <p className="text-xs text-gray-500">
          Last regenerated:{" "}
          {new Date(profile.profile_regenerated_at).toLocaleString()}
        </p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {profile === null && !error && (
        <p className="text-sm text-gray-500">Loading…</p>
      )}

      {profile && profile.markdown.trim() === "" && (
        <p className="text-sm text-gray-600">
          No profile yet. Add a note or click <strong>Regenerate</strong> to
          synthesize one from existing facts.
        </p>
      )}

      {profile && profile.markdown.trim() !== "" && (
        <article className="bg-white rounded-lg border p-6 prose prose-sm max-w-none">
          <ReactMarkdown>{profile.markdown}</ReactMarkdown>
        </article>
      )}
    </div>
  );
}
