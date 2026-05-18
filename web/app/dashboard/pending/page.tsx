"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listPending, type PendingForward } from "@/lib/api/pending-forwards";
import { PendingForwardCard } from "@/components/whatsapp/pending-forward-card";

const POLL_MS = 10000;

export default function PendingPage() {
  const [items, setItems] = useState<PendingForward[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setItems(await listPending(true));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          ← Back to dashboard
        </Link>
      </div>

      <h2 className="text-2xl font-semibold mb-2">Pending forwards</h2>
      <p className="text-sm text-gray-600 mb-6">
        WhatsApp forwards waiting for client attribution. Confirm one to drop
        it into a client&apos;s KB; discard to ignore.
      </p>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {items === null && !error && (
        <p className="text-sm text-gray-500">Loading…</p>
      )}

      {items !== null && items.length === 0 && (
        <p className="text-sm text-gray-600">
          No pending forwards. Forward a client message to your linked WhatsApp
          number with a name as the caption (e.g. &quot;Sarah Tan&quot;).{" "}
          <Link
            href="/dashboard/settings/whatsapp"
            className="text-blue-600 hover:underline"
          >
            Set up WhatsApp linking →
          </Link>
        </p>
      )}

      {items !== null && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((f) => (
            <li key={f.id}>
              <PendingForwardCard
                forward={f}
                onChanged={() => refresh()}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
