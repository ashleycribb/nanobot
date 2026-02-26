---
name: academic
description: Academic research assistant for finding topics, hypotheses, and sources.
metadata: {"nanobot":{"emoji":"🎓","requires":{"python_modules":["httpx","typer","rich"]}}}
---

# Academic Research Assistant

Use this skill to help researchers find topics, generate hypotheses, and search for academic sources.
The skill uses the OpenAlex API via a Python script.

## Commands

### 1. Find Research Topics

If the user needs help finding a research topic, search for general areas of interest.

```bash
python3 -m nanobot.skills.academic.research topics "general area"
```

Example:
```bash
python3 -m nanobot.skills.academic.research topics "artificial intelligence agents"
```

### 2. Generate Hypothesis Prompts

Help the user formulate a hypothesis by generating prompts and finding initial gaps.

```bash
python3 -m nanobot.skills.academic.research hypothesis "specific topic"
```

Example:
```bash
python3 -m nanobot.skills.academic.research hypothesis "LLM hallucinations"
```

### 3. Search for Sources

Find academic papers, articles, and books. Results include abstracts when available.

```bash
python3 -m nanobot.skills.academic.research search "query" --limit 5
```

Example:
```bash
python3 -m nanobot.skills.academic.research search "transformer architecture" --limit 10
```

### 4. Generate Annotated Bibliography

Create a list of sources with citation counts and abstracts, suitable for a bibliography.

```bash
python3 -m nanobot.skills.academic.research bibliography "query"
```

Example:
```bash
python3 -m nanobot.skills.academic.research bibliography "reinforcement learning"
```

## Tips

- Use specific keywords for better search results.
- `search` sorts by publication date (newest first).
- `bibliography` sorts by citation count (impact).
- The output includes abstracts. Use these to summarize findings without needing to browse external URLs immediately.
