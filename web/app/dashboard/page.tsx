import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function DashboardHome() {
  const supabase = await createClient();
  const { data: clients } = await supabase
    .from("clients")
    .select("id, client_name, short_context, status, created_at")
    .eq("is_deleted", false)
    .order("created_at", { ascending: false });

  const hasClients = clients && clients.length > 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-semibold">
          {hasClients ? "Your clients" : "Welcome to FollowRoom"}
        </h2>
        <Link href="/dashboard/clients/new">
          <Button>Add client</Button>
        </Link>
      </div>

      {!hasClients ? (
        <div className="bg-white rounded-lg border p-12 text-center">
          <p className="text-gray-600 mb-6">
            Add your first client to start building their relationship room.
          </p>
          <Link href="/dashboard/clients/new">
            <Button>Add your first client</Button>
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {clients.map((c) => (
            <li key={c.id}>
              <Link
                href={`/dashboard/clients/${c.id}`}
                className="block bg-white rounded-lg border p-4 hover:border-gray-400 hover:shadow-sm transition"
              >
                <h3 className="font-medium">{c.client_name}</h3>
                <p className="text-sm text-gray-600 mt-1">{c.short_context}</p>
                <p className="text-xs text-gray-500 mt-2">
                  Status: {c.status}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
