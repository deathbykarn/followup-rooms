"use client";

import { useState } from "react";
import {
  confirmForward,
  discardForward,
  type PendingForward,
} from "@/lib/api/pending-forwards";
import { Button } from "@/components/ui/button";
import { ClientPicker } from "@/components/whatsapp/client-picker";

export function PendingForwardCard({
  forward,
  onChanged,
}: {
  forward: PendingForward;
  onChanged?: (updated: PendingForward) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickedClientId, setPickedClientId] = useState<string | null>(null);

  async function handleConfirm(clientId: string) {
    setBusy(true);
    setError(null);
    try {
      const updated = await confirmForward(forward.id, clientId);
      onChanged?.(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleDiscard() {
    setBusy(true);
    setError(null);
    try {
      const updated = await discardForward(forward.id);
      onChanged?.(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Discard failed");
    } finally {
      setBusy(false);
    }
  }

  const isPending = forward.state === "pending";

  return (
    <article className="bg-white rounded-lg border p-4 space-y-3">
      <header className="flex justify-between items-start">
        <div className="flex-1">
          <p className="text-xs text-gray-500">
            Forwarded by +{forward.sender_wa_id} ·{" "}
            {new Date(forward.created_at).toLocaleString()}
          </p>
          {forward.caption_text && (
            <p className="text-sm text-gray-700 mt-1">
              <span className="text-xs text-gray-500">Caption: </span>
              <span className="font-medium">{forward.caption_text}</span>
            </p>
          )}
        </div>
        {forward.state !== "pending" && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
            {forward.state}
          </span>
        )}
      </header>

      <div className="bg-gray-50 rounded p-3 text-sm whitespace-pre-wrap">
        {forward.forwarded_text}
      </div>

      {forward.suggested_client_name && isPending && !pickerOpen && (
        <div className="text-sm">
          <p className="text-gray-700">
            Suggested:{" "}
            <span className="font-medium">{forward.suggested_client_name}</span>
            {forward.suggested_confidence !== null && (
              <span className="text-xs text-gray-500 ml-1">
                ({Math.round(forward.suggested_confidence * 100)}% confidence)
              </span>
            )}
          </p>
        </div>
      )}

      {isPending && (
        <div className="flex gap-2 items-start flex-wrap">
          {forward.suggested_client_id && !pickerOpen && (
            <Button
              type="button"
              size="sm"
              disabled={busy}
              onClick={() => handleConfirm(forward.suggested_client_id as string)}
            >
              Confirm {forward.suggested_client_name}
            </Button>
          )}
          {!pickerOpen ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => setPickerOpen(true)}
            >
              {forward.suggested_client_id ? "Change" : "Pick client"}
            </Button>
          ) : (
            <div className="flex gap-2 items-center flex-1 min-w-0">
              <div className="flex-1 min-w-0">
                <ClientPicker value={pickedClientId} onChange={setPickedClientId} />
              </div>
              <Button
                type="button"
                size="sm"
                disabled={!pickedClientId || busy}
                onClick={() => handleConfirm(pickedClientId as string)}
              >
                Confirm
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setPickerOpen(false);
                  setPickedClientId(null);
                }}
              >
                Cancel
              </Button>
            </div>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={handleDiscard}
          >
            Discard
          </Button>
        </div>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}
    </article>
  );
}
