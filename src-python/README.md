# pytwoslash

Python CLI that extracts LSP hover information from Python source files, outputting JSON nodes compatible with the `twoslash-python` Shiki transformer.

## Requirements

- Python 3.12+
- A Python project with resolvable imports (the LSP needs to find your dependencies)

## Installation

```bash
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install -e .
```

## Usage

```bash
python main.py <file_path> <project_path> [options]
```

### Arguments

| Argument       | Description                               |
| -------------- | ----------------------------------------- |
| `file_path`    | Path to the Python file to process        |
| `project_path` | Path to the Python project root directory |

### Options

| Option                  | Default                                        | Description                   |
| ----------------------- | ---------------------------------------------- | ----------------------------- |
| `-o, --output`          | `<file>.nodes.json`                            | Output JSON file path         |
| `-v, --verbose`         | `false`                                        | Enable verbose logging        |
| `--symbol-kinds`        | `class,function,variable,base_class,decorator` | Symbol types to include       |
| `--include-all-symbols` | `false`                                        | Include all symbol types      |
| `--hover-timeout`       | `10.0`                                         | Max seconds per hover request |
| `--batch-size`          | `20`                                           | Symbols processed per batch   |

### Example

```bash
# Process a file and generate hover nodes
python main.py ./example.py /path/to/project -o example.nodes.json -v

# Include all symbols (keywords, comments, operators, etc.)
python main.py ./example.py /path/to/project --include-all-symbols

# Only extract class and function info
python main.py ./example.py /path/to/project --symbol-kinds class function
```

## How It Works

1. **Symbol extraction** (`symbol.py`) -- Parses the Python file using both the tokenizer and AST to find all symbols (functions, classes, variables, decorators, etc.)
2. **LSP hover** (`main.py`) -- Starts a Python language server via [multilspy](https://github.com/microsoft/multilspy), sends hover requests for each symbol position, and collects type signatures and documentation.
3. **JSON output** -- Writes the collected hover nodes as a JSON array compatible with the Shiki `twoslash-python` transformer.

## Symbol Types

| Type         | Description                                             |
| ------------ | ------------------------------------------------------- |
| `function`   | Function and async function definitions, lambdas, calls |
| `class`      | Class definitions                                       |
| `variable`   | Assignments, function parameters, annotated variables   |
| `base_class` | Base classes in class inheritance                       |
| `decorator`  | Decorator names                                         |
| `module`     | Import statements                                       |
| `attribute`  | Object attributes                                       |
| `operator`   | Binary and unary operators                              |
| `keyword`    | Python keywords                                         |
| `constant`   | Numbers and strings                                     |
| `comment`    | Comments                                                |

## Output Format

The output JSON is an array of node objects. Each hover node has:

```json
{
  "type": "hover",
  "start": 42,
  "length": 5,
  "line": 3,
  "character": 4,
  "target": "greet",
  "text": "(function) def greet(name: str) -> str",
  "docs": "Greet a person by name.",
  "tags": []
}
```
