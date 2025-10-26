"""
Test CLIP costume classification on cropped person images.
"""

import torch
import clip
from PIL import Image
import os
import time
from costume_labels import get_formatted_labels, COSTUME_LABELS

def test_clip_classification():
    print("🎨 Testing CLIP costume classification...")

    # Check for cropped person images
    crop_files = [f for f in os.listdir('.') if f.startswith('test_person_crop_')]

    if not crop_files:
        print("❌ No person crop images found!")
        print("   Run test_yolo_detection.py first to generate person crops.")
        return

    print(f"\n📸 Found {len(crop_files)} person crop(s) to classify")

    # Load CLIP model
    print("\n📦 Loading CLIP model...")
    print("   (This may take a minute on first run...)")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   Using device: {device}")

    start_time = time.time()
    model, preprocess = clip.load("ViT-B/32", device=device)
    load_time = time.time() - start_time
    print(f"   ✅ CLIP model loaded in {load_time:.2f} seconds")

    # Prepare costume labels
    costume_labels = COSTUME_LABELS
    text_prompts = get_formatted_labels()

    print(f"\n🏷️  Classifying against {len(costume_labels)} costume types")

    # Tokenize text prompts
    text_tokens = clip.tokenize(text_prompts).to(device)

    # Process each cropped person image
    for crop_file in sorted(crop_files):
        print(f"\n{'='*60}")
        print(f"Processing: {crop_file}")
        print('='*60)

        # Load and preprocess image
        image = Image.open(crop_file)
        image_input = preprocess(image).unsqueeze(0).to(device)

        # Run CLIP inference
        print("🤖 Running CLIP inference...")
        inference_start = time.time()

        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_tokens)

            # Normalize features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            # Calculate similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

        inference_time = time.time() - inference_start
        print(f"   Inference time: {inference_time:.2f} seconds")

        # Get top 5 predictions
        values, indices = similarity[0].topk(5)

        print(f"\n🎃 Top 5 costume predictions:")
        for i, (value, index) in enumerate(zip(values, indices)):
            costume = costume_labels[index]
            confidence = value.item()
            print(f"   {i+1}. {costume:30s} - {confidence*100:.1f}%")

        # Get the top prediction
        top_costume = costume_labels[indices[0]]
        top_confidence = values[0].item()

        print(f"\n🏆 Best match: {top_costume} ({top_confidence*100:.1f}% confidence)")

    print(f"\n{'='*60}")
    print("🎉 CLIP costume classification test COMPLETE!")
    print('='*60)

    print(f"\n📊 Performance Summary:")
    print(f"   Model load time: {load_time:.2f}s")
    print(f"   Average inference time: {inference_time:.2f}s per image")
    print(f"   Total costume labels: {len(costume_labels)}")

    print(f"\n💡 Next steps:")
    print(f"   1. Review the classification results above")
    print(f"   2. If accuracy is good, proceed to build the main detector")
    print(f"   3. If accuracy is poor, we may need to:")
    print(f"      - Adjust the costume label list")
    print(f"      - Try different CLIP prompts")
    print(f"      - Consider the Baseten API approach instead")

if __name__ == "__main__":
    test_clip_classification()
