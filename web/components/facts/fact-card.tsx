"use client";

import { useState } from "react";
import type { Fact } from "@/lib/api/facts";
import { updateStance } from "@/lib/api/facts";
import { Button } from "@/components/ui/button";

const STANCE_LABELS: Record<Fact["user_stance"], string> = {
  unreviewed: "Unreviewed",
  accepted: "Accepted",
  rejected: "Rejected",
  reframed: "Reframed",
  operator_curated: "Operator-written",
};

const STANCE_COLORS: Record<Fact["user_stance"], string> = {
  unreviewed: "bg-gray-100 text-gray-700",
  accepted: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-700",
  reframed: "bg-amber-100 text-amber-800",
  operator_curated: "bg-blue-100 text-blue-800",
};

export function FactCard({
  fact,
  onChanged,
}: {
  fact: Fact;
  onChanged?: (updated: Fact) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function applyStance(
    stance: "accepted" | "rejected" | "reframed",
    value?: string,
  ) {
    setBusy(true);
    setError(null);
    try {
      const updated = await updateStance(fact.id, stance, value);
      onChanged?.(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="bg-white rounded-lg border p-4">
      <header className="flex justify-between items-start mb-2">
        <div>
          <span className="text-xs font-medium text-gray-500 uppercase">
            {fact.type.replace(/_/g, " ")}
          </span>
          <span
            className={`ml-2 px-2 py-0.5 text-xs rounded-full ${STANCE_COLORS[fact.user_stance]}`}
          >
            {STANCE_LABELS[fact.user_stance]}
          </span>
        </div>
        <span className="text-xs text-gray-400">
          conf {Math.round(fact.confidence_score * 100)}%
        </span>
      </header>

      <p className="text-sm text-gray-900 mb-2">{fact.value}</p>

      {fact.source_spans.length > 0 && (
        <details className="text-xs text-gray-600 mb-3">
          <summary className="cursor-pointer hover:text-gray-900">
            {fact.source_spans.length} source span
            {fact.source_spans.length > 1 ? "s" : ""}
          </summary>
          <ul className="mt-2 space-y-1 pl-3 border-l-2 border-gray-200">
            {fact.source_spans.map((span, i) => (
              <li key={i} className="italic">
                &ldquo;{span.snippet}&rdquo;
              </li>
            ))}
          </ul>
        </details>
      )}

      {fact.user_stance === "unreviewed" && (
        <div className="flex gap-2 mt-3">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => applyStance("accepted")}
          >
            Accept
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => applyStance("rejected")}
          >
            Reject
          </Button>
        </div>
      )}

      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </article>
  );
}
