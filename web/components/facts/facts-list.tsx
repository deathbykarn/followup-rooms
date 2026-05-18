"use client";

import { useEffect, useState } from "react";
import { listFacts, type Fact } from "@/lib/api/facts";
import { FactCard } from "@/components/facts/fact-card";

export function FactsList({ clientId }: { clientId: string }) {
  const [facts, setFacts] = useState<Fact[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    listFacts(clientId)
      .then((data) => {
        if (!cancelled) setFacts(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [clientId]);

  if (error) {
    return <p className="text-sm text-red-600">Failed to load facts: {error}</p>;
  }
  if (facts === null) {
    return <p className="text-sm text-gray-500">Loading…</p>;
  }
  if (facts.length === 0) {
    return (
      <p className="text-sm text-gray-600">
        No facts yet. Add a note and they&apos;ll appear here.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {facts.map((f) => (
        <li key={f.id}>
          <FactCard
            fact={f}
            onChanged={(updated) =>
              setFacts((prev) =>
                (prev || []).map((p) => (p.id === updated.id ? updated : p)),
              )
            }
          />
        </li>
      ))}
    </ul>
  );
}
