"""Research assistant CLI tool."""

import httpx
import typer
from rich import print

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
        title = item.get("title", "No Title")
        authorships = item.get("authorships", [])
        authors = ", ".join([a.get("author", {}).get("display_name", "") for a in authorships])
        year = item.get("publication_year", "")
        doi = item.get("doi", "")
        abstract_idx = item.get("abstract_inverted_index")
        abstract = _reconstruct_abstract(abstract_idx)

        print(f"\n[bold]{title}[/bold]")
        print(f"Authors: {authors}")
        print(f"Year: {year}")
        if doi:
            print(f"DOI: {doi}")
        if abstract:
            # Truncate abstract if too long for display
            display_abstract = abstract[:500] + "..." if len(abstract) > 500 else abstract
            print(f"[dim]Abstract: {display_abstract}[/dim]")

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
        title = item.get("title", "No Title")
        authorships = item.get("authorships", [])
        authors = ", ".join([a.get("author", {}).get("display_name", "") for a in authorships])
        year = item.get("publication_year", "")
        doi = item.get("doi", "")
        cited_by = item.get("cited_by_count", 0)
        abstract_idx = item.get("abstract_inverted_index")
        abstract = _reconstruct_abstract(abstract_idx)

        print(f"**{title}** ({year}). {authors}.")
        if doi:
            print(f"DOI: {doi}")
        print(f"Cited by: {cited_by}")
        if abstract:
            # Truncate abstract if too long
            display_abstract = abstract[:300] + "..." if len(abstract) > 300 else abstract
            print(f"> Abstract: {display_abstract}")
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
