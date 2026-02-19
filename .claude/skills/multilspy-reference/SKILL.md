---
name: multilspy-reference
description: Reference for the multilspy Python LSP client library. Use when working on src-python/main.py, modifying LSP queries, or troubleshooting hover/completion extraction.
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Multilspy Reference

## What is Multilspy

Multilspy is a Python library that provides a unified interface to Language Server Protocol (LSP) servers for multiple languages. It handles server lifecycle, file management, and LSP request/response marshalling.

Repo: https://github.com/microsoft/multilspy (and eventually https://github.com/microsoft/multilspy)

## Configuration

```python
from multilspy import LanguageServer, SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

config = MultilspyConfig.from_dict({"code_language": "python"})
logger = MultilspyLogger()

# Async version
lsp = LanguageServer.create(config, logger, "/path/to/project")

# Sync wrapper
sync_lsp = SyncLanguageServer.create(config, logger, "/path/to/project")
```

### Supported Languages

`python`, `java`, `rust`, `csharp`, `typescript`, `javascript`, `go`, `dart`, `ruby`, `kotlin`, `cpp`

### Config Options

```python
MultilspyConfig(
    code_language: str,               # Required: language identifier
    trace_lsp_communication: bool,    # Log all LSP messages (debug)
    start_independent_lsp_process: bool  # Separate process for LSP
)
```

## Server Lifecycle

```python
# Async pattern (preferred)
async with lsp.start_server():
    # Server is running, send requests here
    result = await lsp.request_hover(file_path, line, col)
# Server automatically shut down

# Sync pattern
with sync_lsp.start_server():
    result = sync_lsp.request_hover(file_path, line, col)
```

## LSP Query Methods

All methods take a relative file path (relative to project root), line (0-based), and column (0-based).

### request_hover

```python
result = await lsp.request_hover(file_path: str, line: int, column: int) -> Hover | None
```

Returns `Hover` with:

```python
class Hover(TypedDict):
    contents: MarkupContent  # { kind: str, value: str }
    range: Range | None      # Optional source range
```

The `contents.value` typically contains markdown with code blocks and documentation separated by `---`.

### request_completions

```python
result = await lsp.request_completions(file_path: str, line: int, column: int) -> list[CompletionItem]
```

Returns list of `CompletionItem`:

```python
class CompletionItem(TypedDict):
    completionText: str
    kind: CompletionItemKind  # IntEnum: Method=2, Function=3, Class=7, Variable=13, etc.
    detail: str | None
```

### request_definition

```python
result = await lsp.request_definition(file_path: str, line: int, column: int) -> list[Location]
```

### request_references

```python
result = await lsp.request_references(file_path: str, line: int, column: int) -> list[Location]
```

### request_document_symbols

```python
result = await lsp.request_document_symbols(file_path: str) -> list[UnifiedSymbolInformation]
```

## File Management

Files must be opened before querying:

```python
async with lsp.start_server():
    with lsp.open_file(relative_path):
        # File is open in the LSP, queries work
        hover = await lsp.request_hover(relative_path, line, col)
    # File automatically closed
```

**Note**: In the current twoslash-python implementation (`src-python/main.py`), file opening is handled internally by the batch processing pipeline.

## Type Definitions

```python
# Positions are 0-based
class Position(TypedDict):
    line: int
    character: int

class Range(TypedDict):
    start: Position
    end: Position

class Location(TypedDict):
    uri: str
    range: Range
    absolutePath: str
    relativePath: str

class CompletionItemKind(IntEnum):
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Keyword = 14
    Snippet = 15
    Constant = 21

class SymbolKind(IntEnum):
    File = 1
    Module = 2
    Namespace = 3
    Class = 5
    Method = 6
    Property = 7
    Function = 12
    Variable = 13
    Constant = 14
```

## How twoslash-python Uses Multilspy

In `src-python/main.py`, the `PyTwoslash` class:

1. Creates a `LanguageServer` with `code_language: "python"` config
2. Extracts symbols from the target file using AST (`symbol.py`)
3. Starts the LSP server
4. Sends hover requests in batches (default: 20 per batch) with timeout
5. Parses hover responses: splits on `---` to separate type info from docs
6. Extracts `@param`, `@returns` etc. tags from docs
7. Creates `NodeHover` objects with position, text, docs, tags
8. Saves as JSON compatible with the TypeScript transformer

## Common Issues

- **Hover returns None**: The LSP needs the project's dependencies installed. Make sure the project's virtualenv is active or packages are importable
- **Timeout errors**: Default 10s per hover. Increase with `--hover-timeout` for large projects
- **Wrong positions**: multilspy uses 0-based line/column. The AST parser uses 1-based lines, so subtract 1 when converting

## Key Source Files

- Main implementation: `src-python/main.py`
- Symbol extraction: `src-python/symbol.py`
- Multilspy source: `context/multilspy/src/multilspy/language_server.py`
- Multilspy types: `context/multilspy/src/multilspy/multilspy_types.py`
- Multilspy config: `context/multilspy/src/multilspy/multilspy_config.py`
- Test examples: `context/multilspy/tests/multilspy/test_multilspy_typescript.py`
