import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PendingForwardCard } from "@/components/whatsapp/pending-forward-card";
import type { PendingForward } from "@/lib/api/pending-forwards";

vi.mock("@/lib/api/pending-forwards", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/pending-forwards")>(
    "@/lib/api/pending-forwards",
  );
  return {
    ...actual,
    confirmForward: vi.fn(),
    discardForward: vi.fn(),
  };
});

vi.mock("@/components/whatsapp/client-picker", () => ({
  ClientPicker: ({ onChange }: { onChange: (id: string) => void }) => (
    <button onClick={() => onChange("picked-client-id")}>__pick__</button>
  ),
}));

import { confirmForward, discardForward } from "@/lib/api/pending-forwards";

function makeForward(overrides: Partial<PendingForward> = {}): PendingForward {
  return {
    id: "p1",
    operator_id: "op-1",
    wa_message_id: "wamid.x",
    sender_wa_id: "6591234567",
    forwarded_text: "I want Marine Parade this weekend",
    caption_text: "Sarah",
    wa_timestamp: new Date().toISOString(),
    suggested_client_id: "c1",
    suggested_client_name: "Sarah Tan",
    suggested_confidence: 0.92,
    state: "pending",
    committed_client_id: null,
    committed_event_id: null,
    committed_at: null,
    discarded_reason: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("PendingForwardCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders forwarded text + caption + suggested client", () => {
    render(<PendingForwardCard forward={makeForward()} />);
    expect(screen.getByText("I want Marine Parade this weekend")).toBeInTheDocument();
    expect(screen.getByText("Sarah")).toBeInTheDocument();
    expect(screen.getByText("Sarah Tan")).toBeInTheDocument();
    expect(screen.getByText(/92% confidence/)).toBeInTheDocument();
  });

  it("Confirm-suggestion button calls confirmForward with suggested client_id", async () => {
    vi.mocked(confirmForward).mockResolvedValue(
      makeForward({ state: "confirmed" }),
    );
    const onChanged = vi.fn();
    render(<PendingForwardCard forward={makeForward()} onChanged={onChanged} />);

    fireEvent.click(screen.getByRole("button", { name: /Confirm Sarah Tan/i }));
    await waitFor(() => {
      expect(confirmForward).toHaveBeenCalledWith("p1", "c1");
      expect(onChanged).toHaveBeenCalled();
    });
  });

  it("Change opens picker and Confirm sends picked client_id", async () => {
    vi.mocked(confirmForward).mockResolvedValue(makeForward({ state: "confirmed" }));
    render(<PendingForwardCard forward={makeForward()} />);

    fireEvent.click(screen.getByRole("button", { name: /Change/i }));
    fireEvent.click(screen.getByText("__pick__"));
    fireEvent.click(screen.getByRole("button", { name: /^Confirm$/i }));

    await waitFor(() => {
      expect(confirmForward).toHaveBeenCalledWith("p1", "picked-client-id");
    });
  });

  it("Discard calls discardForward", async () => {
    vi.mocked(discardForward).mockResolvedValue(makeForward({ state: "discarded" }));
    render(<PendingForwardCard forward={makeForward()} />);

    fireEvent.click(screen.getByRole("button", { name: /Discard/i }));
    await waitFor(() => {
      expect(discardForward).toHaveBeenCalledWith("p1");
    });
  });

  it("does NOT show action buttons for non-pending states", () => {
    render(<PendingForwardCard forward={makeForward({ state: "confirmed" })} />);
    expect(screen.queryByRole("button", { name: /Confirm/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Discard/i })).not.toBeInTheDocument();
  });
});
