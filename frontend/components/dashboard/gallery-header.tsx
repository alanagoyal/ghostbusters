import type { ReactNode } from "react";

export function GalleryHeader({ online, local = false, connection = "Offline", children }: { online: boolean; local?: boolean; connection?: string; children?: ReactNode }) {
  return <header className="gallery-header">
    <div>
      <h1>Ghostbusters</h1>
      <p>{local
        ? "A live feed of trick-or-treaters’ costumes, classified locally."
        : "A live feed of trick-or-treaters’ costumes."}</p>
    </div>
    <div className="gallery-status">
      {local && <span>Local gallery</span>}
      <span role="status" className="status-pill" title={online || local ? undefined : "The camera is currently offline."}>
        <i className={online ? 'is-connected' : ''} />
        {online ? "Live" : local ? (connection === "Connected" ? "Camera offline" : connection) : "Offline"}
      </span>
      {children}
    </div>
  </header>;
}
