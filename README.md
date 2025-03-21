# Twoslash Python

[![npm version](https://badge.fury.io/js/twoslash-python.svg)](https://www.npmjs.com/package/twoslash-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Shiki transformer that brings Python Language Server Protocol (LSP) powered type information and documentation to your code blocks. This package extends Shiki's capabilities to work with Python, enabling rich, interactive code documentation with type information, hover states, and more.

## Features

- 🐍 Python code blocks with LSP-powered type information
- 💡 Hover tooltips showing type information and documentation
- 🔍 Error highlighting and diagnostics
- 🎨 Seamless integration with Shiki themes
- 📚 Compatible with modern documentation frameworks

## Installation

```bash
npm install twoslash-python
# or
yarn add twoslash-python
# or
pnpm add twoslash-python
# or
bun add twoslash-python
```

## Usage

The package provides several components that work together to enable Python LSP features in your code blocks:

```typescript
import {
  createTwoslasherPython,
  transformerTwoslashPython,
  rendererRichPython,
  renderMarkdown,
  renderMarkdownInline
} from 'twoslash-python';

// Create a Shiki transformer with Python LSP support
const transformer = transformerTwoslashPython({
  // Enable explicit trigger with `twoslash` comment
  explicitTrigger: true,

  // Configure the renderer
  renderer: rendererRichPython({
    renderMarkdown,
    renderMarkdownInline
  }),

  // Specify supported languages
  langs: ['python'],
  langAlias: {
    python: 'python'
  },

  // Configure the twoslasher
  twoslasher: createTwoslasherPython({})
});
```

### Using in Documentation

In your documentation, add the `twoslash` marker to Python code blocks you want to enhance:

```markdown
```python twoslash
def greet(name: str) -> str:
    """Greet a person by name.

    Args:
        name: The person's name

    Returns:
        A greeting message
    """
    return f"Hello, {name}!"
```
```

The transformer will:
1. Process the code through the Python Language Server
2. Extract type information and documentation
3. Add interactive hover tooltips
4. Highlight any errors or warnings
5. Render the enhanced code block with Shiki

## API Reference

### `createTwoslasherPython(options?: CreateTwoslashPythonOptions)`

Creates a Python-specific twoslasher instance that processes code through the Python Language Server.

#### Options:
- `eslintConfig`: ESLint configuration for code analysis
- `debugShowGeneratedCode`: Show generated code in output (default: false)

### `transformerTwoslashPython(options: TransformerTwoslashPythonOptions)`

Creates a Shiki transformer that processes Python code blocks.

#### Options:
- `explicitTrigger`: Enable explicit triggering with `twoslash` marker (boolean | RegExp)
- `renderer`: Configure how the enhanced code is rendered
- `langs`: Array of supported languages (default: ['python'])
- `langAlias`: Language alias mappings
- `twoslasher`: The twoslasher instance to use

### `rendererRichPython(options?: RendererRichOptionsPython)`

Configures how the enhanced code blocks are rendered.

#### Options:
- `renderMarkdown`: Function to render markdown content
- `renderMarkdownInline`: Function to render inline markdown
- Additional styling and rendering options

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of [Shiki](https://shiki.style/), the beautiful syntax highlighter
- Inspired by [TypeScript's Twoslash](https://www.typescriptlang.org/dev/twoslash/)
- Uses [Python Language Server](https://github.com/python-lsp/python-lsp-server) for type information and documentation
