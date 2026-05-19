"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

type ClientOption = { id: string; client_name: string };

export function ClientPicker({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (clientId: string) => void;
}) {
  const [options, setOptions] = useState<ClientOption[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase
      .from("clients")
      .select("id, client_name")
      .eq("is_deleted", false)
      .order("client_name")
      .then(({ data, error: err }) => {
        if (err) setError(err.message);
        else setOptions(data || []);
      });
  }, []);

  if (error) return <p className="text-xs text-red-600">{error}</p>;
  if (options === null) return <p className="text-xs text-gray-500">Loading clients…</p>;
  if (options.length === 0) {
    return <p className="text-xs text-gray-600">No clients yet — add one first.</p>;
  }

  return (
    <select
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      className="border rounded-md px-2 py-1 text-sm w-full"
    >
      <option value="">Pick a client…</option>
      {options.map((c) => (
        <option key={c.id} value={c.id}>
          {c.client_name}
        </option>
      ))}
    </select>
  );
}
