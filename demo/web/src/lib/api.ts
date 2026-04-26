import type { TaskSpec } from "@/types/taskspec";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8765";

export async function submitIntent(userText: string): Promise<TaskSpec> {
  const res = await fetch(`${API_URL}/api/intent`, {
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
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}
