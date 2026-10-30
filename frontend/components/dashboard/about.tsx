const steps = [
  ["Capture", "A DoorBird doorbell streams video over RTSP. Every 30th frame is checked."],
  ["Detect", "YOLOv8n, a 6 MB model, finds people. It also keeps cars, dogs, cats and birds, since that is how it often labels inflatable costumes."],
  ["Filter", "A detection needs over 70% confidence, a center on the doorstep and two frames in a row. After a capture, the camera waits 30 seconds."],
  ["Classify", "The crop is sent to Nemotron 3.5 Super VL on Baseten. It returns a costume, a confidence and a one-line description. Inflatables it can’t confirm are dropped."],
  ["Publish", "Each person is blurred, the record is saved to Supabase, and Realtime adds it to this page."],
]

export function About() {
  return <section className="about-section" aria-labelledby="about-title">
    <h2 id="about-title" className="instrument-title">How This Works</h2>
    <ol className="about-steps">
      {steps.map(([name, body], i) => <li key={name}>
        <span className="about-index">{String(i + 1).padStart(2, "0")}</span>
        <h3>{name}</h3>
        <p>{body}</p>
      </li>)}
    </ol>
    <p className="about-notes">Counts are detections, not unique visitors. Confidence scores are the model’s own estimates.</p>
  </section>
}
