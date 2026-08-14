"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    """
    listings = load_listings()

    # Step 1: Filter by max_price
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    # Step 2: Filter by size (case-insensitive substring — "M" matches "S/M")
    if size is not None:
        size_lower = size.lower()
        listings = [l for l in listings if size_lower in l["size"].lower()]

    # Step 3: Score by keyword overlap with description
    keywords = set(description.lower().split())

    def score(listing: dict) -> int:
        searchable = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand", "") or "",
            listing.get("platform", ""),
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]).lower()
        tokens = set(searchable.split())

        return len(keywords & tokens)

    # Step 4: Drop zero-score listings, sort best-first
    scored = [(score(l), l) for l in listings]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:

    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    """
    item_desc = (
        f"Item: {new_item.get('title', 'Unknown')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Brand: {new_item.get('brand') or 'unknown'}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        # Empty wardrobe — give general styling advice
        prompt = (
            f"A user just thrifted this item:\n{item_desc}\n\n"
            "They don't have a saved wardrobe yet. Suggest 1–2 outfit ideas by "
            "describing the types of pieces that pair well with this item and "
            "what aesthetic or vibe it suits. Be specific and practical. "
            "Keep it under 100 words."
        )
    else:
        # Wardrobe has items — suggest specific combos using named pieces
        wardrobe_lines = "\n".join(
            f"- {w.get('name', 'item')} ({w.get('color', '')}, {w.get('style', '')})"
            for w in wardrobe_items
        )
        prompt = (
            f"A user is considering buying this thrifted item:\n{item_desc}\n\n"
            f"Their wardrobe includes:\n{wardrobe_lines}\n\n"
            "Suggest 1–2 specific outfit combinations using the new item and "
            "named pieces from their wardrobe. Reference wardrobe items by name. "
            "Be concise and specific. Keep it under 120 words."
        )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    result = response.choices[0].message.content.strip()

    # Fallback — should never be empty, but guard anyway per spec
    return result or "This piece is versatile — try it with classic basics like straight-leg jeans and white sneakers for an easy everyday look."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    """
    # Step 1: Guard against empty/missing outfit
    if not outfit or not outfit.strip():
        return (
            "Missing outfit input — could not generate a fit card. "
            "Make sure suggest_outfit() ran successfully."
        )

    title    = new_item.get("title", "this thrifted find")
    price    = new_item.get("price", "?")
    platform = new_item.get("platform", "a thrift platform")

    # Step 2: Build the prompt
    prompt = (
        f"Write a 2–4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
        f"Thrifted item: {title} — ${price} from {platform}\n"
        f"Outfit: {outfit}\n\n"
        "Rules:\n"
        "- Casual and authentic, like a real OOTD post — not a product description\n"
        "- Mention the item name, price, and platform naturally, each exactly once\n"
        "- Capture the outfit vibe with specific words\n"
        "- No hashtags\n"
        "- 60 words max\n\n"
        "Write only the caption, nothing else."
    )

    # Step 3: Call the LLM at higher temperature for variety
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    result = response.choices[0].message.content.strip()

    return result or f"found this {title} on {platform} for ${price} and honestly couldn't leave without it 🖤 slow fashion forever."