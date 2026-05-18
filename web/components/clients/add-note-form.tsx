"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { callBackend } from "@/lib/api/backend";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type IngestResponse = {
  event_id: string;
  facts_added: number;
  facts_updated: number;
  facts_noop: number;
  facts_deleted: number;
  profile_regenerated: boolean;
};

export function AddNoteForm({ clientId }: { clientId: string }) {
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (rawText.trim().length < 10) {
      setError("Note must be at least 10 characters.");
      return;
    }

    setLoading(true);
    try {
      const response = await callBackend<IngestResponse>("/events", {
        method: "POST",
        body: JSON.stringify({
          client_id: clientId,
          source_type: "manual_note",
          raw_text: rawText,
        }),
      });
      setResult(response);
      setRawText("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save note");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <div className="space-y-2">
        <Label htmlFor="raw_text">Note</Label>
        <Textarea
          id="raw_text"
          rows={8}
          required
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder={
            "What did you learn? E.g., 'Sarah told me her parents live in Marine Parade and that she prefers being close to them. Budget around $1.8M. Wants to view this weekend.'"
          }
        />
        <p className="text-xs text-gray-500">
          The note is stored verbatim, then Claude extracts structured facts you
          can review.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-green-900">
          Note saved. Facts: {result.facts_added} added · {result.facts_updated}{" "}
          updated · {result.facts_noop} no-op.{" "}
          {result.profile_regenerated && "Profile refreshed."}
        </div>
      )}

      <Button type="submit" disabled={loading}>
        {loading ? "Saving…" : "Save note"}
      </Button>
    </form>
  );
}
