"""Research assistant CLI tool."""

import httpx
import typer
from rich import print
import sys
import re

app = typer.Typer()

OPENALEX_API_URL = "https://api.openalex.org"

def _fetch(endpoint: str, params: dict) -> dict:
    try:
        response = httpx.get(f"{OPENALEX_API_URL}/{endpoint}", params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        return {}
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        return {}

def _reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""

    words = []
    for word, indices in inverted_index.items():
        for index in indices:
            words.append((index, word))

    words.sort(key=lambda x: x[0])
    return " ".join(w[1] for w in words)

def _clean_bibtex_key(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', text)

def _print_bibtex(item: dict):
    """Generate and print BibTeX."""
    title = item.get("title", "No Title") or "No Title"
    authorships = item.get("authorships", [])

    first_author_last = "Unknown"
    if authorships:
        author = authorships[0].get("author", {})
        display_name = author.get("display_name", "")
        if display_name:
            first_author_last = display_name.split()[-1]

    year = item.get("publication_year") or 0
    first_word = title.split()[0] if title else "Title"

    bib_key = f"{first_author_last}{year}{first_word}"
    bib_key = _clean_bibtex_key(bib_key)

    # Authors list
    author_names = []
    for a in authorships:
        name = a.get("author", {}).get("display_name", "")
        if name:
            author_names.append(name)
    authors_bib = " and ".join(author_names) if author_names else "Unknown"

    venue_info = item.get("primary_location", {}) or {}
    source = venue_info.get("source", {}) or {}
    venue = source.get("display_name", "Unknown Venue")

    doi = item.get("doi", "")

    print("\n[yellow]BibTeX:[/yellow]")
    print(f"@article{{{bib_key},")
    print(f"  title = {{{title}}},")
    print(f"  author = {{{authors_bib}}},")
    print(f"  journal = {{{venue}}},")
    print(f"  year = {{{year}}},")
    if doi:
        print(f"  doi = {{{doi.replace('https://doi.org/', '')}}},")
    print("}")

def _print_work(item: dict, full_abstract: bool = False, show_bibtex: bool = False):
    """Print work details."""
    title = item.get("title", "No Title")
    authorships = item.get("authorships", [])

    author_names = []
    for a in authorships[:5]: # limit to 5 authors for display
        name = a.get("author", {}).get("display_name", "")
        if name:
            author_names.append(name)
    if len(authorships) > 5:
        author_names.append("et al.")
    authors = ", ".join(author_names)

    year = item.get("publication_year", "")
    doi = item.get("doi", "")
    work_id = item.get("id", "").replace("https://openalex.org/", "")

    # Open Access
    oa = item.get("open_access", {})
    oa_url = oa.get("oa_url")
    is_oa = oa.get("is_oa", False)

    # Venue
    loc = item.get("primary_location", {}) or {}
    source = loc.get("source", {}) or {}
    venue = source.get("display_name", "Unknown Venue")

    abstract_idx = item.get("abstract_inverted_index")
    abstract = _reconstruct_abstract(abstract_idx)

    print(f"\n[bold]{title}[/bold] (ID: {work_id})")
    print(f"Authors: {authors}")
    print(f"Published in: {venue} ({year})")
    if doi:
        print(f"DOI: {doi}")
    if is_oa and oa_url:
        print(f"[green]Open Access PDF:[/green] {oa_url}")

    if abstract:
        if full_abstract:
             print(f"\n[bold]Abstract:[/bold]\n{abstract}")
        else:
            display_abstract = abstract[:500] + "..." if len(abstract) > 500 else abstract
            print(f"[dim]Abstract: {display_abstract}[/dim]")

    if show_bibtex:
        _print_bibtex(item)

@app.command()
def topics(query: str):
    """Find research topics related to a query."""
    data = _fetch("topics", {"search": query})
    results = data.get("results", [])

    if not results:
        print(f"No topics found for '{query}'.")
        return

    print(f"[bold]Research topics related to '{query}':[/bold]")
    for item in results[:5]:
        name = item.get("display_name", "Unknown")
        desc = item.get("description", "No description")
        print(f"- [cyan]{name}[/cyan]: {desc}")

@app.command()
def search(query: str, limit: int = 5):
    """Search for academic papers."""
    data = _fetch("works", {"search": query, "per-page": limit, "sort": "publication_date:desc"})
    results = data.get("results", [])

    if not results:
        print(f"No papers found for '{query}'.")
        return

    for item in results:
        _print_work(item)

@app.command()
def lookup(work_id: str):
    """Lookup a paper by OpenAlex ID or DOI."""
    # Handle DOI input
    if work_id.startswith("10."):
        work_id = f"https://doi.org/{work_id}"

    endpoint = f"works/{work_id}"
    # If full URL provided, extract ID
    if "openalex.org/works/" in work_id:
        endpoint = f"works/{work_id.split('/')[-1]}"

    try:
        response = httpx.get(f"{OPENALEX_API_URL}/{endpoint}", timeout=10.0)
        response.raise_for_status()
        item = response.json()
        _print_work(item, full_abstract=True, show_bibtex=True)
    except httpx.HTTPError as e:
         print(f"[bold red]Error looking up '{work_id}':[/bold red] {e}")

@app.command()
def related(work_id: str, limit: int = 5):
    """Find related papers based on a given paper ID."""

    # First resolve the paper ID to get its concept/related works
    try:
        # Handle DOI input
        if work_id.startswith("10."):
            lookup_id = f"https://doi.org/{work_id}"
        elif not work_id.startswith("http") and not work_id.startswith("W"):
            lookup_id = work_id # Assuming simple ID
        else:
            lookup_id = work_id

        endpoint = f"works/{lookup_id}"
        if "openalex.org/works/" in lookup_id:
            endpoint = f"works/{lookup_id.split('/')[-1]}"

        response = httpx.get(f"{OPENALEX_API_URL}/{endpoint}", timeout=10.0)
        response.raise_for_status()
        item = response.json()

        print(f"[bold]Finding papers related to: {item.get('title')}[/bold]")

        related_urls = item.get("related_works", [])
        if not related_urls:
            print(f"No related works found for {work_id}")
            return

        # Limit the number of IDs to fetch
        related_urls = related_urls[:limit]

        # Build filter query: ids.openalex:url1|url2...
        filter_query = "|".join(related_urls)

        data = _fetch("works", {"filter": f"ids.openalex:{filter_query}"})
        results = data.get("results", [])

        for res in results:
            _print_work(res)

    except httpx.HTTPError as e:
         print(f"[bold red]Error finding related works for '{work_id}':[/bold red] {e}")

@app.command()
def bibtex(work_id: str):
    """Generate BibTeX for a paper."""
    try:
        if work_id.startswith("10."):
             work_id = f"https://doi.org/{work_id}"

        endpoint = f"works/{work_id}"
        if "openalex.org/works/" in work_id:
            endpoint = f"works/{work_id.split('/')[-1]}"

        response = httpx.get(f"{OPENALEX_API_URL}/{endpoint}", timeout=10.0)
        response.raise_for_status()
        item = response.json()
        _print_bibtex(item)
    except httpx.HTTPError as e:
        print(f"[bold red]Error generating BibTeX for '{work_id}':[/bold red] {e}")


@app.command()
def bibliography(query: str, limit: int = 5):
    """Generate a bibliography."""
    data = _fetch("works", {"search": query, "per-page": limit, "sort": "cited_by_count:desc"})
    results = data.get("results", [])

    if not results:
        print(f"No papers found for '{query}'.")
        return

    print(f"# Bibliography for '{query}'\n")
    for item in results:
        _print_work(item, full_abstract=False, show_bibtex=False)
        print()

@app.command()
def hypothesis(topic: str):
    """Generate hypothesis prompts."""
    print(f"[bold]Generating hypothesis prompts for '{topic}':[/bold]")
    print(f"1. Based on recent findings in {topic}, what is a gap that needs addressing?")
    print(f"2. Formulate a prediction: 'If X increases in {topic}, then Y will...'")
    print(f"3. Consider the null hypothesis: '{topic} has no effect on...'")

    print("\n[dim]Running a quick search to help form a hypothesis...[/dim]")
    search(topic, limit=3)

if __name__ == "__main__":
    app()
