export function GalleryHeader({ online, local = false }: { online: boolean; local?: boolean }) {
  return <header className="gallery-header">
    <div>
      <h1>Ghostbusters</h1>
      <p>{local
        ? "A live feed of trick-or-treaters’ costumes, classified locally."
        : "A live feed of trick-or-treaters’ costumes, classified by NVIDIA Nemotron 3.5 Super VL on Baseten."}</p>
    </div>
    <div className="gallery-status">
      {local && <span>Local gallery</span>}
      <span role="status"><i className={online ? 'is-connected' : ''} />{online ? "Live" : "Offline"}</span>
      {!online && <span className="offline-note">Ghostbusters is currently offline.<br />Check back October 31 at 3pm PT.</span>}
    </div>
  </header>;
}
