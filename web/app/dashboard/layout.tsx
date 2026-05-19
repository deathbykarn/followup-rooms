import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();

  // IMPORTANT: use getUser(), NOT getSession() — only getUser hits the
  // auth server and is trustworthy in server code (design doc §9.3).
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // Pending forwards count (server-side; RLS scopes to this operator)
  const { count: pendingCount } = await supabase
    .from("pending_forwards")
    .select("id", { count: "exact", head: true })
    .eq("state", "pending");

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">
            <Link href="/dashboard">FollowRoom</Link>
          </h1>
          <div className="flex items-center gap-4">
            {pendingCount !== null && pendingCount > 0 && (
              <Link
                href="/dashboard/pending"
                className="text-sm bg-amber-100 text-amber-900 px-2.5 py-1 rounded-full hover:bg-amber-200"
              >
                {pendingCount} pending forward{pendingCount === 1 ? "" : "s"}
              </Link>
            )}
            <Link
              href="/dashboard/settings/whatsapp"
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              WhatsApp
            </Link>
            <span className="text-sm text-gray-600">{user.email}</span>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
