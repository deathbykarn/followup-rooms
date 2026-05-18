"use client";

import { useEffect, useState } from "react";
import { listUploads, type IngestionJob } from "@/lib/api/uploads";
import { IngestionStatusCard } from "@/components/clients/ingestion-status-card";

export function IngestionFeed({
  clientId,
  recent,
}: {
  clientId: string;
  recent: IngestionJob[];
}) {
  const [jobs, setJobs] = useState<IngestionJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listUploads(clientId)
      .then((data) => {
        if (!cancelled) setJobs(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [clientId]);

  if (error) return <p className="text-sm text-red-600">Failed to load: {error}</p>;
  if (jobs === null) return <p className="text-sm text-gray-500">Loading…</p>;

  // Merge in any just-created jobs (from the form) that aren't in the fetched list yet
  const fetchedIds = new Set(jobs.map((j) => j.id));
  const merged = [...recent.filter((r) => !fetchedIds.has(r.id)), ...jobs];

  if (merged.length === 0) {
    return (
      <p className="text-sm text-gray-600">
        No uploads yet. Drop a transcript or voice memo above and the pipeline
        will run automatically.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {merged.map((j) => (
        <li key={j.id}>
          <IngestionStatusCard job={j} clientId={clientId} />
        </li>
      ))}
    </ul>
  );
}
