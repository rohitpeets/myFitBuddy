# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
The tool loads a dataset of listings and accepts 3 fields: the keywords describing what the user is looking for, the desired size, and the maximum price.
**Input parameters:**
- `description` (str):Keywords describing what the user is looking for.
- `size` (str):Size string to filter by, or None to skip size filtering. Matching is case-insensitive - "M" matches "S/M".
- `max_price` (float):Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
A list of matching listing dicts , sorted by relevance.

**What happens if it fails or returns nothing:**
It returns an empty list if nothing matches.

---

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item and the user's wardrobe, it generates one or more outfit recommendations.
**Input parameters:**
- `new_item` (dict):It is a listing dictionary representing the item the user is looking to buy.
- `wardrobe` (dict):A wardrobe dict containing an items key
**What it returns:**
It returns a non empty string with an outfit suggestion and if the wardrobe is empty it gives general styling advice without raising an exception or returning an empty string.
**What happens if it fails or returns nothing:**
It should not throw an exception or an empty string.If the wardrobe is empty, it should give general styling advice (for example : what are the common items to pair this up with, etc)
---

### Tool 3: create_fit_card

**What it does:**
It generates a short sharable caption for the thrifted outfit by using information from the input parameters.
**Input parameters:**
- `outfit` (str): The outfit suggestion string from suggest_outfit().
-  `new_item` (dict):The listing dict for the thrifted item.
**What it returns:**
A 2-4 sentence string that can be used as instagram/TikTok caption for that thrifted outfit.
  The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

**What happens if it fails or returns nothing:**
It should not raise an exception but should provide a descriptive error message.
Return a descriptive error message indicating which input is missing. Do not raise an exception.

### Additional Tools (if any)


---

## Planning Loop

**How does your agent decide which tool to call next?**
First, the search_listings() runs and returns a list.
if empty,
        returns an error message specifying that no relevent messages could be found and that user should try again with a different input.
If not empty,
        session["selected_item"] = results[0] and proceed to suggest_outfit().
        
        suggest_outfit() checks whether wardrobe["items"] is empty.        
        if empty,
               general styling ideas(what kinds of items pair well, what vibe it suits, etc.).
        if not empty,
                suggest specific outfit combinations using the new item and named pieces from the wardrobe and return a string.
                
                then proceed with create_fit_card().

                create_fit_finder: create a shareable outfit caption for social platforms like instagram or TikTok. 
                If an input parameter is not available: give an error message with the context.
               
---

## State Management

**How does information from one tool get passed to the next?**
A single session dict is reponsible for managing state and carring data between different tools. No data is transferred directly. Each step reads input from the session dict and writes output into it which is read by the next step.

_new_session() - Creates - session["query"]
session["query"] - Read By - query parser - Creates - session["parsed"]
session["parsed"] - Read By - search_listings() - Creates - session["search_results"]

item selection - Uses - session["search_results"]
session["selected items"]= results[0]

_new_session() - Creates - session["wardrobe"]
session["selected items"]= results[0] and session["wardrobe"] - Read By - suggest_outfit() - Creates - session["outfit_suggestion"] 

session["outfit_suggestion"] and session["selected_items"]= results[0] - Reads - create_fit_card() - Creates - session["fit_card"]



---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set session["error"] = "No listings found matching your search. Try different keywords, a different size, or a higher price limit." Return the session immediately — do not call suggest_outfit or create_fit_card. app.py displays the error in the listing panel and leaves the other two panels empty.|
| suggest_outfit | Wardrobe is empty | Switch to a general styling prompt: ask the LLM what types of items pair well with the new piece and what aesthetic it suits. Return that string — never return an empty string or raise an exception.|
| create_fit_card | Outfit input is missing or incomplete | Return the error string "Missing outfit input — could not generate a fit card. Make sure suggest_outfit() ran successfully." Do not raise an exception.|

---

## Architecture

     User input (query, wardrobe_choice)
        │
        ▼
  handle_query()  [app.py]
        │
        ▼
   run_agent()  [agent.py]
        │
        ▼
┌───────────────────────────────────────────┐
│             SESSION DICT                  │
│  query, parsed, search_results,           │
│  selected_item, wardrobe,                 │
│  outfit_suggestion, fit_card, error       │
└───────────────────────────────────────────┘
        │
        ▼
  Step 1: Parse query (LLM → JSON)
        │
        ▼
  Step 2: search_listings(description, size, max_price)
        │
        ├── empty list ──► set session["error"] ──► return session early
        │
        └── results ──► session["selected_item"] = results[0]
                │
                ▼
          Step 3: suggest_outfit(selected_item, wardrobe)
                │
                ├── wardrobe empty ──► LLM: general styling advice
                │
                └── wardrobe has items ──► LLM: specific outfit combos
                        │
                        ▼
                  Step 4: create_fit_card(outfit_suggestion, selected_item)
                        │
                        ▼
                  return session
                        │
                        ▼
              handle_query() formats output
              → (listing_text, outfit_suggestion, fit_card)
                        │
                        ▼
              Gradio displays 3 output panels

---

## AI Tool Plan


**Individual tool implementations:**
Tool 1 - search_listings()
i will give claude the spec for tool 1 from planning.md ,The planning loop, The state management information and the Architecture ,and ask it to implement search_listings(). i will then verify the code generated by reading through it to understand its working and run 3 test queries.
- One with a tight price filter.
- One that should return one result.
- One that should return an empty string.
At last, I will check the outputs and validate them.
Tool 2- I will give claude the spec for tool 2 from planning.md, the planning loop , the state management information and the architecture information ,and ask it to implement the tool. I will then test it using a sample new_item() dict , a sample wardrobe and an empty wardrobe and validate the outputs.
Tool 3 - I will give claude the Tool 3 spec from planning.md, the planning loop , the state management and the architecture info ,and ask it to implement the tool. I will them run test cases including one with an empty outfit string and another time with a sample outfit string. i will validate the outputs to make sure they meet the standard.

**Planning loop and state management:**
I will give Claude the Planning Loop section, the State Management table, the Architecture diagram, and the _new_session() skeleton from agent.py, and ask it to implement run_agent().I expect it to produce a function that: parses the query using the LLM, calls the three tools in order, writes results into the session dict at each step, and exits early with session["error"] if search_listings returns empty. I will verify by running the two CLI test cases already in agent.py — the happy path ("vintage graphic tee under $30") and the no-results path ("designer ballgown size XXS under $5") — and checking that the happy path populates all three session output fields and the no-results path sets session["error"] with no outfit or fit card.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
run_agent() initializes the session with _new_session(). It calls the LLM to parse the query into structured fields. The LLM returns {"description": "vintage graphic tee", "size": None, "max_price": 30.0} — no size was mentioned so size is None. This is stored in session["parsed"].

**Step 2:**

search_listings("vintage graphic tee", size=None, max_price=30.0) is called. It loads all listings, drops any priced above $30 (size filter skipped), then scores the rest by keyword overlap with "vintage graphic tee" against each listing's title, description, style_tags, category, and brand. Listings scoring 0 are dropped. Suppose 3 listings match — they are returned sorted by score. session["search_results"] = those 3 dicts. session["selected_item"] = results[0], e.g. {"title": "Vintage Nirvana Band Tee", "price": 22.0, "platform": "Depop", "size": "M", "style_tags": ["vintage", "grunge"], "colors": ["black"]}.
**Step 3:**
suggest_outfit(session["selected_item"], session["wardrobe"]) is called. The wardrobe has items, so the LLM is prompted with the item details and the full wardrobe list and asked for 1–2 specific outfit combinations using named wardrobe pieces. It returns: "Pair the Nirvana tee with your baggy Levi's and white Air Force 1s for a laid-back 90s look. Or tuck it into your plaid mini skirt with chunky boots for a grunge-lite vibe." Stored in session["outfit_suggestion"].

Then create_fit_card(session["outfit_suggestion"], session["selected_item"]) is called. The LLM generates a casual caption: "thrifted this nirvana tee on depop for $22 and i'm not okay 🖤 baggy jeans, chunky sneakers, done. slow fashion forever." Stored in session["fit_card"]. run_agent()
**Final output to user:**
handle_query() in app.py checks session["error"] — it's None, so no early exit. It formats session["selected_item"] and returns all three strings to Gradio:


🛍️ Top listing found: Vintage Nirvana Band Tee | $22.00 | Size: M | Condition: Good | Platform: Depop | Style: vintage, grunge | Colors: black
👗 Outfit idea: Pair the Nirvana tee with your baggy Levi's and white Air Force 1s for a laid-back 90s look. Or tuck it into your plaid mini skirt with chunky boots for a grunge-lite vibe.
✨ Your fit card: thrifted this nirvana tee on depop for $22 and i'm not okay 🖤 baggy jeans, chunky sneakers, done. slow fashion forever.
