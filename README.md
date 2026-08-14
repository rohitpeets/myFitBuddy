# 👕 FitFindr

FitFindr is an AI-powered thrift shopping assistant that helps users discover secondhand clothing, generate outfit recommendations using their wardrobe, and create shareable social-media-style fit cards.

The agent follows a structured planning workflow that:

1. Parses a user's shopping request
2. Searches a secondhand clothing dataset
3. Suggests outfit combinations
4. Generates a TikTok/Instagram-style caption

---

# Project Structure

```text
fitfindr/
├── agent.py                   # Planning loop and session management
├── app.py                     # Gradio user interface
├── tools.py                   # Core agent tools
├── planning.md                # Design and planning documentation
├── README.md                  # Project documentation
├── test_app.py                # CLI testing script
├── requirements.txt           # Python dependencies
│
├── data/
│   ├── listings.json          # Mock thrift listings dataset
│   └── wardrobe_schema.json   # Wardrobe schema and example wardrobe
│
└── utils/
    └── data_loader.py         # Dataset loading utilities
```

---

# Installation

Install project dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_api_key_here
```

---

# Tool Inventory

## Tool 1: search_listings()

### Purpose

Search the thrift listings dataset and return relevant listings based on user preferences.

### Inputs

| Parameter   | Type         | Description                                 |
| ----------- | ------------ | ------------------------------------------- |
| description | str          | Keywords describing the item the user wants |
| size        | str | None   | Optional size filter                        |
| max_price   | float | None | Optional maximum price filter               |

### Output

```python
list[dict]
```

Returns matching listings sorted by relevance.

### Failure Handling

Returns an empty list if no listings match the query.

---

## Tool 2: suggest_outfit()

### Purpose

Generate outfit recommendations using the selected thrifted item and the user's wardrobe.

### Inputs

| Parameter | Type | Description             |
| --------- | ---- | ----------------------- |
| new_item  | dict | Selected thrift listing |
| wardrobe  | dict | User wardrobe data      |

### Output

```python
str
```

Returns an outfit recommendation.

### Failure Handling

If the wardrobe is empty, the tool generates general styling advice instead of specific outfit combinations.

No exception is raised.

---

## Tool 3: create_fit_card()

### Purpose

Generate a social-media-style caption for the selected outfit.

### Inputs

| Parameter | Type | Description             |
| --------- | ---- | ----------------------- |
| outfit    | str  | Outfit recommendation   |
| new_item  | dict | Selected thrift listing |

### Output

```python
str
```

Returns a 2–4 sentence Instagram/TikTok-style caption.

### Failure Handling

If outfit information is missing, a descriptive error message is returned instead of raising an exception.

---

# How the Planning Loop Works

The agent follows a sequential workflow where each step depends on the previous step.

## Step 1: Parse User Query

The user's natural-language request is parsed into structured search criteria:

```python
{
    "description": "vintage graphic tee",
    "size": None,
    "max_price": 30.0
}
```

---

## Step 2: Search Listings

The agent calls:

```python
search_listings(description, size, max_price)
```

### Decision Point

If no results are found:

```python
session["error"] = "No listings found..."
```

The agent exits early and does not continue.

If results are found:

```python
session["selected_item"] = results[0]
```

The highest-ranked listing is selected.

---

## Step 3: Generate Outfit Recommendation

The agent calls:

```python
suggest_outfit(selected_item, wardrobe)
```

If wardrobe items exist:

* Generate specific outfit combinations using named wardrobe pieces.

If wardrobe is empty:

* Generate general styling advice.

---

## Step 4: Create Fit Card

The agent calls:

```python
create_fit_card(outfit_suggestion, selected_item)
```

The tool generates a short social-media-ready caption.

---

## Step 5: Return Results

The final outputs are returned to the Gradio interface:

* Top listing found
* Outfit recommendation
* Fit card caption

---

# State Management

FitFindr uses a shared session dictionary to store and pass information between tools.

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

## Data Flow

| Field             | Created By        | Used By                             |
| ----------------- | ----------------- | ----------------------------------- |
| query             | _new_session()    | Query Parser                        |
| parsed            | Query Parser      | search_listings()                   |
| search_results    | search_listings() | Item Selection                      |
| selected_item     | Item Selection    | suggest_outfit(), create_fit_card() |
| wardrobe          | _new_session()    | suggest_outfit()                    |
| outfit_suggestion | suggest_outfit()  | create_fit_card()                   |
| fit_card          | create_fit_card() | UI Output                           |
| error             | Any Step          | app.py                              |

Each tool reads from and writes to the session dictionary instead of directly passing data to another tool.

---

# Error Handling Strategy

## search_listings()

### Failure Mode

No matching listings are found.

### Agent Response

```python
session["error"] = (
    "No listings found matching your search. "
    "Try different keywords, a different size, "
    "or a higher price limit."
)
```

The planning loop exits immediately.

### Example Test

Query:

```text
designer ballgown size XXS under $5
```

Result:

```text
No listings found matching your search.
```

---

## suggest_outfit()

### Failure Mode

The wardrobe is empty.

### Agent Response

Generate general styling advice.

### Example

Instead of:

```text
Pair with your Levi's jeans...
```

The tool returns:

```text
Graphic tees pair well with baggy jeans, cargo pants,
and chunky sneakers for a relaxed vintage aesthetic.
```

---

## create_fit_card()

### Failure Mode

Outfit information is missing.

### Agent Response

Return:

```text
Missing outfit input — could not generate a fit card.
Make sure suggest_outfit() ran successfully.
```

No exception is raised.

---

# Example Interaction

## User Query

```text
I'm looking for a vintage graphic tee under $30.
```

## Selected Listing

```text
Vintage Nirvana Band Tee
$22.00
Depop
```

## Outfit Suggestion

```text
Pair the Nirvana tee with baggy Levi's and white Air Force 1s
for a laid-back 90s look.
```

## Fit Card

```text
Thrifted this Nirvana tee on Depop for $22 and I'm not okay 🖤
Baggy jeans, chunky sneakers, done.
Slow fashion forever.
```

---

# Spec Reflection

## How the Spec Helped

The planning document provided a clear structure before implementation began. Defining tool inputs, outputs, and failure modes beforehand made it easier to generate and verify code for each component independently.

## How Implementation Diverged

The original specification assumed simple size matching. During implementation, size matching was expanded to support partial matches such as "M" matching "S/M" because it produced more useful search results and improved the user experience.

---

# AI Usage

## Example 1

I used Claude to generate the implementation of `search_listings()` using the tool specification from `planning.md`.

After reviewing the generated code, I validated it using:

* A query with a strict price limit
* A query expected to return one result
* A query expected to return no results

I adjusted the keyword scoring logic to improve result ranking.

---

## Example 2

I used Claude to generate the `run_agent()` planning loop using the Planning Loop, State Management, and Architecture sections from `planning.md`.

After testing, I revised the generated code to ensure the agent exited immediately when `search_listings()` returned an empty list and correctly populated the session dictionary on successful runs.

---

# Features

* AI-powered query understanding
* Thrift listing search
* Wardrobe-aware outfit recommendations
* Social-media-style caption generation
* Session-based planning architecture
* Graceful error handling
* Gradio web interface

---

# Future Improvements

* Image-based fashion search
* Personalized style profiles
* Saved wardrobes
* Multi-item outfit generation
* Marketplace integrations
* Improved recommendation ranking
