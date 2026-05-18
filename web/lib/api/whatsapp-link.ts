import { callBackend } from "@/lib/api/backend";

export type LinkStatus = {
  is_linked: boolean;
  wa_id: string | null;
  linked_at: string | null;
};

export type LinkCode = {
  code: string;
  expires_at: string;
  whatsapp_number: string;
  instructions: string;
};

export function getLinkStatus(): Promise<LinkStatus> {
  return callBackend<LinkStatus>("/whatsapp/link-status");
}

export function issueLinkCode(): Promise<LinkCode> {
  return callBackend<LinkCode>("/whatsapp/link-code", { method: "POST" });
}
