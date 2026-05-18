import Link from "next/link";
import { LinkInstructions } from "@/components/whatsapp/link-instructions";

export default async function WhatsAppSettingsPage() {
  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          ← Back to dashboard
        </Link>
      </div>

      <h2 className="text-2xl font-semibold mb-2">WhatsApp linking</h2>
      <p className="text-sm text-gray-600 mb-6">
        Connect your WhatsApp so forwarded client messages flow into FollowRoom.
      </p>

      <LinkInstructions />
    </div>
  );
}
