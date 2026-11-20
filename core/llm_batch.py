"""Batched LLM requests: many sentences or subtitle lines per request.

Enabled with `llm_batching: true`. Each request carries up to `llm_batch_size`
items with ids; the reply is checked item by item. An item that is missing or
malformed in the reply is not retried with another request: it takes the same
no-LLM fallback the per-item path uses when the model fails (a mechanical
split, or keeping the line as it is), so a bad reply never multiplies requests.
"""

import json
import re
from difflib import SequenceMatcher

from rich.console import Console

from core.task_runner import StopTask
from core.utils import ask_gpt, check_cancel, get_source_language, load_key, load_key_or

console = Console()

BR = re.compile(r'\[\s*/?\s*br\s*/?\s*\]|<\s*/?\s*br\s*/?\s*>', re.IGNORECASE)


def batch_size():
    return max(1, int(load_key_or("llm_batch_size", 60) or 60))


def groups(items):
    size = batch_size()
    return [list(range(k, min(k + size, len(items)))) for k in range(0, len(items), size)]


def _same_text(a, b):
    a, b = re.sub(r"\s+", "", a), re.sub(r"\s+", "", b)
    return SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.9


def _ask(prompt, title, valid):
    """The JSON reply, or None when the request itself failed (e.g. quota)."""
    check_cancel()
    try:
        return ask_gpt(prompt, resp_type="json", valid_def=valid, log_title=title)
    except StopTask:
        raise
    except Exception as error:  # quota, network, unparseable reply
        console.print(f"[yellow]⚠️ Batched {title} request failed ({error}); using the no-LLM fallback for it[/yellow]")
        return None


def _by_id(reply, key):
    out = {}
    for item in (reply or {}).get(key) or []:
        if isinstance(item, dict) and str(item.get("id", "")).strip().isdigit():
            out[int(str(item["id"]).strip())] = item
    return out


# ------------------------------------------------------------------
# Sentence splitting
# ------------------------------------------------------------------

def split_prompt(batch):
    language = get_source_language()
    payload = [{"id": i + 1, "parts": parts, "max_words": limit, "text": sentence}
               for i, (sentence, parts, limit) in enumerate(batch)]
    return f"""
## Role
You are a professional Netflix subtitle splitter in **{language}**.

## Task
Each item below is one subtitle text. Split every item into exactly its `parts` number of parts,
each under `max_words` words, by inserting [br] at the split positions.

1. Keep the meaning of each part coherent, following Netflix subtitle standards
2. MOST IMPORTANT: keep the parts of an item roughly equal in length (at least 3 words each)
3. Split at natural points such as punctuation marks or conjunctions
4. Copy the text of each item exactly; only insert [br]. Never merge, drop or reorder items
5. For repeated words, split in the middle of the repetition

## Items
```json
{json.dumps(payload, ensure_ascii=False, indent=1)}
```

## Output in only JSON format and no other text
```json
{{"splits": [{{"id": 1, "split": "first part [br] second part"}}]}}
```
Return one entry per item id. Start your answer with ```json and end with ```.
""".strip()


def batch_split(items):
    """[(sentence, num_parts, word_limit)] -> [newline-joined parts] in one request per group."""
    from core._3_2_split_meaning import apply_split, mechanical_split
    results = [None] * len(items)
    for ids in groups(items):
        batch = [items[i] for i in ids]
        reply = _ask(split_prompt(batch), "split_by_meaning_batch",
                     lambda r: {"status": "success" if isinstance(r, dict) and isinstance(r.get("splits"), list)
                                else "error", "message": "expected a `splits` list"})
        answers = _by_id(reply, "splits")
        ok = 0
        for n, (i, (sentence, parts, _)) in enumerate(zip(ids, batch), 1):
            marked = BR.sub("[br]", str((answers.get(n) or {}).get("split", "")))
            pieces = [p for p in marked.split("[br]")]
            if len(pieces) >= 2 and all(p.strip() for p in pieces) and _same_text(marked.replace("[br]", ""), sentence):
                lines = [line.strip() for line in apply_split(sentence, marked).split("\n") if line.strip()]
                if len(lines) >= 2:
                    results[i] = "\n".join(lines)
                    ok += 1
                    continue
            results[i] = mechanical_split(sentence, parts)
        console.print(f"[green]✅ Split {ok}/{len(ids)} sentences in one request"
                      f"{'' if ok == len(ids) else ' (the rest split mechanically)'}[/green]")
    return results


# ------------------------------------------------------------------
# Subtitle alignment
# ------------------------------------------------------------------

def align_prompt(batch):
    src_lang, targ_lang = get_source_language(), load_key("target_language")
    payload = [{"id": i + 1, "source": src, "translation": tr, "source_parts": parts}
               for i, (src, tr, parts) in enumerate(batch)]
    return f"""
## Role
You are a Netflix subtitle alignment expert fluent in both {src_lang} and {targ_lang}.

## Task
Each item has a {src_lang} subtitle, its {targ_lang} translation, and the {src_lang} subtitle already
split into `source_parts`. Split each {targ_lang} translation into the same number of parts so that
part k corresponds to source part k.

1. Follow the word order and structure of each pair
2. Never leave a part empty; if the meaning is hard to split, you may lightly rewrite the translation
3. Do not add comments or explanations; the subtitles are for the audience to read

## Items
```json
{json.dumps(payload, ensure_ascii=False, indent=1)}
```

## Output in only JSON format and no other text
```json
{{"aligns": [{{"id": 1, "target_parts": ["part 1", "part 2"]}}]}}
```
Return one entry per item id, with exactly as many target_parts as that item's source_parts.
Start your answer with ```json and end with ```.
""".strip()


def batch_align(items):
    """[(src, tr, src_parts)] -> [target parts or None] in one request per group."""
    results = [None] * len(items)
    for ids in groups(items):
        batch = [items[i] for i in ids]
        reply = _ask(align_prompt(batch), "align_subs_batch",
                     lambda r: {"status": "success" if isinstance(r, dict) and isinstance(r.get("aligns"), list)
                                else "error", "message": "expected an `aligns` list"})
        answers = _by_id(reply, "aligns")
        for n, (i, (_, _, src_parts)) in enumerate(zip(ids, batch), 1):
            parts = (answers.get(n) or {}).get("target_parts")
            if (isinstance(parts, list) and len(parts) == len(src_parts)
                    and all(isinstance(p, str) and p.strip() for p in parts)):
                results[i] = [p.strip() for p in parts]
    return results
