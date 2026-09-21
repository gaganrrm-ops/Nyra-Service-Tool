async function getMeta() {
  const base = process.env.API_BASE || "http://localhost:8000";
  try {
    const r = await fetch(`${base}/api/v1/meta/summary`, { cache: "no-store" });
    return await r.json();
  } catch (e) {
    return { status: "unreachable" };
  }
}

export default async function Home() {
  const m = await getMeta();
  return (
    <main style={{ padding: 32, maxWidth: 900 }}>
      <h1 style={{ marginBottom: 4 }}>Nyra Help Centre</h1>
      <p style={{ color: "#666", marginTop: 0 }}>End-user portal - day 1 scaffold (submit/track/self-help land day 10-11)</p>
      <pre style={{ background: "#f4f4f5", padding: 12, borderRadius: 6 }}>{JSON.stringify(m, null, 2)}</pre>
    </main>
  );
}
