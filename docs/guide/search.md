# Search

The `client.search` resource provides two search methods: simple text search and JsonLogic queries.

## Simple text search

Search for text across all files in the vault:

```python
results = await client.search.simple("python asyncio")
for result in results:
    print(f"{result.filename} (score: {result.score})")
    for match in result.matches or []:
        print(f"  ...{match.context}...")
```

### Context length

Control how much surrounding text is included with each match:

```python
results = await client.search.simple("python", context_length=200)
```

## JsonLogic search

Use [JsonLogic](https://jsonlogic.com/) for programmatic query construction:

```python
results = await client.search.jsonlogic({"glob": ["*.md"]})
for result in results:
    print(result.filename)
```

## Search result structure

Each search method returns a list of `SearchResult` objects:

| Field | Type | Description |
|-------|------|-------------|
| `filename` | `str` | Path to the matching file |
| `score` | `float \| None` | Relevance score (simple search only) |
| `matches` | `list[SearchMatch] \| None` | Match locations with context (simple search only) |
| `result` | `dict[str, Any] \| list[Any] \| None` | Raw result data (JsonLogic only) |

Each `SearchMatch` contains:

| Field | Type | Description |
|-------|------|-------------|
| `match` | `MatchSpan` | Match start/end positions |
| `context` | `str` | Surrounding text context |
