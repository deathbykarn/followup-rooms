import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function ClientOverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: events } = await supabase
    .from("events")
    .select("id, source_type, raw_text, created_at")
    .eq("client_id", id)
    .order("created_at", { ascending: false })
    .limit(10);

  const hasEvents = events && events.length > 0;

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-lg font-medium mb-3">Recent events</h3>
        {!hasEvents ? (
          <div className="bg-white rounded-lg border p-6 text-center text-sm text-gray-600">
            No events yet. Use the <strong>Add note</strong> tab to record your first
            conversation or observation.
          </div>
        ) : (
          <ul className="space-y-3">
            {events.map((e) => (
              <li key={e.id} className="bg-white rounded-lg border p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-medium text-gray-500 uppercase">
                    {e.source_type.replace("_", " ")}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(e.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-gray-800 whitespace-pre-wrap line-clamp-4">
                  {e.raw_text}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
