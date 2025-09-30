import os
import subprocess
import numpy as np
import base64
import uuid
from pathlib import Path
import requests
from openai import OpenAI
from celery import shared_task


# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@shared_task
def generate_video(prompt: str, out_path="output.mp4"):
    """
    DIY pipeline: GPT (script) + DALL·E (frames) + TTS (voiceover) + FFmpeg (video assembly).
    Handles both `b64_json` and `url` image responses.
    """
    out_dir = Path("media/generated_videos/" + str(uuid.uuid4()) + "/")
    out_dir.mkdir(exist_ok=True)

    # --- 1. GPT: Generate script ---
    gpt_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Write a short 3-sentence script for a video about: {prompt}"
        }]
    )
    script_text = gpt_resp.choices[0].message.content
    print("Generated Script:\n", script_text)

    # --- 2. DALL·E: Generate frames ---
    frames = []
    for i, line in enumerate(script_text.split("."), start=1):
        if not line.strip():
            continue

        img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=line.strip(),
            size="1536x1024"  # widescreen landscape
        )

        img_path = out_dir / f"frame_{i}_{str(uuid.uuid4())}.png"

        # Try URL first, fall back to base64
        if hasattr(img_resp.data[0], "url") and img_resp.data[0].url:
            img_url = img_resp.data[0].url
            r = requests.get(img_url)
            r.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(r.content)
            print(f"✅ Saved frame {i} from URL: {img_url}")

        elif hasattr(img_resp.data[0], "b64_json") and img_resp.data[0].b64_json:
            image_base64 = img_resp.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Saved frame {i} from base64")

        else:
            raise ValueError("No valid image data found in response")

        frames.append(str(img_path))

    # --- 3. TTS: Narration ---
    audio_path = out_dir / f"narration_{str(uuid.uuid4())}.mp3"
    # with client.audio.speech.with_streaming_response.create(
    #     model="gpt-4o-mini-tts",
    #     voice="alloy",
    #     input=script_text
    # ) as response:
    #     response.stream_to_file(audio_path)
    print(f"Narration saved: {audio_path}")

    # --- 4. Assemble Video with FFmpeg ---
    frame_list_file = out_dir / f"frames_{str(uuid.uuid4())}.txt"
    with open(frame_list_file, "w") as f:
        for frame in frames:
            abs_path = Path(frame).resolve()
            f.write(f"file '{abs_path}'\n")
            f.write("duration 2\n")
        last_frame = Path(frames[-1]).resolve()
        f.write(f"file '{last_frame}'\n")
    
    
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(frame_list_file),
        # "-i", str(audio_path),
        "-vf", (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
        ),
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    subprocess.run(cmd, check=True)

    print(f"🎬 Video saved at {out_path}")
    return out_path



@shared_task
def search_documents(query: str, documents: list, model: str = "text-embedding-3-small"):
    """
    Search for the most relevant document(s) given a query using OpenAI embeddings.
    
    Args:
        query (str): The search query.
        documents (list): A list of text documents.
        model (str): The embedding model ("text-embedding-3-small" or "text-embedding-3-large").
    
    Returns:
        dict: { "best_match": str, "scores": list of (doc, score) sorted by similarity }
    """
    # Embed all documents
    doc_embeddings = []
    for doc in documents:
        resp = client.embeddings.create(model=model, input=doc)
        vector = np.array(resp.data[0].embedding)
        doc_embeddings.append((doc, vector))
    
    # Embed query
    resp = client.embeddings.create(model=model, input=query)
    query_vec = np.array(resp.data[0].embedding)
    
    # Similarity function
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # Score documents
    scores = [(doc, cosine_similarity(query_vec, vec)) for doc, vec in doc_embeddings]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "best_match": scores[0][0],
        "scores": scores
    }

