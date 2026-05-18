import { UploadFlow } from "@/components/clients/upload-flow";

export default async function UploadTabPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Upload transcript or voice memo</h3>
      <UploadFlow clientId={id} />
    </div>
  );
}
