"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function NewClientForm() {
  const [clientName, setClientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [shortContext, setShortContext] = useState("");
  const [relationshipType, setRelationshipType] = useState("buyer");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (shortContext.trim().length < 20) {
      setError(
        "Short context must be at least 20 characters — give us enough to start. " +
          "Example: 'HDB upgrade, East Coast, ~$1.8M, husband in finance.'",
      );
      return;
    }

    setLoading(true);

    const supabase = createClient();
    const { error: dbError } = await supabase.from("clients").insert({
      client_name: clientName,
      phone_number: phoneNumber || null,
      relationship_type: relationshipType,
      short_context: shortContext,
    });

    setLoading(false);

    if (dbError) {
      setError(dbError.message);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl">
      <div className="space-y-2">
        <Label htmlFor="client_name">Client name *</Label>
        <Input
          id="client_name"
          required
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone_number">Phone number (optional)</Label>
        <Input
          id="phone_number"
          type="tel"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          placeholder="+65 9123 4567"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="relationship_type">Relationship type</Label>
        <select
          id="relationship_type"
          value={relationshipType}
          onChange={(e) => setRelationshipType(e.target.value)}
          className="w-full border rounded-md px-3 py-2"
        >
          <option value="buyer">Buyer</option>
          <option value="seller">Seller</option>
          <option value="landlord">Landlord</option>
          <option value="tenant">Tenant</option>
          <option value="investor">Investor</option>
          <option value="commercial_landlord">Commercial landlord</option>
          <option value="commercial_tenant">Commercial tenant</option>
          <option value="referral_partner">Referral partner</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="short_context">
          Short context *{" "}
          <span className="text-xs text-gray-500">(min 20 chars)</span>
        </Label>
        <Textarea
          id="short_context"
          required
          minLength={20}
          rows={3}
          value={shortContext}
          onChange={(e) => setShortContext(e.target.value)}
          placeholder="e.g., HDB upgrade, East Coast, ~$1.8M, husband in finance. Wife's family in Marine Parade."
        />
        <p className="text-xs text-gray-500">
          A few sentences about who they are and what they want. This seeds the
          relationship memory — the richer the seed, the smarter the room from day one.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex gap-3">
        <Button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create client"}
        </Button>
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
