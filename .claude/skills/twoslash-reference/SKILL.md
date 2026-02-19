---
name: twoslash-reference
description: Reference for the Twoslash markup system, node types, renderer hooks, and Shiki transformer integration. Use when working on transformer.ts, renderer.ts, or the node processing pipeline.
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Twoslash Reference

## What is Twoslash

Twoslash is a markup format for code samples that uses a language server to extract type information, completions, and errors. It was originally built for TypeScript and this project ports it to Python.

## Notation Syntax

| Notation | Example | Purpose |
|----------|---------|---------|
| `^?` | Line below identifier | Extract type/hover info at position |
| `^|` | Line below identifier | Get auto-completions at position |
| `^^^` | Line below code | Highlight the range above |
| `// @flag: value` | Top of code block | Set compiler/handbook options |
| `// ---cut---` | Anywhere | Remove lines above from output |
| `// @filename: path` | Before code | Split into virtual files |
| `// @errors: 1234` | Top of block | Expect specific error codes |
| `// @noErrors` | Top of block | Suppress all errors |

## Node Types (TwoslashNode union)

All nodes share a base: `{ type, start, length, line, character }`

```typescript
// Hover information (from LSP)
NodeHover: { type: 'hover', target: string, text: string, docs?: string, tags?: [string, string?][] }

// Explicit query (^?)
NodeQuery: { type: 'query', target: string, text: string, docs?: string, tags?: [string, string?][] }

// Completions (^|)
NodeCompletion: { type: 'completion', completions: CompletionItem[], completionsPrefix: string }

// Errors (from diagnostics)
NodeError: { type: 'error', text: string, code?: number, level?: 'warning'|'error'|'suggestion'|'message', filename?: string, id?: string }

// Highlight ranges (^^^)
NodeHighlight: { type: 'highlight', text?: string }

// Custom tags (@tag)
NodeTag: { type: 'tag', name: string, text?: string }
```

## TwoslashReturn Structure

```typescript
{
  code: string           // Cleaned output code (notations removed)
  nodes: TwoslashNode[]  // All extracted information
  meta?: {
    extension?: string   // File extension
    removals?: Range[]   // Removed ranges for offset calculation
  }
}
```

## Renderer Hooks (TwoslashRenderer interface)

The renderer is called by the transformer for each node type:

```typescript
interface TwoslashRenderer {
  // Required: renders hover popup for a token
  nodeStaticInfo(info: NodeHover, node: Element | Text): Partial<ElementContent>

  // Optional hooks
  nodeQuery?(query: NodeQuery, node: Element | Text): Partial<ElementContent>
  nodeCompletion?(query: NodeCompletion, node: Element | Text): Partial<ElementContent>
  nodesError?(error: NodeError, nodes: ElementContent[]): ElementContent[]
  nodesHighlight?(highlight: NodeHighlight, nodes: ElementContent[]): ElementContent[]
  lineError?(error: NodeError): ElementContent[]
  lineQuery?(query: NodeQuery, targetNode?: Element | Text): ElementContent[]
  lineCustomTag?(tag: NodeTag): ElementContent[]
}
```

## Transformer Pipeline

The Shiki transformer hooks execute in this order:

1. **`preprocess(code)`** -- Check language filter, load JSON, call twoslasher
2. **`tokens(tokens)`** -- Split tokens at node boundaries using `splitTokens`
3. **`pre(pre)`** -- Add CSS classes to `<pre>` element
4. **`code(codeEl)`** -- Main processing: iterate nodes, wrap tokens with renderer output

In the `code` hook, processing order matters:
- Errors and queries are processed first
- Hovers are deferred (collected in `actionsHovers`)
- Highlights are deferred (collected in `actionsHighlights`)
- Deferred actions run after all nodes are visited

## CSS Classes

| Class | Element |
|-------|---------|
| `.twoslash` | `<pre>` wrapper |
| `.twoslash-hover` | Hoverable token |
| `.twoslash-popup-container` | Popup box |
| `.twoslash-popup-code` | Type info in popup |
| `.twoslash-popup-docs` | Documentation in popup |
| `.twoslash-popup-docs-tags` | JSDoc tags container |
| `.twoslash-error` | Error-highlighted token |
| `.twoslash-highlighted` | Manually highlighted range |
| `.twoslash-completion-cursor` | Completion cursor |
| `.twoslash-completion-list` | Completion dropdown |

## Key Source Files

- Transformer: `src/transformer.ts`
- Renderer: `src/renderer.ts`
- Twoslasher: `src/twoslasher.ts`
- Original twoslash core: `context/twoslash/packages/twoslash/src/core.ts`
- Node type definitions: `context/twoslash/packages/twoslash-protocol/src/types/nodes.ts`
- Shiki twoslash renderer: `context/twoslash/packages/twoslash/src/renderer-rich.ts`
