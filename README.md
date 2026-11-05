# FitFindr

An AI thrift-shopping assistant. You describe what you're looking for, and FitFindr finds a secondhand listing, suggests outfits using clothes you already own, and writes a short TikTok/Instagram-style caption for the look. It runs as a Gradio app on Groq-hosted models.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_api_key_here
```

## Project structure

```text
fitfindr/
├── agent.py                   # Planning loop and session management
├── app.py                     # Gradio user interface
├── tools.py                   # Core agent tools
├── planning.md                # Design and planning document
├── test_app.py                # CLI testing script
├── requirements.txt
├── data/
│   ├── listings.json          # Mock thrift listings dataset
│   └── wardrobe_schema.json   # Wardrobe schema and example wardrobe
└── utils/
    └── data_loader.py         # Dataset loading utilities
```

## Tools

| Tool | Inputs | Returns | When it can't do its job |
|---|---|---|---|
| `search_listings()` | `description: str`, `size: str \| None`, `max_price: float \| None` | `list[dict]` of listings sorted by relevance | Returns an empty list |
| `suggest_outfit()` | `new_item: dict`, `wardrobe: dict` | `str` outfit recommendation | With an empty wardrobe, gives general styling advice instead |
| `create_fit_card()` | `outfit: str`, `new_item: dict` | `str`, a 2 to 4 sentence caption | With no outfit, returns an error message instead of raising |

## How the planning loop works

The agent runs the steps in order, and each step depends on the one before it.

1. Parse the request into search criteria, for example `{"description": "vintage graphic tee", "size": None, "max_price": 30.0}`.
2. Call `search_listings(description, size, max_price)`. If nothing matches, set `session["error"]` and stop. Otherwise take the top result as `session["selected_item"]`.
3. Call `suggest_outfit(selected_item, wardrobe)`. It names specific wardrobe pieces when the wardrobe has items, and falls back to general styling advice when it's empty.
4. Call `create_fit_card(outfit_suggestion, selected_item)` to write the caption.
5. Return the listing, outfit and caption to the Gradio interface.

## State

The tools don't pass data to each other directly. Each one reads from and writes to a shared session dictionary:

```python
session = {
    "query": "",
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": {},
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None
}
```

| Field | Written by | Read by |
|---|---|---|
| `query` | `_new_session()` | query parser |
| `parsed` | query parser | `search_listings()` |
| `search_results` | `search_listings()` | item selection |
| `selected_item` | item selection | `suggest_outfit()`, `create_fit_card()` |
| `wardrobe` | `_new_session()` | `suggest_outfit()` |
| `outfit_suggestion` | `suggest_outfit()` | `create_fit_card()` |
| `fit_card` | `create_fit_card()` | UI output |
| `error` | any step | `app.py` |

## Error handling

- No listings found: the loop stops with "No listings found matching your search. Try different keywords, a different size, or a higher price limit." Tested with `designer ballgown size XXS under $5`.
- Empty wardrobe: `suggest_outfit()` returns general advice, such as "Graphic tees pair well with baggy jeans, cargo pants, and chunky sneakers for a relaxed vintage aesthetic.", instead of naming pieces the user doesn't have.
- Missing outfit: `create_fit_card()` returns "Missing outfit input — could not generate a fit card. Make sure suggest_outfit() ran successfully." No exception is raised.

## Example

Query: `I'm looking for a vintage graphic tee under $30.`

- Listing: Vintage Nirvana Band Tee, $22.00, Depop
- Outfit: "Pair the Nirvana tee with baggy Levi's and white Air Force 1s for a laid-back 90s look."
- Fit card: "Thrifted this Nirvana tee on Depop for $22 and I'm not okay 🖤 Baggy jeans, chunky sneakers, done. Slow fashion forever."

## Spec reflection

Writing `planning.md` first meant every tool's inputs, outputs and failure modes were defined before any code existed, so I could generate and check each component on its own.

The spec assumed exact size matching. During implementation I extended it to partial matches (so "M" matches "S/M") because it returned more useful results.

## AI usage

- I had Claude implement `search_listings()` from the tool spec in `planning.md`. I tested it with a strict price limit, a query expected to return one result, and a query expected to return none, then adjusted the keyword scoring to improve the ranking.
- I had Claude write the `run_agent()` planning loop from the planning, state and architecture sections of `planning.md`. After testing, I fixed it so the agent exits as soon as `search_listings()` returns an empty list and fills in the session dictionary correctly on successful runs.

## Possible next steps

Image-based search, saved wardrobes and style profiles, multi-item outfits, better ranking, and real marketplace integrations.
