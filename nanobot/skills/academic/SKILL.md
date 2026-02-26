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

### 2. Generate Hypothesis Prompts

Help the user formulate a hypothesis by searching for initial context and gaps. Use the search results provided by this command to suggest 2-3 specific hypotheses to the user.

```bash
python3 -m nanobot.skills.academic.research hypothesis "specific topic"
```

### 3. Search for Sources

Find academic papers, articles, and books. Results include abstracts and Open Access PDF links when available.

```bash
python3 -m nanobot.skills.academic.research search "query" --limit 5
```

### 4. Lookup Paper Details

Get full details, abstract, and BibTeX for a specific paper using its OpenAlex ID (e.g., `W2741809807`) or DOI (e.g., `10.1371/journal.pone.0266781`).

```bash
python3 -m nanobot.skills.academic.research lookup "W2741809807"
```

### 5. Find Related Papers

Find papers related to a specific paper ID.

```bash
python3 -m nanobot.skills.academic.research related "W2741809807" --limit 5
```

### 6. Generate BibTeX

Generate a BibTeX entry for a specific paper ID.

```bash
python3 -m nanobot.skills.academic.research bibtex "W2741809807"
```

### 7. Generate Annotated Bibliography

Create a list of sources with citation counts and abstracts, suitable for a bibliography.

```bash
python3 -m nanobot.skills.academic.research bibliography "query"
```

## Tips

- Use specific keywords for better search results.
- `search` sorts by publication date (newest first).
- `bibliography` sorts by citation count (impact).
- The output includes abstracts. Use these to summarize findings without needing to browse external URLs immediately.
- Use `lookup` to get deep details on a paper you found via `search`.
- Use `related` to traverse the citation graph and find similar works.
