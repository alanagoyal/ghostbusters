# Halloween Costume Classifier - Baseten Truss

This directory contains a Truss package for deploying a vision-language model (Qwen2-VL-7B-Instruct) to Baseten for costume classification.

## Quick Start

### Prerequisites

1. **Baseten account**: Sign up at [baseten.co](https://baseten.co)
2. **API key**: Get from Baseten dashboard → Settings → API Keys
3. **Truss CLI**: Install with `pip install truss`

### Deploy

```bash
# Authenticate
truss login

# Deploy model
cd truss_costume_classifier
truss push
```

The deployment will:
- Upload model code and config
- Build Docker container with dependencies
- Deploy to L4 GPU infrastructure
- Return model URL and ID

Save the model URL and ID to your `.env` file.

## Directory Structure

```
truss_costume_classifier/
├── README.md              # This file
├── config.yaml            # Truss configuration
└── model/
    ├── __init__.py
    └── model.py           # Model inference code
```

## Configuration Highlights

**Model**: Qwen2-VL-7B-Instruct (7 billion parameter vision-language model)

**Hardware**:
- Single NVIDIA L4 GPU (24GB VRAM) - cheapest option
- 4 CPU cores, 16GB RAM

**Features**:
- **Scale-to-zero**: Automatically shuts down when idle (saves costs)
- **Autoscaling**: Scales up for traffic spikes
- **Concurrency**: Handles 4 parallel requests per replica

**Cost**: ~$0.05-$0.50 per hour active inference

## API Usage

### Input Format

```json
{
  "image": "base64_encoded_image_string",
  "prompt": "What Halloween costume is this person wearing?",
  "max_tokens": 256,
  "temperature": 0.3
}
```

### Output Format

```json
{
  "description": "witch with purple hat and broom",
  "confidence": null
}
```

### Example Request (Python)

```python
import requests
import base64

# Load image
with open("person.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# Call API
response = requests.post(
    "https://model-<your-id>.api.baseten.co/production/predict",
    headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
    json={
        "image": f"data:image/jpeg;base64,{image_base64}",
        "prompt": "What Halloween costume is this person wearing?",
        "max_tokens": 256,
        "temperature": 0.3
    }
)

result = response.json()
print(f"Costume: {result['description']}")
```

## Testing

### Local Testing (Optional)

Requires Docker:

```bash
truss run-image truss_costume_classifier
```

This starts a local server at `http://localhost:8080`.

### Production Testing

After deployment, test via Baseten dashboard Playground or use the example Python script above.

## Model Details

### System Prompt

The model is configured with a specialized prompt for costume classification:

> "You are a Halloween costume classifier. Describe the person's costume in one short, specific phrase (e.g., 'witch with purple hat and broom', 'skeleton with glowing bones', 'inflatable T-Rex'). Focus on distinctive details and colors."

This ensures:
- Concise descriptions (not long paragraphs)
- Specific details (colors, props, themes)
- Consistent output format

### Performance

- **Cold start**: ~30-60 seconds (first request after idle)
- **Warm inference**: ~1-3 seconds per image
- **Throughput**: ~4 requests/second with concurrency=4

### Limitations

- **Confidence scores**: Qwen2-VL doesn't provide confidence scores (always `null`)
- **Image size**: Recommended max 2048×2048 pixels
- **Languages**: Best performance with English prompts

## Cost Optimization

### Scale-to-Zero

The model automatically scales to zero replicas after 10 minutes of inactivity:

- **Idle**: $0/hour
- **Active**: ~$0.50/hour

For Halloween night (3 hours, 100 trick-or-treaters):
- **Total cost**: ~$0.05-$0.50

### Warm-Up Strategy

To avoid cold starts during Halloween:

```python
# Send warm-up request 30 minutes before event
requests.post(model_url, headers=headers, json={
    "image": "data:image/jpeg;base64,...",  # Small test image
    "prompt": "test",
    "max_tokens": 10
})
```

## Monitoring

### View Logs

```bash
# Real-time logs
truss logs <model-id> --follow

# Recent logs
truss logs <model-id> --tail 100
```

### Metrics

View in Baseten dashboard:
- Request count and latency
- Error rates
- GPU utilization
- Cost tracking

## Updating the Model

To update the model code or configuration:

1. **Edit files**: Modify `config.yaml` or `model/model.py`
2. **Redeploy**: Run `truss push` again
3. **Version**: Baseten automatically versions deployments
4. **Rollback**: Can rollback to previous versions in dashboard

## Troubleshooting

### Cold Start Timeout

**Issue**: First request takes >60 seconds

**Solution**: Expected with scale-to-zero. Send warm-up request before event.

### Empty Descriptions

**Issue**: Model returns very short or empty descriptions

**Solution**:
- Increase `temperature` (try 0.5-0.7)
- Adjust system prompt in `model/model.py`
- Increase `max_tokens` to 512

### CUDA Out of Memory

**Issue**: "CUDA out of memory" error

**Solution**:
- Model too large for L4 GPU
- Try smaller model (Qwen2-VL-2B)
- Or upgrade to A10G/A100 in `config.yaml`

## Further Documentation

See `/docs/BASETEN_DEPLOYMENT.md` for comprehensive guide including:
- Detailed explanation of Baseten and Truss
- Step-by-step deployment walkthrough
- Integration with Raspberry Pi
- Advanced configuration options
- Cost analysis and optimization strategies

## Support

- **Baseten Docs**: https://docs.baseten.co
- **Truss Docs**: https://truss.baseten.co
- **Discord**: https://discord.gg/baseten
- **Email**: support@baseten.co
