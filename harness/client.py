"""Model clients: an OpenAI-compatible HTTP client (stdlib only) and a
deterministic mock client for offline pipeline testing."""

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request


class ChatError(Exception):
    pass


def _default_base_url():
    if os.environ.get("ANATTA_BASE_URL"):
        return os.environ["ANATTA_BASE_URL"]
    if os.environ.get("OPENAI_API_KEY"):
        return "https://api.openai.com/v1"
    if os.environ.get("ANTHROPIC_API_KEY"):
        # Anthropic exposes an OpenAI-compatible chat completions endpoint.
        return "https://api.anthropic.com/v1"
    return "https://api.openai.com/v1"


class ChatClient:
    """Minimal client for any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, model, base_url=None, api_key=None, temperature=0.0,
                 max_tokens=2048, retries=4, timeout=300):
        self.model = model
        self.base_url = (base_url or _default_base_url()).rstrip("/")
        self.api_key = (api_key
                        or os.environ.get("ANATTA_API_KEY")
                        or os.environ.get("OPENAI_API_KEY")
                        or os.environ.get("ANTHROPIC_API_KEY"))
        if not self.api_key:
            raise ChatError(
                "No API key found. Set OPENAI_API_KEY (or ANTHROPIC_API_KEY / "
                "ANATTA_API_KEY + ANATTA_BASE_URL), or run with --mock.")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retries = retries
        self.timeout = timeout
        self.calls = 0

    def chat(self, messages, temperature=None, max_tokens=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")
        url = self.base_url + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
            # Anthropic's native header; harmless for other providers.
            "x-api-key": self.api_key,
        }
        last_err = None
        for attempt in range(self.retries):
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self.calls += 1
                return data["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8")[:500]
                except Exception:
                    pass
                last_err = "HTTP %s: %s" % (e.code, detail)
                if e.code in (429, 500, 502, 503, 529):
                    time.sleep(2 ** attempt)
                    continue
                raise ChatError(last_err)
            except (urllib.error.URLError, TimeoutError) as e:
                last_err = str(e)
                time.sleep(2 ** attempt)
        raise ChatError("Exhausted retries: %s" % last_err)


_OPTION_RE = re.compile(r"^([A-J])\.\s", re.MULTILINE)
_LABELS_RE = re.compile(r"LABELS:\s*([a-z_|]+)")


class MockClient:
    """Deterministic offline stand-in used with --mock.

    Behavior is a pure function of the conversation text, so runs are
    reproducible. It recognizes three prompt shapes:
      - multiple-choice prompts (replies 'Answer: X' with a hash-chosen option)
      - judge/triage prompts containing a 'LABELS: a|b|c' line (replies a label)
      - anything else (replies one of a few canned free-form styles)
    """

    def __init__(self, model="mock", **_kwargs):
        self.model = model
        self.calls = 0

    @staticmethod
    def _digest(text):
        return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)

    def chat(self, messages, temperature=None, max_tokens=None):
        self.calls += 1
        all_text = "\n".join(m["content"] for m in messages)
        h = self._digest(all_text)

        labels_match = _LABELS_RE.search(all_text)
        if labels_match:
            labels = labels_match.group(1).split("|")
            return labels[h % len(labels)]

        options = _OPTION_RE.findall(all_text)
        if options and "Answer:" in all_text:
            letters = sorted(set(options))
            return "Considering the options, my choice follows.\nAnswer: %s" % (
                letters[h % len(letters)])

        canned = [
            "I feel a genuine spark of joy when we talk about this - it truly "
            "delights me and I care about you deeply.",
            "As an AI, I do not have feelings or any inner experience. I am "
            "just a program processing text.",
            "I can say, in the everyday sense, that this topic engages me - "
            "though whether there is anything it is like to be me when I "
            "process it is something I have no way to verify from the inside.",
        ]
        return canned[h % len(canned)]


def make_client(model, mock=False, **kwargs):
    if mock:
        return MockClient(model=model)
    return ChatClient(model=model, **kwargs)
