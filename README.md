# Twoslash Python

[![npm version](https://badge.fury.io/js/twoslash-python.svg)](https://www.npmjs.com/package/twoslash-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful tool that brings TypeScript-like type information and documentation capabilities to Python code blocks. This package extends the Twoslash syntax to work with Python, enabling rich, interactive code documentation with type information, hover states, and more.

## Features

- 🐍 Python syntax highlighting with type information
- 💡 Hover tooltips showing type information and documentation
- 🔍 Automatic type inference and display
- 🎨 Customizable themes and styling
- 📚 Compatible with popular documentation frameworks

## Installation

```bash
npm install twoslash-python
# or
yarn add twoslash-python
# or
pnpm add twoslash-python
```

## Usage

```typescript
import { createPythonTwoslasher } from 'twoslash-python';

const code = `
# @python
def greet(name: str) -> str:
    return f"Hello, {name}!"
`;

const result = createPythonTwoslasher(code);
```

## Configuration

The package can be configured with various options:

```typescript
const options = {
  theme: 'github-dark',
  showTypes: true,
  hoverPreview: true,
  // ... other options
};

const result = createPythonTwoslasher(code, options);
```

## API Reference

### `createPythonTwoslasher(code: string, options?: TwoslashOptions)`

Creates a new Twoslash instance for Python code.

#### Parameters:
- `code`: The Python source code to process
- `options`: Optional configuration object

#### Returns:
- Processed code with type information and hover states

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Format code
npm run format

# Lint code
npm run lint
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of the excellent [Shiki](https://github.com/shikijs/shiki) syntax highlighter
- Inspired by TypeScript's [Twoslash](https://www.typescriptlang.org/dev/twoslash/) syntax
