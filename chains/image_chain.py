import os
import json
import base64
from io import BytesIO
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
import torch
from diffusers import AutoPipelineForText2Image


class ImageChain:
    def __init__(self, llm=None, pipeline=None):
        self.llm = llm or ChatOllama(model="llama3:8b", temperature=0.7)
        
        if pipeline is None:
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                "stabilityai/sdxl-turbo",
                torch_dtype=torch.float16,
                variant="fp16"
            )
            if torch.cuda.is_available():
                self.pipe = self.pipe.to("cuda")
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

        # Generate image using local Stable Diffusion
        image = self.pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
        
        # Convert PIL image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return b64


__all__ = ["ImageChain"]