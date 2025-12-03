import os
import json
import base64
from io import BytesIO
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama


def _ollama_base_kwargs():
    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return {"base_url": base}
    return {}
import torch
from diffusers import AutoPipelineForText2Image


class ImageChain:
    def __init__(self, llm=None, pipeline=None):
        self.llm = llm or ChatOllama(model="llama3:8b", temperature=0.7, **_ollama_base_kwargs())
        
        if pipeline is None:
            # Force CPU mode for stability (GPU can hang on some systems)
            force_cpu = os.getenv("FORCE_CPU_IMAGE", "true").lower() in ("1", "true", "yes")
            
            if force_cpu:
                print("[IMAGE] Loading Stable Diffusion on CPU (set FORCE_CPU_IMAGE=false to use GPU)")
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    "stabilityai/sdxl-turbo",
                    torch_dtype=torch.float32
                )
                self.pipe = self.pipe.to("cpu")
            else:
                print("[IMAGE] Loading Stable Diffusion on GPU")
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    "stabilityai/sdxl-turbo",
                    torch_dtype=torch.float16,
                    variant="fp16"
                )
                if torch.cuda.is_available():
                    self.pipe = self.pipe.to("cuda")
                else:
                    print("[IMAGE] Warning: CUDA not available, falling back to CPU")
                    self.pipe = self.pipe.to("cpu")
        else:
            self.pipe = pipeline

        # Prompt to extract cinematic components
        self.prompt = PromptTemplate(
            input_variables=["final_text"],
            template=(
                "Extract cinematic image prompt components from the following fictional continuation. "
                "Return a JSON object with exactly these keys: subject, setting, lighting, mood, realism_level. "
                "Keep values concise, suitable for an image-generation prompt. Output MUST be valid JSON only.\n\n"
                "Continuation:\n{final_text}"
            ),
        )

    def build_prompt_from_components(self, comps: dict) -> str:
        # Build readable cinematic prompt
        parts = [
            f"Subject: {comps.get('subject')}",
            f"Setting: {comps.get('setting')}",
            f"Lighting: {comps.get('lighting')}",
            f"Mood: {comps.get('mood')}",
            f"Realism: {comps.get('realism_level')}",
            "Cinematic photograph, ultra-detailed, 1:1 aspect ratio, high resolution"
        ]
        return ", ".join(parts)

    def generate(self, final_text: str) -> str:
        # Use LLM to extract components
        print("[IMAGE] Extracting image prompt components from story using LLM...")
        chain = self.prompt | self.llm
        comp_raw = chain.invoke({"final_text": final_text}).content
        try:
            comps = json.loads(comp_raw)
        except Exception:
            # Fallback: try to extract JSON from text
            start = comp_raw.find('{')
            end = comp_raw.rfind('}')
            if start == -1 or end == -1:
                raise RuntimeError(f"Could not parse JSON from components: {comp_raw}")
            comps = json.loads(comp_raw[start:end+1])

        prompt = self.build_prompt_from_components(comps)
        print(f"[IMAGE] Prompt extracted. Generating image with Stable Diffusion (this may take 10-60s)...")

        # Generate image using local Stable Diffusion
        image = self.pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
        print("[IMAGE] ✓ Image generation complete")
        
        # Convert PIL image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return b64


__all__ = ["ImageChain"]