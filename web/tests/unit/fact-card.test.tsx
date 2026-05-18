import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FactCard } from "@/components/facts/fact-card";
import type { Fact } from "@/lib/api/facts";

vi.mock("@/lib/api/facts", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/facts")>(
    "@/lib/api/facts",
  );
  return {
    ...actual,
    updateStance: vi.fn(),
  };
});

import { updateStance } from "@/lib/api/facts";

function makeFact(overrides: Partial<Fact> = {}): Fact {
  return {
    id: "f1",
    client_id: "c1",
    type: "property_preference",
    value: "Marine Parade preferred",
    confidence_score: 0.9,
    visibility: "operator_only",
    provenance: "llm_generated",
    user_stance: "unreviewed",
    source_event_ids: ["e1"],
    source_spans: [{ event_id: "e1", snippet: "wants Marine Parade" }],
    superseded_by: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("FactCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the fact type, value, and confidence", () => {
    render(<FactCard fact={makeFact()} />);
    expect(screen.getByText("Marine Parade preferred")).toBeInTheDocument();
    expect(screen.getByText(/property preference/i)).toBeInTheDocument();
    expect(screen.getByText(/conf 90%/i)).toBeInTheDocument();
  });

  it("shows Accept/Reject buttons for unreviewed facts", () => {
    render(<FactCard fact={makeFact()} />);
    expect(screen.getByRole("button", { name: /accept/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reject/i })).toBeInTheDocument();
  });

  it("does NOT show Accept/Reject for already-accepted facts", () => {
    render(<FactCard fact={makeFact({ user_stance: "accepted" })} />);
    expect(screen.queryByRole("button", { name: /accept/i })).not.toBeInTheDocument();
  });

  it("calls updateStance and notifies onChanged when Accept clicked", async () => {
    const onChanged = vi.fn();
    const updatedFact = makeFact({ user_stance: "accepted" });
    vi.mocked(updateStance).mockResolvedValue(updatedFact);

    render(<FactCard fact={makeFact()} onChanged={onChanged} />);
    fireEvent.click(screen.getByRole("button", { name: /accept/i }));

    await waitFor(() => {
      expect(updateStance).toHaveBeenCalledWith("f1", "accepted", undefined);
      expect(onChanged).toHaveBeenCalledWith(updatedFact);
    });
  });
});
