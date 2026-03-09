# Periodic Notes

The `client.periodic` resource manages periodic notes — daily, weekly, monthly, quarterly, and yearly.

!!! note
    Periodic notes require the corresponding Obsidian plugin to be configured (e.g. Daily Notes core plugin or the Periodic Notes community plugin).

## Available periods

```python
from aiobsidian import Period

Period.DAILY      # Daily note
Period.WEEKLY     # Weekly note
Period.MONTHLY    # Monthly note
Period.QUARTERLY  # Quarterly note
Period.YEARLY     # Yearly note
```

## Accessing notes by date

By default, all methods operate on the **current** periodic note. Pass `date` to access a note for a specific date:

```python
import datetime
from aiobsidian import ContentType, Period

# Get the daily note for March 15, 2024
content = await client.periodic.get(
    Period.DAILY, date=datetime.date(2024, 3, 15)
)

# Update a specific monthly note
await client.periodic.update(
    Period.MONTHLY,
    "# June 2024 Summary",
    date=datetime.date(2024, 6, 1),
)

# Append to a past daily note
await client.periodic.append(
    Period.DAILY,
    "\n\nLate addition.",
    date=datetime.date(2024, 3, 15),
)

# Delete a yearly note
await client.periodic.delete(
    Period.YEARLY, date=datetime.date(2023, 1, 1)
)
```

## Reading a periodic note

```python
from aiobsidian import Period

# Get today's daily note as Markdown
content = await client.periodic.get(Period.DAILY)
print(content)

# Get this week's note as structured JSON
from aiobsidian import ContentType

note = await client.periodic.get(
    Period.WEEKLY,
    content_type=ContentType.NOTE_JSON,
)
print(note.frontmatter)
```

## Creating or updating a periodic note

Replace the entire content of a periodic note. If the note doesn't exist yet, it will be created:

```python
await client.periodic.update(
    Period.DAILY,
    "# Daily Note\n\n- [ ] Task 1\n- [ ] Task 2",
)
```

## Appending to a periodic note

```python
await client.periodic.append(
    Period.DAILY,
    "\n\n## Evening Review\n\nToday was productive.",
)
```

## Patching a periodic note

Target specific sections within a periodic note:

```python
from aiobsidian import PatchOperation, Period, TargetType

await client.periodic.patch(
    Period.DAILY,
    "- [x] Completed task",
    operation=PatchOperation.APPEND,
    target_type=TargetType.HEADING,
    target="Tasks",
)
```

## Deleting a periodic note

```python
await client.periodic.delete(Period.DAILY)
```
