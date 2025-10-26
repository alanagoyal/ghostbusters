# Baseten Deployment Checklist

Use this checklist to ensure successful deployment and integration of the costume classification model.

## Pre-Deployment

### 1. Account Setup
- [ ] Create Baseten account at [baseten.co](https://baseten.co)
- [ ] Verify email address
- [ ] Add payment method (required for GPU deployments)

### 2. API Keys
- [ ] Generate API key from Baseten dashboard → Settings → API Keys
- [ ] Add to `.env` file:
  ```bash
  BASETEN_API_KEY=your_api_key_here
  ```

### 3. Install Truss CLI
- [ ] Install Truss: `pip install truss`
- [ ] Authenticate: `truss login`
- [ ] Verify: `truss --version`

## Deployment

### 4. Review Configuration
- [ ] Check `truss_costume_classifier/config.yaml`:
  - [ ] GPU type is `L4` (cheapest option)
  - [ ] Concurrency is set appropriately (`predict_concurrency: 4`)
  - [ ] Model cache includes Qwen2-VL-7B-Instruct
- [ ] Review `model/model.py`:
  - [ ] System prompt is optimized for costume classification
  - [ ] Temperature is set to 0.3 (consistent descriptions)
  - [ ] Max tokens is 256 (short descriptions)

### 5. Deploy Model
- [ ] Navigate to directory: `cd truss_costume_classifier`
- [ ] Deploy: `truss push`
- [ ] Note deployment output (model ID and URL)
- [ ] Add to `.env`:
  ```bash
  BASETEN_MODEL_ID=your_model_id
  BASETEN_MODEL_URL=your_model_url
  ```

### 6. Wait for Build
- [ ] Monitor build progress in Baseten dashboard
- [ ] Wait for status: "Active" (~10-15 minutes first time)
- [ ] Check logs for any errors: `truss logs <model-id>`

## Testing

### 7. Test in Dashboard
- [ ] Open Baseten dashboard → Your Model → Playground
- [ ] Upload a test costume image
- [ ] Click "Predict"
- [ ] Verify description is reasonable

### 8. Test via API
- [ ] Run test script: `python test_baseten_api.py <test_image.jpg>`
- [ ] Verify response format:
  ```json
  {
    "description": "witch with purple hat",
    "confidence": null
  }
  ```
- [ ] Check response time (should be 1-3 seconds after warmup)

### 9. Test Integration with Pi Code
- [ ] Test API client: `python classify_costume_api.py <test_image.jpg>`
- [ ] Verify error handling works (try with invalid image)
- [ ] Test warmup function: `python classify_costume_api.py --warmup`

## Pre-Event Preparation

### 10. Warmup Strategy (Optional)
- [ ] Decide: Keep model warm or accept cold start?
  - **Warm**: Send request every 5 minutes starting 1 hour before
  - **Cold start**: Accept 30-60 second delay on first trick-or-treater
- [ ] If keeping warm, create warmup cron job or script

### 11. Cost Estimation
- [ ] Estimate expected traffic:
  - Number of trick-or-treaters: ________
  - Duration of event: ________ hours
  - Requests per hour: ________
- [ ] Calculate cost:
  - L4 GPU: ~$0.50/hour active
  - Estimated total: ~$________ for the night

### 12. Set Budget Alerts (Recommended)
- [ ] Go to Baseten dashboard → Billing
- [ ] Set budget alert (e.g., $10)
- [ ] Add email for notifications

## Halloween Night

### 13. Pre-Event Checks (1 hour before)
- [ ] Verify model status: "Active" in dashboard
- [ ] Send warmup request: `python classify_costume_api.py --warmup`
- [ ] Check API latency (should be <3 seconds)
- [ ] Verify .env file is loaded on Pi
- [ ] Test full pipeline (RTSP → YOLO → Baseten → Supabase)

### 14. During Event Monitoring
- [ ] Monitor Baseten dashboard for:
  - [ ] Request count (should increment with each detection)
  - [ ] Error rate (should be <5%)
  - [ ] Latency (should be 1-3 seconds)
- [ ] Watch Pi logs for API errors
- [ ] Check Supabase for incoming costume data

### 15. Troubleshooting
If issues occur:

**High latency (>10 seconds)**:
- [ ] Check if model is cold starting (first request after idle)
- [ ] Verify network connection on Pi
- [ ] Check Baseten status page

**Errors (429 Too Many Requests)**:
- [ ] Reduce request rate on Pi
- [ ] Increase concurrency in config.yaml and redeploy
- [ ] Add retry logic with backoff

**Empty or poor descriptions**:
- [ ] Check image quality (too dark, blurry, etc.)
- [ ] Verify person crop includes full costume
- [ ] Try adjusting temperature (0.5-0.7 for more creativity)

**API credentials error**:
- [ ] Verify .env file is loaded
- [ ] Check API key is valid (test in dashboard)
- [ ] Verify model URL is correct

## Post-Event

### 16. Review and Analysis
- [ ] Check total requests in Baseten dashboard
- [ ] Review total cost
- [ ] Export logs for debugging
- [ ] Analyze costume descriptions for quality

### 17. Cleanup (Optional)
- [ ] Archive model (to avoid idle costs)
- [ ] Download logs for future reference
- [ ] Update documentation with lessons learned

### 18. Scale Down (If Not Using Scale-to-Zero)
- [ ] Model will auto-scale to zero after 10 minutes idle
- [ ] No manual action needed if using default config

## Future Improvements

- [ ] Consider upgrading to larger model (Qwen2-VL-72B) for better descriptions
- [ ] Add confidence score estimation
- [ ] Implement caching for similar costumes
- [ ] Fine-tune model on Halloween costume dataset
- [ ] Add support for multiple languages

## Notes

**Important reminders**:
- First request after idle may take 30-60 seconds (cold start)
- Scale-to-zero means $0 cost when idle
- Always test warmup strategy before event
- Set budget alerts to avoid surprises
- Monitor dashboard during event for issues

**Support resources**:
- Baseten Docs: https://docs.baseten.co
- Truss Docs: https://truss.baseten.co
- Discord: https://discord.gg/baseten
- Email: support@baseten.co

---

**Deployment Date**: _______________

**Model ID**: _______________

**Model URL**: _______________

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________
