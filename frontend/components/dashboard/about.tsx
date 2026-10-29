const steps = [
  ["Capture", "A doorbell camera streams video. About one frame per second is checked."],
  ["Detect", "YOLOv8n looks for people and for shapes that might be inflatable costumes."],
  ["Filter", "A person must be on the doorstep in two frames in a row. After each capture, the camera waits 30 seconds."],
  ["Classify", "Nemotron 3.5 Super VL guesses the costume and writes a short description."],
  ["Publish", "The person is blurred and the photo appears here."],
]

export function About() {
  return <section className="about-section" aria-labelledby="about-title">
    <h2 id="about-title" className="instrument-title">About Ghostbusters</h2>
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
