async function getHealth() {
  const base = process.env.API_BASE || "http://localhost:8000";
  try {
    const r = await fetch(`${base}/health`, { cache: "no-store" });
    return await r.json();
  } catch (e) {
    return { status: "unreachable", error: String(e) };
  }
}

export default async function Home() {
  const h = await getHealth();
  return (
    <main style={{ padding: 32, maxWidth: 900 }}>
      <h1 style={{ marginBottom: 4 }}>Nyra Service Tool</h1>
      <p style={{ color: "#666", marginTop: 0 }}>Agent workspace - day 1 scaffold (UI lands day 7)</p>
      <h3>API status</h3>
      <pre style={{ background: "#f4f4f5", padding: 12, borderRadius: 6 }}>{JSON.stringify(h, null, 2)}</pre>
      <p style={{ color: "#666", fontSize: 14 }}>
        Queue, incident workbench, bulk actions and macros arrive on day 7 of the 14-day plan.
      </p>
    </main>
  );
}
