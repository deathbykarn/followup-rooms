"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { createUpload, type IngestionJob, type UploadType } from "@/lib/api/uploads";
import { Button } from "@/components/ui/button";

const TEXT_MIMES = {
  "text/plain": [".txt"],
  "text/vtt": [".vtt"],
  "application/x-subrip": [".srt"],
} as const;

const AUDIO_MIMES = {
  "audio/mpeg": [".mp3"],
  "audio/mp4": [".m4a", ".mp4"],
  "audio/x-m4a": [".m4a"],
  "audio/wav": [".wav"],
  "audio/x-wav": [".wav"],
  "audio/ogg": [".ogg"],
  "audio/webm": [".webm"],
  "audio/aac": [".aac"],
} as const;

export function UploadForm({
  clientId,
  onCreated,
}: {
  clientId: string;
  onCreated: (job: IngestionJob) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadType, setUploadType] = useState<UploadType>("transcript");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { ...TEXT_MIMES, ...AUDIO_MIMES },
    maxSize: 100 * 1024 * 1024,
    multiple: false,
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const job = await createUpload(file, clientId, uploadType);
      onCreated(job);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <div className="flex gap-4 text-sm">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="upload_type"
            value="transcript"
            checked={uploadType === "transcript"}
            onChange={() => setUploadType("transcript")}
          />
          <span>
            <strong>Transcript</strong> (multi-party meeting; uses speaker labels)
          </span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="upload_type"
            value="voice_memo"
            checked={uploadType === "voice_memo"}
            onChange={() => setUploadType("voice_memo")}
          />
          <span>
            <strong>Voice memo</strong> (your own reflection; single speaker)
          </span>
        </label>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          isDragActive
            ? "border-gray-700 bg-gray-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div>
            <p className="font-medium">{file.name}</p>
            <p className="text-xs text-gray-500 mt-1">
              {(file.size / 1024).toFixed(1)} KB · {file.type || "unknown type"}
            </p>
          </div>
        ) : isDragActive ? (
          <p className="text-sm text-gray-700">Drop the file here…</p>
        ) : (
          <div className="text-sm text-gray-600">
            <p>Drop a transcript or voice memo here, or click to pick a file.</p>
            <p className="text-xs text-gray-500 mt-2">
              Accepted: .txt / .vtt / .srt for transcripts ·
              .mp3 / .m4a / .wav / .ogg / .webm for audio · max 100MB
            </p>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button type="submit" disabled={!file || busy}>
        {busy ? "Uploading…" : "Upload"}
      </Button>
    </form>
  );
}
