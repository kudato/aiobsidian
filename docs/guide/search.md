# Search

The `client.search` resource provides three search methods: simple text search, Dataview DQL queries, and JsonLogic queries.

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

## Dataview DQL search

Use [Dataview Query Language](https://blacksmithgu.github.io/obsidian-dataview/) for structured queries:

```python
results = await client.search.dataview('TABLE file.name FROM "Notes"')
for result in results:
    print(result.filename)
    print(result.result)  # Raw Dataview result data
```

!!! note
    Dataview DQL search requires the [Dataview plugin](https://github.com/blacksmithgu/obsidian-dataview) to be installed and enabled in Obsidian.

## JsonLogic search

Use [JsonLogic](https://jsonlogic.com/) for programmatic query construction:

```python
results = await client.search.jsonlogic({"glob": ["*.md"]})
for result in results:
    print(result.filename)
```

Only files the query evaluates truthy for come back, and `result` carries what the expression evaluated to for each of them — any JSON type:

```python
# A predicate: result is True for every file listed
await client.search.jsonlogic({"==": [{"var": "frontmatter.title"}, "Welcome"]})

# A field lookup: result is that field's value
await client.search.jsonlogic({"var": "tags"})        # ["draft", "python"]
await client.search.jsonlogic({"var": "stat.size"})   # 113
```

## Search result structure

Each search method returns a list of `SearchResult` objects:

| Field | Type | Description |
|-------|------|-------------|
| `filename` | `str` | Path to the matching file |
| `score` | `float \| None` | Relevance score (simple search only) |
| `matches` | `list[SearchMatch] \| None` | Match locations with context (simple search only) |
| `result` | `str \| bool \| int \| float \| dict \| list \| None` | What the query evaluated to for this file (Dataview/JsonLogic only) |

Each `SearchMatch` contains:

| Field | Type | Description |
|-------|------|-------------|
| `match` | `MatchSpan` | Match start/end positions |
| `context` | `str` | Surrounding text context |
