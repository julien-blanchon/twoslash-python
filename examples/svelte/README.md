# Twoslash Python - Svelte Example

Minimal SvelteKit app showing Python code blocks with LSP-powered hover tooltips using `twoslash-python` and Shiki.

Scaffolded with [`sv create`](https://github.com/sveltejs/cli) (minimal template, TypeScript).

## Setup

```bash
# From the repo root, build the package first
bun install
bun run build

# Then set up the example
cd examples/svelte
bun install
bun run dev
```

Open http://localhost:5173 and hover over symbols in the code block.

## How it works

1. `static/example.py` -- The Python source code to display
2. `static/example.nodes.json` -- Pre-generated hover data (from `pytwoslash` CLI)
3. `src/routes/+page.svelte` -- Loads Shiki + twoslash-python, renders the code block

### Generating nodes.json for your own files

```bash
cd ../../src-python
pip install -e .
pytwoslash ../examples/svelte/static/example.py /path/to/your/project -o ../examples/svelte/static/example.nodes.json
```

### Using in a real SvelteKit app

In production, you'd typically:

1. Run `pytwoslash` at build time to generate JSON for each code block
2. Use `createTwoslasherPython()` with `json_file_path` in code block metadata
3. Process markdown files with a remark/rehype plugin that passes the transformer to Shiki

```ts
import { codeToHtml } from 'shiki';
import {
  createTwoslasherPython,
  transformerTwoslashPython,
  rendererRichPython,
  renderMarkdown,
  renderMarkdownInline,
} from 'twoslash-python';

const html = await codeToHtml(code, {
  lang: 'python',
  theme: 'github-dark',
  transformers: [
    transformerTwoslashPython({
      twoslasher: createTwoslasherPython({}),
      renderer: rendererRichPython({ renderMarkdown, renderMarkdownInline }),
      explicitTrigger: true,
    }),
  ],
  meta: {
    json_file_path: './path/to/nodes.json',
    __raw: 'twoslash',
  },
});
```

## Building

```bash
bun run build
bun run preview
```
