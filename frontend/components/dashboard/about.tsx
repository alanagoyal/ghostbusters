const steps = [
  ["Capture", "A DoorBird doorbell streams RTSP over TCP. One frame in thirty is kept, about one a second."],
  ["Detect", "YOLOv8n, all 6 MB of it, looks for people. It also flags cars, dogs, cats and birds, which is what it tends to call an inflatable costume."],
  ["Debounce", "A box needs >0.7 confidence, a center on the doorstep and two hits in a row. Then the camera ignores everyone for 30 s."],
  ["Classify", "The unblurred crop goes to Nemotron 3.5 Super VL on Baseten and comes back as JSON: a label, a confidence, one line of description. Inflatables it can't confirm are dropped."],
  ["Publish", "Each person is blurred with a 33 px Gaussian, the row lands in Supabase, and Realtime pushes it to this page."],
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
    <p className="about-notes">Counts are detections, not visitors: a kid who comes back for seconds counts twice. Confidence is the model grading its own homework, not a calibrated probability. And a smaller model was cut in testing for looking at a Ghostbusters costume and answering “No costume.”</p>
  </section>
}
