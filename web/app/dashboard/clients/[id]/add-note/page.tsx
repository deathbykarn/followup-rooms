import { AddNoteForm } from "@/components/clients/add-note-form";

export default async function AddNotePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Add a note</h3>
      <AddNoteForm clientId={id} />
    </div>
  );
}
