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
      <span role="status" className="status-pill" title={online ? undefined : "Ghostbusters is currently offline. Check back October 31 at 3pm PT."}>
        <i className={online ? 'is-connected' : ''} />
        {online ? "Live" : <>Offline<span className="status-sep" aria-hidden>·</span><span className="status-return">Back Oct 31, 3pm PT</span></>}
      </span>
    </div>
  </header>;
}
