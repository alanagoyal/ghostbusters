import { galleryCopy } from "@/lib/gallery-copy";

export function About() {
  return <section className="about-section" aria-labelledby="about-title">
    <h2 id="about-title" className="instrument-title">How This Works</h2>
    <ol className="about-steps">
      {galleryCopy.steps.map(([name, body], i) => <li key={name}>
        <span className="about-index">{String(i + 1).padStart(2, "0")}</span>
        <h3>{name}</h3>
        <p>{body}</p>
      </li>)}
    </ol>
    <p className="about-notes">Counts are detections, not unique visitors. Confidence scores are the model’s own estimates. Cloud classification receives unblurred crops; saved-photo blurring is best effort, not anonymization.</p>
  </section>
}
