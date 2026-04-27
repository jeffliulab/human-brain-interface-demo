import type { TaskSpec } from "@/types/taskspec";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export async function submitIntent(userText: string): Promise<TaskSpec> {
  const res = await fetch(`${BASE}/api/intent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_text: userText }),
  });
  if (!res.ok) {
    throw new Error(`intent failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; model: string }> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
