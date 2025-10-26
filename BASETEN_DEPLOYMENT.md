# Deploying Qwen-VL (7B) to Baseten

## Current Status: ⏸️ Waiting on Baseten Support

**Issue**: A10G GPU type not available on current Baseten tier
**Action**: Contacted Baseten support to request GPU access or alternative
**Date**: 2025-10-26

## Prerequisites

✅ Completed:
- Baseten API key configured in `.env` file
- Python environment set up
- Truss installed via `uv tool install truss`
- Truss examples cloned to `~/Developer/truss-examples`

## Deployment Steps (Resume Once GPU Access Granted)

### 1. Install Truss

```bash
uv pip install --upgrade truss
```

### 2. Clone Truss Examples

```bash
cd ~/Developer
git clone https://github.com/basetenlabs/truss-examples.git
cd truss-examples/qwen/qwen-vl
```

### 3. Deploy to Baseten

```bash
truss push
```

When prompted:
- Enter your Baseten API key: `S2bxUsqG.6AwcHlZbfVLKfbdFStFdSvoLbuEfZVP7`
- Choose development or production deployment
- Wait for model to build and deploy (~5-10 minutes)

### 4. Get Your Model Endpoint

After deployment completes, you'll receive:
- **Model ID**: Save this (looks like `model-xxxxxxxxx`)
- **API URL**: `https://model-<ID>.api.baseten.co/development/predict`

### 5. Update .env File

Add to your `.env` file:
```bash
BASETEN_MODEL_ID=your_model_id_here
BASETEN_MODEL_URL=https://model-<ID>.api.baseten.co/development/predict
```

## Testing Your Deployment

```bash
cd ~/Developer/costume-classifier
uv run python test_baseten_model.py
```

## Model Specifications

- **Model**: Qwen-VL (7B parameters)
- **GPU**: Single A10G
- **Input**: Images (URL or base64) + text prompts
- **Output**: Text descriptions/classifications
- **Cost**: ~$0.001-0.003 per image (estimate)

## Troubleshooting

### Deployment fails
- Check your API key is correct
- Ensure you have credits in your Baseten account

### Model timeout
- First request may take 30-60 seconds (cold start)
- Subsequent requests should be faster (2-5 seconds)

## Support Request Details

**What to tell Baseten support:**
> I'm trying to deploy the Qwen-VL model from your truss-examples repository (`qwen/qwen-vl`), but I'm getting an error:
>
> ```
> ERROR ApiError: Feature unavailable: The GPU type 'A10G' is not supported for your organization.
> ```
>
> Can you please enable A10G GPU access for my account, or recommend an alternative GPU type that would work for vision language models on my current tier?

**Model Details:**
- Model: Qwen-VL (7B parameters)
- Repository: `basetenlabs/truss-examples/qwen/qwen-vl`
- Required GPU: A10G (according to config.yaml)
- Use case: Halloween costume classification for personal project

**Account:**
- API Key: (configured in `.env` file)

## Next Steps

### Once GPU Access is Granted:
1. Run `truss push` from `~/Developer/truss-examples/qwen/qwen-vl`
2. Add model URL to `.env` file
3. Test with `uv run python test_baseten_model.py`
4. Run costume classification with `uv run python classify_costumes.py`
5. Deploy to Raspberry Pi

### Alternative if GPU Not Available:
Consider switching to OpenAI GPT-4 Vision API (no deployment needed, direct API access)
