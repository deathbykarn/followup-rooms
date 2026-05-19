"use client";

import { useEffect, useState } from "react";
import { getLinkStatus, issueLinkCode, type LinkCode, type LinkStatus } from "@/lib/api/whatsapp-link";
import { Button } from "@/components/ui/button";

export function LinkInstructions() {
  const [status, setStatus] = useState<LinkStatus | null>(null);
  const [code, setCode] = useState<LinkCode | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLinkStatus().then(setStatus).catch((e: Error) => setError(e.message));
  }, []);

  async function handleIssue() {
    setBusy(true);
    setError(null);
    try {
      const next = await issueLinkCode();
      setCode(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate code");
    } finally {
      setBusy(false);
    }
  }

  if (status === null && !error) {
    return <p className="text-sm text-gray-500">Loading…</p>;
  }

  if (status?.is_linked && !code) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-md p-4 text-sm">
        <p className="font-medium text-green-900">WhatsApp linked</p>
        <p className="text-green-800 mt-1">
          Forwards from <code>+{status.wa_id}</code> arrive in your pending tray.
          {status.linked_at && (
            <> Linked since {new Date(status.linked_at).toLocaleDateString()}.</>
          )}
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-3"
          disabled={busy}
          onClick={handleIssue}
        >
          Re-link to a different WhatsApp number
        </Button>
        {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
      </div>
    );
  }

  if (code) {
    return (
      <div className="bg-white border-2 border-gray-900 rounded-md p-6 space-y-4">
        <div>
          <p className="text-xs uppercase text-gray-500 tracking-wide">Your link code</p>
          <p className="text-4xl font-mono font-bold mt-1 tracking-widest">{code.code}</p>
          <p className="text-xs text-gray-500 mt-1">
            Expires {new Date(code.expires_at).toLocaleTimeString()}
          </p>
        </div>
        <div className="text-sm text-gray-800 space-y-2">
          <p>
            Open WhatsApp on your phone and send this message to{" "}
            <strong>{code.whatsapp_number}</strong>:
          </p>
          <pre className="bg-gray-100 rounded px-3 py-2 font-mono text-sm">
            /link {code.code}
          </pre>
          <p className="text-xs text-gray-600">
            We&apos;ll match your WhatsApp number to your FollowRoom account. After
            that, anything you forward to <strong>{code.whatsapp_number}</strong> with
            a client name caption (e.g. &quot;Sarah Tan&quot;) shows up in your pending tray.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-700">
        Link your WhatsApp so you can forward client messages directly to
        FollowRoom. Forwards arrive in a pending tray; you confirm the client
        attribution with one click, then the extraction pipeline runs.
      </p>
      <Button type="button" onClick={handleIssue} disabled={busy}>
        {busy ? "Generating…" : "Generate link code"}
      </Button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
