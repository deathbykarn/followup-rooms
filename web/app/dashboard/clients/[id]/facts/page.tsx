import { FactsList } from "@/components/facts/facts-list";

export default async function FactsTabPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Facts</h3>
      <FactsList clientId={id} />
    </div>
  );
}
