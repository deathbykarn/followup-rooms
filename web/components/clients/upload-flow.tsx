"use client";

import { useState } from "react";
import { type IngestionJob } from "@/lib/api/uploads";
import { UploadForm } from "@/components/clients/upload-form";
import { IngestionFeed } from "@/components/clients/ingestion-feed";

export function UploadFlow({ clientId }: { clientId: string }) {
  const [recent, setRecent] = useState<IngestionJob[]>([]);

  return (
    <div className="space-y-8">
      <UploadForm
        clientId={clientId}
        onCreated={(job) => setRecent((prev) => [job, ...prev])}
      />

      <section>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Recent uploads</h4>
        <IngestionFeed clientId={clientId} recent={recent} />
      </section>
    </div>
  );
}
