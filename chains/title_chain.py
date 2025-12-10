import os
import json
import re
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama


def _ollama_base_kwargs():
    # Allow overriding Ollama host via OLLAMA_BASE_URL env var (e.g. http://host:11434)
    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return {"base_url": base}
    return {}
from schemas import TitlesOutput, Article


class TitleChain:
    def __init__(self, llm=None):
        self.llm = llm or ChatOllama(model="llama3:8b", temperature=0.7, **_ollama_base_kwargs())
        self.prompt = PromptTemplate(
            input_variables=["articles_json"],
            template=(
                "You are a creative editor. Given the following list of news articles as JSON, "
                "generate exactly 3 engaging, rewritten titles suitable for a popular audience. "
                "Respond with a single JSON object exactly in this format: {{\"titles\": [\"title1\", \"title2\", \"title3\"]}} "
                "Do not include any extra text, explanation, or formatting. Keep titles concise and unique.\n\n"
                "Articles JSON:\n{articles_json}"
            ),
        )

    def generate(self, articles: list[Article]) -> TitlesOutput:
        # prepare articles JSON and ensure URLs are serialized as strings
        articles_payload = []
        for a in articles:
            d = a.dict()
            # HttpUrl / AnyUrl objects may not be JSON serializable; coerce to str when present
            if d.get("image_url"):
                d["image_url"] = str(d["image_url"])
            if d.get("url"):
                d["url"] = str(d["url"])
            articles_payload.append(d)

        chain = self.prompt | self.llm
        res = chain.invoke({"articles_json": json.dumps(articles_payload, ensure_ascii=False)}).content

        # parse structured JSON output robustly
        def extract_json(text: str):
            # attempt direct load
            try:
                return json.loads(text)
            except Exception:
                # fallback: find first { and last }
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    chunk = text[start : end + 1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        # try replacing smart quotes
                        cleaned = chunk.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
                        return json.loads(cleaned)
                # last resort: maybe the model returned a bare JSON array
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

            # helper to normalize keys
            def clean_key(k: str) -> str:
                import re as _re

                return _re.sub(r"[^a-z0-9]", "", k.strip().lower())

            # normalize dict keys by stripping surrounding quotes and non-alphanumeric chars
            if isinstance(parsed, dict):
                normalized = {}
                for k, v in parsed.items():
                    newk = k.strip()
                    # remove surrounding quotes if present
                    if (newk.startswith('"') and newk.endswith('"')) or (newk.startswith("'") and newk.endswith("'")):
                        newk = newk[1:-1]
                    # remove non-alphanumeric characters for matching but keep the original cleaned key in dict
                    newk_clean = clean_key(newk)
                    # prefer to set the cleaned readable key if it's meaningful
                    if newk_clean:
                        normalized[newk_clean] = v
                    else:
                        normalized[newk] = v
                parsed = normalized

            def to_list_of_strings(v):
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
                if isinstance(v, str):
                    try:
                        decoded = json.loads(v)
                        return to_list_of_strings(decoded)
                    except Exception:
                        # split on lines or semicolons
                        parts = [s.strip(" -\t\r") for s in re.split(r"\n|;|\\.|\u2022|\u2023", v) if s.strip()]
                        return [p for p in parts if p]
                return [str(v).strip()]

            titles_list = None

            # Direct dict with correct key
            if isinstance(parsed, dict):
                # try exact key
                if "titles" in parsed:
                    titles_list = to_list_of_strings(parsed["titles"])
                else:
                    # search for any key containing title
                    for k, v in parsed.items():
                        if "title" in clean_key(k):
                            titles_list = to_list_of_strings(v)
                            break

            # If parsed is a list, assume it's the titles
            if titles_list is None and isinstance(parsed, list):
                titles_list = to_list_of_strings(parsed)

            # If still None and parsed is a string, attempt to extract quoted strings or lines
            if titles_list is None and isinstance(parsed, str):
                qmatches = re.findall(r'"([^"\n]{3,})"', parsed)
                qmatches += re.findall(r"'([^'\n]{3,})'", parsed)
                if qmatches:
                    titles_list = [s.strip() for s in qmatches][:3]
                else:
                    titles_list = to_list_of_strings(parsed)

            # Final cleanup: ensure list and exactly 3 items
            if not isinstance(titles_list, list):
                titles_list = [str(titles_list)]
            titles_list = [t for t in titles_list if t]
            # If more than 3, take first 3; if fewer, fail later
            if len(titles_list) >= 3:
                titles_list = titles_list[:3]

            parsed = {"titles": titles_list, "article_indices": [0, 1, 2]}
            try:
                out = TitlesOutput(**parsed)
                if len(out.titles) != 3:
                    raise ValueError(f"LLM did not return exactly 3 titles (got {len(out.titles)})")
                return out
            except Exception as validation_error:
                # If TitlesOutput validation fails, raise to trigger fallback
                raise RuntimeError(f"TitlesOutput validation failed: {validation_error}") from validation_error
        except Exception as e:
            # Log raw model output for debugging
            import traceback
            print("[TitleChain] Failed to parse model output:", e)
            print("[TitleChain] Traceback:", traceback.format_exc())
            print("[TitleChain] Raw output:", res)

            # Final fallback: try to heuristically extract three title-like strings
            qmatches = re.findall(r'"([^"\n]{3,})"', res)
            qmatches += re.findall(r"'([^'\n]{3,})'", res)

            candidates = []
            for m in qmatches:
                s = m.strip()
                if s and s not in candidates:
                    candidates.append(s)
                if len(candidates) >= 3:
                    break

            if len(candidates) < 3:
                # fallback to line-based extraction
                lines = [l.strip(" -*\t\r") for l in res.splitlines() if l.strip()]
                for l in lines:
                    # ignore lines that look like JSON or labels
                    if any(ch in l for ch in ["{", "}", ":", "[", "]"]):
                        continue
                    if len(l) < 5:
                        continue
                    if l not in candidates:
                        candidates.append(l)
                    if len(candidates) >= 3:
                        break

            if len(candidates) == 3:
                parsed = {"titles": candidates, "article_indices": [0, 1, 2]}
                try:
                    out = TitlesOutput(**parsed)
                    return out
                except Exception:
                    pass

            # As a last resort, synthesize three fallback titles from the provided articles
            fallback = []
            for idx, a in enumerate(articles[:3]):
                t = a.title or (a.description or "Untitled")
                # simple rewrite heuristics
                if idx == 0:
                    fallback.append(f"Inside: {t}")
                elif idx == 1:
                    fallback.append(f"What This Means: {t}")
                else:
                    fallback.append(f"Spotlight — {t}")

            # if fewer than 3 articles, duplicate with suffixes
            i = 0
            while len(fallback) < 3:
                fallback.append(fallback[i % max(1, len(fallback))] + f" ({len(fallback)+1})")
                i += 1

            print("[TitleChain] Returning fallback titles:", fallback)
            return TitlesOutput(titles=fallback, article_indices=[0, 1, 2])


__all__ = ["TitleChain"]