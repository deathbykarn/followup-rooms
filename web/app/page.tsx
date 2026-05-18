import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

export default async function LandingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl text-center p-8">
        <h1 className="text-4xl font-semibold mb-4">FollowRoom</h1>
        <p className="text-lg text-gray-600 mb-8">
          Living relationship rooms for the operator who refuses to let
          clients fall through the cracks.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/signup">
            <Button size="lg">Get started</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">Log in</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
