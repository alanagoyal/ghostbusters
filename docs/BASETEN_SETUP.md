# Existing Baseten installations

New clones use [local inference](LOCAL_SETUP.md). This page is for the optional legacy cloud path; existing `.env` settings remain supported.

Run `uv run --no-sync ghostbusters setup --provider baseten` for camera, model and Supabase configuration. Preserve existing working endpoints and credentials. The endpoint must accept chat-completions vision requests and return `choices[0].message.content` with the requested JSON.

The hosted configuration tested in October 2026 was:

```dotenv
BASETEN_MODEL_URL=https://inference.baseten.co/v1/chat/completions
BASETEN_MODEL=nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B
BASETEN_AUTH_SCHEME=Bearer
```

Supply `BASETEN_API_KEY` privately. For an existing dedicated Gemma deployment, preserve its endpoint and the original defaults `gemma` / `Api-Key`. Availability and billing depend on your provider account; consult the [Baseten vision documentation](https://docs.baseten.co/inference/model-apis/vision).

`uv run --no-sync ghostbusters doctor --skip-camera` makes a small billed vision request using a generated blank image and checks Supabase access. It does not prove capture, uploads or live gallery delivery; verify those with a deliberate walkthrough. Errors can reflect credentials, model access, credits, endpoint format or auth scheme.

This path sends unblurred person crops to Baseten and stores detections in the public cloud gallery. See [security and privacy](../SECURITY.md), [Supabase setup](SUPABASE_SETUP.md) and [cloud operation](CLI.md).
