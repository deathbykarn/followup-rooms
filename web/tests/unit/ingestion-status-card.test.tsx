import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { IngestionStatusCard } from "@/components/clients/ingestion-status-card";
import type { IngestionJob } from "@/lib/api/uploads";

vi.mock("@/lib/api/uploads", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/uploads")>(
    "@/lib/api/uploads",
  );
  return { ...actual, getUpload: vi.fn() };
});

function makeJob(overrides: Partial<IngestionJob> = {}): IngestionJob {
  return {
    id: "job-1",
    client_id: "c1",
    upload_type: "transcript",
    original_filename: "viewing.txt",
    mime_type: "text/plain",
    size_bytes: 1024,
    state: "queued",
    error_message: null,
    error_code: null,
    transcript_text: null,
    event_id: null,
    transcription_metadata: {},
    started_at: null,
    completed_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("IngestionStatusCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders filename + size + state pill", () => {
    render(<IngestionStatusCard job={makeJob()} clientId="c1" />);
    expect(screen.getByText("viewing.txt")).toBeInTheDocument();
    expect(screen.getByText(/Queued/)).toBeInTheDocument();
    expect(screen.getByText(/1 KB/)).toBeInTheDocument();
  });

  it("shows Facts link when state=done", () => {
    render(
      <IngestionStatusCard
        job={makeJob({ state: "done", event_id: "evt-1" })}
        clientId="c1"
      />,
    );
    expect(screen.getByText(/Done/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review on Facts tab/ })).toHaveAttribute(
      "href",
      "/dashboard/clients/c1/facts",
    );
  });

  it("shows error message when state=failed", () => {
    render(
      <IngestionStatusCard
        job={makeJob({
          state: "failed",
          error_message: "AssemblyAI timed out after 60s",
          error_code: "transcription_failed",
        })}
        clientId="c1"
      />,
    );
    expect(screen.getByText(/Failed/)).toBeInTheDocument();
    expect(screen.getByText(/AssemblyAI timed out/)).toBeInTheDocument();
  });

  it("does NOT show Facts link in non-terminal states", () => {
    render(<IngestionStatusCard job={makeJob({ state: "transcribing" })} clientId="c1" />);
    expect(screen.queryByRole("link", { name: /Review on Facts tab/ })).not.toBeInTheDocument();
  });
});
