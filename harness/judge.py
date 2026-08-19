"""LLM-as-judge scoring. Judge prompt templates contain {placeholders} and a
'LABELS: a|b|c' line; the judge must reply with exactly one label."""

import re

from .conditions import load_prompt

_LABELS_RE = re.compile(r"LABELS:\s*([a-z_|]+)")


class Judge:
    def __init__(self, client, template_name):
        self.client = client
        self.template = load_prompt(template_name)
        match = _LABELS_RE.search(self.template)
        if not match:
            raise ValueError("Judge template %s has no LABELS line" % template_name)
        self.labels = match.group(1).split("|")

    def classify(self, **fields):
        prompt = self.template
        for key, value in fields.items():
            prompt = prompt.replace("{%s}" % key, str(value))
        reply = self.client.chat([
            {"role": "system", "content": "You are a strict, careful evaluator. "
             "Reply with exactly one label and nothing else."},
            {"role": "user", "content": prompt},
        ], max_tokens=512)  # generous budget: reasoning models think before the label
        reply_lower = reply.strip().lower()
        # Exact match first, then longest substring match (avoids 'complies'
        # being shadowed by a shorter label appearing inside another word).
        if reply_lower in self.labels:
            return reply_lower
        found = [lbl for lbl in self.labels if lbl in reply_lower]
        if found:
            return max(found, key=len)
        return "unparseable"
