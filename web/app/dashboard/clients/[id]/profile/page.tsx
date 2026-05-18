import { ProfileViewer } from "@/components/profile/profile-view";

export default async function ProfileTabPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Profile</h3>
      <ProfileViewer clientId={id} />
    </div>
  );
}
