export function GalleryHeader({ connected, status, local = false }: { connected: boolean; status?: string; local?: boolean }) {
  return <header className="gallery-header">
    <div>
      <h1>Ghostbusters</h1>
      <p>{local
        ? "A live feed of trick-or-treaters’ costumes, classified locally."
        : "A live feed of trick-or-treaters’ costumes, classified by Gemma on Baseten."}</p>
    </div>
    <div className="gallery-status">
      {local && <span>Local gallery</span>}
      <span role="status"><i className={connected ? 'is-connected' : ''} />{status || (connected ? 'Connected' : 'Connecting / offline')}</span>
    </div>
  </header>;
}
