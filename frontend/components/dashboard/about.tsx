const steps = [
  ["Capture", "A compatible camera streams video to a computer on the same network."],
  ["Detect", "YOLO finds people and candidate costumes in sampled frames."],
  ["Filter", "The capture settings control confidence, the detection region and the delay between photos."],
  ["Classify", "The configured vision model receives a crop and returns a costume guess, confidence and description."],
  ["Publish", "Detected person regions are blurred before cloud photos are saved to Supabase. Live updates add new records to this page."],
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
    <p className="about-notes">Counts are detections, not unique visitors. Confidence scores are the model’s own estimates. Cloud classification receives unblurred crops; saved-photo blurring is best effort, not anonymization.</p>
  </section>
}
