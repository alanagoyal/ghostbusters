"use client";
import { GalleryHeader } from "@/components/dashboard/gallery-header";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { CostumeDistribution } from "@/components/dashboard/costume-distribution";
import { useEffect, useRef, useState } from "react";

type Detection = {
  id: string;
  created: number;
  state: string;
  costume: string | null;
  description: string | null;
  image_url: string;
  error: string | null;
};
type Health = {
  state: string;
  updated: number;
  action?: string;
  last_frame?: number;
  retention_days?: number;
};
type Snapshot = {
  detections: Detection[];
  total: number;
  recent: number;
  health: Record<string, Health>;
};

export function LocalGallery() {
  const [selected, setSelected] = useState<Detection | null>(null);
  const [filter, setFilter] = useState("");
  const [data, setData] = useState<Snapshot | null>(null);
  const [connection, setConnection] = useState("Connecting");
  const [error, setError] = useState("");
  const [now, setNow] = useState(Date.now());
  // A ref survives React's development effect replay; the effect keeps a local
  // copy so a transient session POST does not lose the removed URL fragment.
  const pendingToken = useRef<string | null>(null);
  useEffect(() => {
    let token =
      pendingToken.current ??
      new URLSearchParams(location.hash.slice(1)).get("token");
    pendingToken.current = token;
    if (token) history.replaceState(null, "", location.pathname);
    let events: EventSource | undefined;
    let cancelled = false;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    async function connect() {
      try {
        if (token) {
          const response = await fetch("/api/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token }),
          });
          if (!response.ok) {
            if (response.status === 401) {
              token = null;
              pendingToken.current = null;
              throw Error(
                "This private gallery link is invalid. Ask your agent for a fresh link.",
              );
            }
            throw Error(
              "Gallery sign-in is temporarily unavailable. Retrying automatically.",
            );
          }
          token = null;
          pendingToken.current = null;
        }
        if (cancelled) return;
        const response = await fetch("/api/status");
        if (!response.ok)
          throw Error(
            response.status === 401
              ? "Open the private gallery link provided by your agent to view this installation."
              : "The local gallery service is unavailable.",
          );
        const initial = await response.json();
        if (cancelled) return;
        setData(initial);
        setError("");
        events = new EventSource("/api/events");
        events.addEventListener("status", (event) => {
          setData(JSON.parse((event as MessageEvent).data));
          setConnection("Connected");
          setError("");
        });
        events.onerror = () => {
          setConnection("Reconnecting");
          setError(
            "Connection interrupted. Retrying automatically; displayed records may be stale.",
          );
        };
      } catch (e) {
        if (!cancelled) {
          setConnection("Disconnected");
          setError((e as Error).message);
          retry = setTimeout(
            connect,
            Math.min(15000, 1000 * 2 ** Math.min(attempts++, 4)),
          );
        }
      }
    }
    connect();
    const timer = setInterval(() => setNow(Date.now()), 3000);
    return () => {
      cancelled = true;
      events?.close();
      clearInterval(timer);
      if (retry) clearTimeout(retry);
    };
  }, []);
  const costumes = Object.entries(
    (data?.detections ?? []).reduce<Record<string, number>>((counts, d) => {
      if (d.state === "complete" && d.costume)
        counts[d.costume] = (counts[d.costume] ?? 0) + 1;
      return counts;
    }, {}),
  )
    .map(([name, count]) => ({
      name,
      fullName: name,
      count,
      descriptions: [],
      percentage:
        (100 * count) /
        Math.max(
          1,
          data?.detections.filter((d) => d.state === "complete").length ?? 0,
        ),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
  return (
    <main className="observatory">
      <GalleryHeader connected={connection === "Connected"} status={connection} local />
      <p className="text-muted-foreground mb-6">
        Photos and costume guesses stay on this computer. Cloud upload is off.
        Counts are detections, not unique people; a visitor may appear again.
      </p>
      {error && (
        <p
          role="alert"
          className="border border-orange-500 rounded-xl p-4 mb-6"
        >
          {error}
        </p>
      )}
      <section
        aria-label="System health"
        className="local-health grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        {["service", "capture", "model", "storage"].map((name) => {
          const health = data?.health[name];
          const stale = health && now - health.updated * 1000 > 60000;
          return (
            <div key={name} className="border rounded-xl p-4">
              <h2 className="capitalize text-sm text-muted-foreground">
                {name}
              </h2>
              <p className="font-semibold mt-1">
                {health
                  ? stale
                    ? "Status stale"
                    : health.state.replaceAll("_", " ")
                  : "Not reported"}
              </p>
              {health?.action && (
                <p className="text-xs mt-2">{health.action}</p>
              )}
            </div>
          );
        })}
      </section>
      <section className="local-totals mb-8">
        <div>
          <strong className="text-3xl">{data?.total ?? "—"}</strong>
          <p>Total retained detections</p>
        </div>
        <div>
          <strong className="text-3xl">{data?.recent ?? "—"}</strong>
          <p>In the last 5 minutes</p>
        </div>
        <div>
          <strong className="text-3xl">{data?.detections.length ?? "—"}</strong>
          <p>Most recent shown (up to 200)</p>
        </div>
      </section>
      {data && data.detections.length === 0 && (
        <section className="rounded-2xl border border-dashed p-12 text-center">
          <h2 className="text-2xl mb-3">No detections yet</h2>
          <p>
            {data.health.capture?.state === "streaming"
              ? "The camera is streaming. A person needs to enter the selected region before a photo appears."
              : "Check capture health above. Your agent can verify the camera, local streaming permission and selected region."}
          </p>
        </section>
      )}
      <label className="block mb-6 text-xs">
        Filter recent photos
        <input
          className="block mt-2 border rounded-lg p-3 bg-background w-full max-w-md"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Costume or classification state"
        />
      </label>
      <section
        aria-label="Costume photos"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {data?.detections
          .filter((d) =>
            `${d.costume} ${d.description} ${d.state}`
              .toLowerCase()
              .includes(filter.toLowerCase()),
          )
          .map((d) => (
            <article key={d.id} className="local-photo border overflow-hidden">
              <button
                className="w-full"
                onClick={() => setSelected(d)}
                aria-label="Open photo"
              >
                <img
                  src={d.image_url}
                  alt={
                    d.description ||
                    "Detected person awaiting costume classification"
                  }
                  className="w-full h-80 object-contain bg-black/10"
                />
              </button>
              <div className="p-5">
                <p className="text-xs text-muted-foreground">
                  {new Date(d.created * 1000).toLocaleString()}
                </p>
                <h2 className="text-xl font-semibold mt-2">
                  {d.costume ||
                    {
                      pending: "Waiting for model",
                      processing: "Classifying…",
                      retry: "Retrying classification",
                      failed: "Classification failed",
                      queue_full: "Saved — classification queue full",
                    }[d.state] ||
                    "Unclassified"}
                </h2>
                <p className="mt-2">
                  {d.description || "The photo is saved locally."}
                </p>
                <p className="text-xs text-muted-foreground mt-3">
                  {d.state === "complete"
                    ? "Model guess · may be wrong"
                    : d.state.replaceAll("_", " ")}
                </p>
              </div>
            </article>
          ))}
      </section>
      <section className="mt-8 grid lg:grid-cols-2 gap-6">
        <CostumeDistribution costumes={costumes} />
        <ActivityTimeline
          detections={(data?.detections ?? []).map((d) => ({
            timestamp: new Date(d.created * 1000).toISOString(),
          }))}
        />
      </section>
      <p className="text-xs text-muted-foreground mt-3">
        Charts summarize the most recent 200 retained detections.
      </p>
      {selected && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Photo detail"
          className="fixed inset-0 z-50 bg-black/90 p-8 flex flex-col items-center justify-center"
          onClick={() => setSelected(null)}
        >
          <button
            autoFocus
            className="text-white mb-4 border px-4 py-2"
            onClick={() => setSelected(null)}
          >
            Close photo
          </button>
          <img
            className="max-h-[75vh] max-w-full object-contain"
            src={selected.image_url}
            alt={selected.description || "Detection"}
          />
          <p className="text-white mt-4">{selected.description}</p>
        </div>
      )}
      <footer className="mt-12 text-sm text-muted-foreground">
        Retention: {data?.health.storage?.retention_days ?? 7} days, also
        limited by the configured disk budget. Oldest records are removed first.
        Times use your browser’s timezone. Keep the private gallery link
        private.
      </footer>
    </main>
  );
}
