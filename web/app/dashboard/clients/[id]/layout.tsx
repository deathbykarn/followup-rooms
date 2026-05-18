import { notFound } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

const TABS = [
  { href: "", label: "Overview" },
  { href: "/add-note", label: "Add note" },
  { href: "/facts", label: "Facts" },
  { href: "/profile", label: "Profile" },
];

export default async function ClientDetailLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: client } = await supabase
    .from("clients")
    .select("id, client_name, short_context, status, relationship_type")
    .eq("id", id)
    .eq("is_deleted", false)
    .maybeSingle();

  if (!client) {
    notFound();
  }

  const basePath = `/dashboard/clients/${id}`;

  return (
    <div>
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          ← Back to clients
        </Link>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-semibold">{client.client_name}</h2>
        <p className="text-sm text-gray-600 mt-1">{client.short_context}</p>
        <p className="text-xs text-gray-500 mt-2">
          {client.relationship_type} · {client.status}
        </p>
      </div>

      <nav className="border-b mb-6">
        <ul className="flex gap-6">
          {TABS.map((tab) => (
            <li key={tab.href}>
              <Link
                href={`${basePath}${tab.href}`}
                className="inline-block py-3 text-sm text-gray-700 hover:text-gray-900 border-b-2 border-transparent hover:border-gray-300"
              >
                {tab.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div>{children}</div>
    </div>
  );
}
