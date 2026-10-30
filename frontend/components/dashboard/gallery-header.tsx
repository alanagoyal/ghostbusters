import type { ReactNode } from "react";
import { galleryCopy } from "@/lib/gallery-copy";

export function GalleryHeader({ online, local = false, connection = "Offline", children }: { online: boolean; local?: boolean; connection?: string; children?: ReactNode }) {
  return <header className="gallery-header">
    <div>
      <h1>Ghostbusters</h1>
      <p>{local
        ? "A live feed of trick-or-treaters’ costumes, classified locally."
        : galleryCopy.subtitle}</p>
    </div>
    <div className="gallery-status">
      {local && <span>Local gallery</span>}
      <span role="status" className="status-pill" title={online || local ? undefined : galleryCopy.offlineMessage || "The camera is currently offline."}>
        <i className={online ? 'is-connected' : ''} />
        {online ? "Live" : local ? (connection === "Connected" ? "Camera offline" : connection) : <>Offline{galleryCopy.offlineMessage && <><span className="status-sep" aria-hidden>·</span><span className="status-return">{galleryCopy.offlineMessage}</span></>}</>}
      </span>
      {children}
    </div>
  </header>;
}
