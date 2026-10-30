# Local vision measurements

Measured October 25, 2026 with MLX-VLM 0.7.10, Python 3.11.17 and an Apple M4
Mac mini (10 CPU / 10 GPU cores, 16 GB unified memory, macOS 26.6). Runs used
Metal GPU acceleration with no cloud inference.

## Model and resource requirements

Selected model: [`mlx-community/Qwen3-VL-4B-Instruct-4bit`](https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit),
revision `2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b`, Apache 2.0. It is a quantized
conversion of [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct).
The runtime pins this revision. YOLOv8n detects candidate regions; see
[third-party notices](../THIRD_PARTY_NOTICES.md) for licenses.

| Measurement | Result |
| --- | --- |
| Vision model download | Approximately 2.9 GiB |
| Free disk for model/dependency setup | Allow at least 6 GB, plus retained images |
| Warm inference, comparison crops | Approximately 2.0–3.1 seconds |
| First inference, comparison run | 6.57 seconds |
| Peak Metal allocation, comparison run | 3.91 GB |
| Model load, already downloaded with warm filesystem | 4.42 seconds |

Metal allocation is not total application memory. Capture, the gallery and other
processes need additional memory. These are not cold-disk/reboot measurements
and do not establish performance on every Apple Silicon chip. The supported
installation floor is 16 GB RAM; Pi, Linux, Windows and CPU-only local inference
are not supported by this release.

## Method and limitations

The [five licensed fixture photographs](../backend/tests/fixtures/local/README.md)
include costumes and ordinary-clothes controls. Four photos were used for model
comparison; the witch photo was held out. YOLOv8n produced 14 comparison crops at
confidence ≥0.5, including incidental people and car/bird/dog/cat candidates.
Vision input was bounded to 640×640, temperature 0, and 180 output tokens. No
fixture-specific prompts or labels were supplied.

All 14 comparison responses passed schema validation. Six clear foreground
costume crops received acceptable generic labels, including Batman, Cat in the
Hat, Ghostbusters and owl. The inflatable deer was called “inflatable suit.” An
ambiguous cross-holding person received a prop description rather than a useful
costume label. The held-out witch was correctly labeled on two repeated calls.

This tiny selected set is **not a general accuracy estimate**. Repeated calls
are not independent samples. YOLO can merge people or miss candidates; partial
and background crops can produce speculative descriptions. Model confidence is
uncalibrated. Low light, occlusion, masks, groups, distant children and unusual
costumes still need testing on the actual doorstep.

## Fresh-install acceptance

An M2 MacBook Air (24 GB, macOS 26.6.2, Python 3.11.14) passed a fresh install on
October 25, 2026: DoorBird discovery/authentication without a saved IP, continuous
stream decoding, the licensed fixture pipeline and detached restart checks. A
real-person walkthrough automatically classified as “No costume” and appeared
in the authenticated gallery. This verifies the ordinary-clothes path, not
costume accuracy across lighting conditions or other cameras.

To repeat the camera-free pipeline check, follow the
[fixture test instructions](../backend/tests/fixtures/README.md).
