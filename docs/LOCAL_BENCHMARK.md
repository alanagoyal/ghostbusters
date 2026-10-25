# Local vision benchmark — October 25, 2026

Selected runtime: MLX-VLM 0.7.10, Python 3.11.17, Apple M4 Mac mini (10 CPU / 10 GPU cores), 16 GB unified memory, macOS 26.6. GPU access is required; the agent sandbox itself had no Metal device, so actual model runs used the host GPU. No cloud inference, account or token was used.

Selected model: [`mlx-community/Qwen3-VL-4B-Instruct-4bit`](https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit), revision `2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b`, Apache 2.0. Download approximately 2.9 GiB; allow at least 6 GB free for model/dependency setup, plus retained images. Pinning is in `vision.py` and `local models`. MLX weights are a quantized conversion of [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct). YOLOv8n uses Ultralytics' license; see THIRD_PARTY_NOTICES.

## Method and measured results

Five real licensed photographs are shipped with attribution in `backend/tests/fixtures/local/README.md`. First four were used to compare candidates. The fifth (witch) was held out until selection. YOLOv8n produced crops at confidence >=0.5, including the existing car/bird/dog/cat candidate classes. Vision input is bounded to 640×640, temperature 0, max 180 output tokens. JSON is parsed and schema validated. No fixture-specific prompts or labels are passed to the model.

Identical first-four-photo crop comparison (14 crops including incidental people/candidates): Qwen3 returned 14/14 valid schemas, roughly 2.0–3.1 seconds warm, 6.57 seconds first inference, peak Metal allocation 3.91 GB. The held-out witch gave two correct `witch` labels, 4.25 seconds first and 2.58 seconds repeat. Fresh-process model load on an already downloaded/warm filesystem was 4.42 seconds (2.94 CPU-seconds); first/repeat inference used 1.31/0.60 CPU-seconds. Peak Metal allocation in that held-out process was 3.62 GB and OS max RSS 0.55 GB; RSS excludes separately reported Metal memory and is **not** total memory use. Simultaneous app/capture needs additional memory. This is not a cold-disk/reboot benchmark. Initial 3B load, including first-time library overhead, took 25.78 seconds.

| Visible foreground case | Qwen3 result | Judgment |
|---|---|---|
| Batman mask / Waluigi hat overlap | Batman; description mentions other cap | Correct visible category, misses second character; YOLO merges two people |
| Reflective wrapped suit | Mummy | Reasonable generic label |
| Cross-holding white-shirt person | wooden cross | Descriptive prop, not a useful costume label; ambiguous case |
| Black-shirt bystander | No costume | Correct ordinary-clothes control |
| Cat in the Hat | Cat in the Hat | Correct |
| Ghostbusters patch and gear | Ghostbusters | Correct |
| Owl vest/beak | owl | Correct |
| Inflatable deer | inflatable suit | Correct generic category, does not identify deer |
| Held-out witch | witch (twice) | Correct |

Six clear foreground costume crops in the comparison had acceptable generic labels (6/6); held-out adds one photo, two repeated calls (not two independent samples). This tiny selected set is **not a general accuracy estimate**. Remaining blurred/partial/background crops mostly returned Unknown/No costume; some descriptions speculate. YOLO coverage is also imperfect: merged people, partial crops and nonhuman candidates are not unique visitors. Inflatable recovery only covers selected YOLO candidate classes, not every shape.

Rejected alternatives: Qwen2.5-VL-3B 4-bit (~2.9 GiB) was fast (~1.4–3.7 seconds warm) but called a visible Ghostbusters costume and Batman mask “No costume” under the final general prompt. Its initial shorter prompt recovered some clear costumes but still missed others. Qwen2.5-VL-7B 4-bit (~5.3 GiB), on identical crops, was slower (~3.7–5.8 seconds warm; 7.21 first) and used 6.26 GB peak Metal; it confused owl with eagle and the inflatable deer with sumo. Qwen3 was selected for materially better observed labels at lower memory/latency, not just successful JSON.

Confidence is model-generated and uncalibrated (wrong alternatives often said 0.9). The gallery calls outputs “model guesses” and does not present confidence as accuracy. Low light, occlusion, masks, novel/inflatable costumes, children at a distance, multiple people and non-costumed bystanders remain hard cases. This host evidence supports a 16 GB Apple Silicon profile only; no Pi, Linux, Windows or CPU-only local performance claim.

Continuous real DoorBird stream: 119 decoded 640×480 MJPEG frames in 15.0847 seconds, no disconnect/error, no frame saved. This does not prove a real person/costume walkthrough. Full pipeline and lifecycle evidence is separate from these classification-only benchmarks.

## Fresh-install acceptance

On October 25, 2026, an M2 MacBook Air (24 GB, macOS 26.6.2, Python 3.11.14) installed from a fresh source snapshot, discovered and authenticated DoorBird without a saved IP, decoded 119 frames in 15.06 seconds, and passed the licensed fixture pipeline and detached restart checks without source fixes. A real-person walkthrough then classified automatically as “No costume” on its first attempt and appeared in the authenticated gallery. This verifies the ordinary-clothes path, not costume accuracy in all lighting or on other camera models.
