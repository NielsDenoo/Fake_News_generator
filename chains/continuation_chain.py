import os
import json
import re
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

# Lazy local generator (transformers) to use when Ollama is unavailable
_LOCAL_PIPE = None
def _get_local_pipe():
    global _LOCAL_PIPE
    if _LOCAL_PIPE is None:
        try:
            from transformers import pipeline
            import torch

            device = 0 if torch.cuda.is_available() else -1
            model_name = os.getenv("LOCAL_GEN_MODEL", "gpt2")
            _LOCAL_PIPE = pipeline("text-generation", model=model_name, device=device)
        except Exception:
            _LOCAL_PIPE = None
    return _LOCAL_PIPE


def _ollama_base_kwargs():
    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return {"base_url": base}
    return {}
from schemas import ContinuationOptions


class ContinuationChain:
    def __init__(self, llm=None):
        self.llm = llm or ChatOllama(model="llama3:8b", temperature=0.8, **_ollama_base_kwargs())
        self.prompt = PromptTemplate(
            input_variables=["article_text"],
            template=(
                "You are an imaginative writer. Given the following news article text, generate exactly 3 distinct continuation ideas "
                "that could plausibly continue the narrative in a fictional direction. Respond with a single JSON object exactly like: "
                "{{\"options\": [\"option1\", \"option2\", \"option3\"]}}. Do not add any other text.\n\nArticle:\n{article_text}"
            ),
        )

    def generate(self, article_text: str) -> ContinuationOptions:
        # First try the configured LLM (usually Ollama)
        try:
            chain = self.prompt | self.llm
            res = chain.invoke({"article_text": article_text}).content
        except Exception as primary_exc:
            # Attempt local transformers generator as a substitute
            try:
                pipe = _get_local_pipe()
                if pipe is None:
                    raise primary_exc
                prompt_text = self.prompt.format(article_text=article_text)
                gen = pipe(prompt_text, max_new_tokens=256, do_sample=True, temperature=0.8)[0]
                res = gen.get("generated_text") or gen.get("text") or ""
            except Exception:
                # re-raise the original exception to be handled by caller
                raise primary_exc
        # robust JSON extraction (same strategy as TitleChain)
        def extract_json(text: str):
            try:
                return json.loads(text)
            except Exception:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    chunk = text[start : end + 1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        cleaned = chunk.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
                        return json.loads(cleaned)
                start = text.find("[")
                end = text.rfind("]")
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(text[start : end + 1])
                    except Exception:
                        pass
                raise ValueError("No JSON object found in model output")

        try:
            parsed = extract_json(res)

            def clean_key(k: str) -> str:
                import re as _re

                return _re.sub(r"[^a-z0-9]", "", k.strip().lower())

            def to_list_of_strings(v):
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
                if isinstance(v, str):
                    try:
                        decoded = json.loads(v)
                        return to_list_of_strings(decoded)
                    except Exception:
                        parts = [s.strip(" -\t\r") for s in re.split(r"\n|;|\\.|\u2022|\u2023", v) if s.strip()]
                        return [p for p in parts if p]
                return [str(v).strip()]

            options_list = None

            if isinstance(parsed, dict):
                if "options" in parsed:
                    options_list = to_list_of_strings(parsed["options"])
                else:
                    for k, v in parsed.items():
                        if "option" in clean_key(k) or "choice" in clean_key(k):
                            options_list = to_list_of_strings(v)
                            break

            if options_list is None and isinstance(parsed, list):
                options_list = to_list_of_strings(parsed)

            if options_list is None and isinstance(parsed, str):
                qmatches = re.findall(r'"([^"\n]{3,})"', parsed)
                qmatches += re.findall(r"'([^'\n]{3,})'", parsed)
                if qmatches:
                    options_list = [s.strip() for s in qmatches][:3]
                else:
                    options_list = to_list_of_strings(parsed)

            if not isinstance(options_list, list):
                options_list = [str(options_list)]
            options_list = [o for o in options_list if o]
            if len(options_list) >= 3:
                options_list = options_list[:3]

            parsed = {"options": options_list}
            out = ContinuationOptions(**parsed)
            if len(out.options) != 3:
                raise ValueError(f"LLM did not return exactly 3 options (got {len(out.options)})")
            return out
        except Exception as e:
            raise RuntimeError(f"Failed to parse continuation output: {e}\nRaw output:\n{res}")


__all__ = ["ContinuationChain"]