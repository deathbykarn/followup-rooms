import { NewClientForm } from "@/components/clients/new-client-form";

export default function NewClientPage() {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Add a client</h2>
      <NewClientForm />
    </div>
  );
}
