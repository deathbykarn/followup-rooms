export const dynamic = "force-dynamic";

export default async function RoomPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Plan 6 implements the full room rendering. Placeholder confirms
  // routing + proxy exclusion works end-to-end.
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center p-8">
        <h1 className="text-2xl font-semibold mb-2">FollowRoom</h1>
        <p className="text-gray-600">
          Room <code className="font-mono text-sm">{slug}</code> is coming soon.
        </p>
      </div>
    </div>
  );
}
