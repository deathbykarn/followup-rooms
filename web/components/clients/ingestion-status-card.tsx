"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getUpload, type IngestionJob, type IngestionState } from "@/lib/api/uploads";

const STATE_LABEL: Record<IngestionState, string> = {
  queued: "Queued",
  transcribing: "Transcribing",
  extracting: "Extracting facts",
  done: "Done",
  failed: "Failed",
};

const STATE_COLOR: Record<IngestionState, string> = {
  queued: "bg-gray-100 text-gray-700",
  transcribing: "bg-amber-100 text-amber-800",
  extracting: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-700",
};

const TERMINAL: ReadonlySet<IngestionState> = new Set(["done", "failed"]);
const POLL_MS = 3000;

export function IngestionStatusCard({
  job,
  clientId,
  onTerminal,
}: {
  job: IngestionJob;
  clientId: string;
  onTerminal?: (final: IngestionJob) => void;
}) {
  const [current, setCurrent] = useState<IngestionJob>(job);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setCurrent(job);
  }, [job]);

  useEffect(() => {
    if (TERMINAL.has(current.state)) {
      onTerminal?.(current);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const next = await getUpload(current.id);
        setCurrent(next);
      } catch {
        // transient — keep the current state, retry on next poll
      }
    }, POLL_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [current, onTerminal]);

  const elapsedSec = Math.max(
    0,
    Math.floor(
      (new Date().getTime() - new Date(current.created_at).getTime()) / 1000,
    ),
  );

  return (
    <article className="bg-white rounded-lg border p-4">
      <header className="flex justify-between items-start mb-2">
        <div>
          <p className="font-medium text-sm">{current.original_filename}</p>
          <p className="text-xs text-gray-500 mt-1">
            {current.upload_type === "transcript" ? "Transcript" : "Voice memo"} ·{" "}
            {(current.size_bytes / 1024).toFixed(0)} KB · {elapsedSec}s
          </p>
        </div>
        <span
          className={`px-2 py-0.5 text-xs rounded-full ${STATE_COLOR[current.state]}`}
        >
          {STATE_LABEL[current.state]}
        </span>
      </header>

      {current.state === "failed" && current.error_message && (
        <p className="text-xs text-red-600 mt-2">{current.error_message}</p>
      )}

      {current.state === "done" && (
        <p className="text-xs text-gray-600 mt-2">
          Facts extracted.{" "}
          <Link
            href={`/dashboard/clients/${clientId}/facts`}
            className="text-blue-600 hover:underline"
          >
            Review on Facts tab →
          </Link>
        </p>
      )}
    </article>
  );
}
