# Twoslash Python

[![npm version](https://badge.fury.io/js/twoslash-python.svg)](https://www.npmjs.com/package/twoslash-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [Shiki](https://shiki.style/) transformer that brings **Python LSP-powered type information** to your code blocks -- the same rich hover experience [Twoslash](https://twoslash.netlify.app/) provides for TypeScript, but for Python.

Hover over any symbol in a Python code block and get type signatures, docstrings, and parameter info, all extracted via the Python Language Server.

## How It Works

The project has two parts:

1. **`pytwoslash`** (Python CLI) -- Uses [multilspy](https://github.com/microsoft/multilspy) to spin up a Python language server, walks your code's AST to find symbols, and fetches hover information for each one. Outputs a JSON file of annotated nodes.

2. **`twoslash-python`** (Node.js / Shiki transformer) -- Reads that JSON and injects hover popups, error highlights, and type annotations into Shiki-rendered code blocks.

```
Python source file
        |
        v
  [ pytwoslash CLI ]  -->  nodes.json  (hover info, errors, etc.)
        |                       |
        v                       v
  Python LSP            [ Shiki transformer ]
  (multilspy)                   |
                                v
                        Rich HTML code block
                        with hover tooltips
```

## Features

- Python code blocks with LSP-powered type information
- Hover tooltips showing type signatures and documentation
- Error highlighting and diagnostics
- Seamless integration with Shiki themes
- Compatible with documentation frameworks (VitePress, Astro, etc.)

## Installation

### Node.js package

```bash
bun add twoslash-python
```

### Python CLI

Requires **Python 3.12+**.

```bash
cd src-python
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
cd src-python
uv pip install -e .
```

## Usage

### Step 1: Generate hover data with `pytwoslash`

Run the Python CLI on a source file to extract LSP hover information:

```bash
cd src-python
python main.py <file.py> <project_path> -o output.json
```

**Arguments:**

| Argument                | Description                                                 |
| ----------------------- | ----------------------------------------------------------- |
| `file_path`             | Path to the Python file to process                          |
| `project_path`          | Path to the Python project root (used for LSP resolution)   |
| `-o, --output`          | Output JSON file path (default: `<file>.nodes.json`)        |
| `-v, --verbose`         | Enable verbose logging                                      |
| `--symbol-kinds`        | Filter symbol types (e.g., `class`, `function`, `variable`) |
| `--include-all-symbols` | Include all symbol types                                    |
| `--hover-timeout`       | Max seconds per hover request (default: 10)                 |
| `--batch-size`          | Symbols per LSP batch (default: 20)                         |

**Example:**

```bash
python main.py ../examples/demo.py ../examples -o demo.nodes.json
```

### Step 2: Use the Shiki transformer

```typescript
import {
  createTwoslasherPython,
  transformerTwoslashPython,
  rendererRichPython,
  renderMarkdown,
  renderMarkdownInline,
} from "twoslash-python";

const transformer = transformerTwoslashPython({
  explicitTrigger: true,
  renderer: rendererRichPython({
    renderMarkdown,
    renderMarkdownInline,
  }),
  langs: ["python"],
  twoslasher: createTwoslasherPython({}),
});
```

Then pass `transformer` to Shiki's `codeToHtml` or use it in your documentation framework. The code block's metadata should include a `json_file_path` pointing to the generated JSON:

````markdown
```python twoslash json_file_path=./demo.nodes.json
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"
```
````

## API Reference

### `createTwoslasherPython(options?)`

Creates a Python twoslasher that reads pre-generated JSON node data.

### `transformerTwoslashPython(options)`

Returns a Shiki transformer for Python code blocks.

| Option            | Type                          | Default                              | Description                                |
| ----------------- | ----------------------------- | ------------------------------------ | ------------------------------------------ |
| `twoslasher`      | `TwoslashShikiFunctionPython` | _required_                           | The twoslasher instance                    |
| `explicitTrigger` | `boolean \| RegExp`           | `false`                              | Only process blocks with `twoslash` marker |
| `renderer`        | `TwoslashRenderer`            | `rendererRichPython()`               | Renderer for output                        |
| `langs`           | `string[]`                    | `['python']`                         | Languages to process                       |
| `langAlias`       | `Record<string, string>`      | `{ python: 'python', py: 'python' }` | Language aliases                           |
| `throws`          | `boolean`                     | `true`                               | Throw on errors                            |

### `rendererRichPython(options?)`

Configures how enhanced code blocks are rendered.

| Option                 | Type                | Default             | Description                 |
| ---------------------- | ------------------- | ------------------- | --------------------------- |
| `renderMarkdown`       | `function`          | pass-through        | Markdown renderer for docs  |
| `renderMarkdownInline` | `function`          | pass-through        | Inline markdown renderer    |
| `processHoverInfo`     | `function`          | cleanup processor   | Custom type info formatter  |
| `errorRendering`       | `'line' \| 'hover'` | `'line'`            | How errors are displayed    |
| `classExtra`           | `string`            | `'twoslash-python'` | Extra CSS class on elements |

## CSS

The transformer adds CSS classes you can style. The main classes follow the `@shikijs/twoslash` convention:

- `.twoslash` -- wrapper on the `<pre>` element
- `.twoslash-hover` -- hoverable token
- `.twoslash-popup-container` -- the popup box
- `.twoslash-popup-code` -- type info inside popup
- `.twoslash-popup-docs` -- documentation inside popup
- `.twoslash-error` -- error-highlighted token
- `.twoslash-highlighted` -- manually highlighted range

See the [`@shikijs/twoslash` style reference](https://shiki.style/packages/twoslash#css) for a complete CSS example.

## Development

```bash
# Install dependencies
bun install

# Build TypeScript
bun run build

# Lint
bun run lint

# Format
bun run format
```

## Acknowledgments

- Built on [Shiki](https://shiki.style/)
- Inspired by [Twoslash](https://twoslash.netlify.app/) for TypeScript
- Uses [multilspy](https://github.com/microsoft/multilspy) for Python LSP integration

## License

[MIT](./LICENSE) -- Julien Blanchon
