#!/usr/bin/env python3
"""
PyTwoslash: Python implementation of Twoslash for LSP-powered hover information.

This module provides a class that uses multilspy to generate hover information for Python code,
outputting it in a format compatible with Shiki Twoslash for enhanced code blocks on websites.
"""

import asyncio
import json
import logging
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from multilspy import LanguageServer, SyncLanguageServer, multilspy_types
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from multilspy.multilspy_utils import TextUtils
from symbol import Symbol, SymbolType, extract_symbols

# Default symbol kinds to include (Class, Method, Function, Object, Property)
DEFAULT_SYMBOL_KINDS = {
    SymbolType.VARIABLE,
    SymbolType.FUNCTION,
    SymbolType.CLASS,
    SymbolType.BASE_CLASS,
    SymbolType.DECORATOR,
}

# ----- Dataclass Models for Twoslash Nodes -----


class ErrorLevel(StrEnum):
    """Error level enumeration."""

    WARNING = "warning"
    ERROR = "error"
    SUGGESTION = "suggestion"
    MESSAGE = "message"


@dataclass
class Position:
    """Position in a file (line and character)."""

    # 0-indexed line number
    line: int

    # 0-indexed character number
    character: int


@dataclass
class NodeStartLength:
    """Basic node with start and length to represent a range in the code."""

    # 0-indexed position of the node in the file
    start: int

    # The length of the node
    length: int


@dataclass
class NodeBase(NodeStartLength, Position):
    """Base class for all Twoslash nodes."""


@dataclass
class NodeHover(NodeBase):
    """Hover information node."""

    # The node type
    type: str = "hover"

    # The string content of the node this represents (mainly for debugging)
    target: str = ""

    # The base LSP response (the type)
    text: str = ""

    # Attached JSDoc info
    docs: str | None = None

    # JSDoc tags as tuples of (name, text)
    tags: list[tuple[str, str | None]] = field(default_factory=list)


@dataclass
class NodeHighlight(NodeBase):
    """Highlight node."""

    # The node type
    type: str = "highlight"

    # The annotation message
    text: str | None = None


@dataclass
class NodeQuery(NodeHover):
    """Query node (similar to hover but with type='query')."""

    # Override the type
    type: str = "query"


@dataclass
class NodeError(NodeBase):
    """Error node for code errors."""

    # The node type
    type: str = "error"

    # Error message
    text: str = ""

    # Unique ID for the error
    id: str | None = None

    # Error level
    level: ErrorLevel = ErrorLevel.ERROR

    # Error code
    code: int | str | None = None

    # The filename of the file the error is in
    filename: str | None = None


@dataclass
class NodeTag(NodeBase):
    """Tag node for annotations."""

    # The node type
    type: str = "tag"

    # What was the name of the tag
    name: str = ""

    # What was the text after the `// @tag: ` string
    text: str | None = None


# Type alias for all possible node types
type TwoslashNode = NodeHover | NodeHighlight | NodeQuery | NodeError | NodeTag


# ----- Main PyTwoslash Implementation -----


class PyTwoslash:
    def __init__(
        self,
        project_path: str | Path,
        verbose: bool = False,
        log_level: int = logging.INFO,
        symbol_kinds: Sequence[SymbolType] | None = None,
        hover_timeout: float = 10.0,
        batch_size: int = 20,
    ):
        """
        Initialize the PyTwoslash instance.

        Args:
            project_path: Path to the Python project/venv directory
            verbose: Whether to print verbose output
            log_level: Logging level for the logger
            symbol_kinds: Set of symbol kinds to include, defaults to classes, methods, and functions
            hover_timeout: Maximum time in seconds to wait for a hover request (default: 10s)
            batch_size: Number of hover requests to process in a single batch (default: 20)

        """
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.symbol_kinds = symbol_kinds or DEFAULT_SYMBOL_KINDS
        self.hover_timeout = hover_timeout
        self.batch_size = batch_size

        # Set up logging
        self.logger = logging.getLogger("py_twoslash")
        self.logger.setLevel(log_level if verbose else logging.WARNING)

        # Create console handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Initialize multilspy
        self.lsp_logger = MultilspyLogger()
        self.config = MultilspyConfig.from_dict({"code_language": "python"})

        # Create both sync and async versions of the language server
        self.lsp = SyncLanguageServer.create(
            self.config, self.lsp_logger, str(self.project_path)
        )

        self.async_lsp = LanguageServer.create(
            self.config, self.lsp_logger, str(self.project_path)
        )

        self.logger.info(f"Initialized with project path: {self.project_path}")

    @staticmethod
    def _postprocess_hover_info(
        hover_info: multilspy_types.Hover | None,
    ) -> tuple[str, str | None, list[tuple[str, str | None]]]:
        text = ""
        docs = None
        tags = []

        if hover_info is None:
            return text, docs, tags

        contents = hover_info["contents"]
        text = contents["value"]

        # Extract docs from markdown-formatted text
        # Multilspy often provides docs embedded in the text field with a separator "---"
        if text:
            # Look for documentation after markdown separator
            doc_parts = re.split(r"\n\s*---\s*\n", text, maxsplit=1)
            if len(doc_parts) > 1:
                # Keep the code part in text and move docs to docs field
                text = doc_parts[0]
                docs_text = doc_parts[1]

                # Clean up docs text
                # If it starts with ```text, extract the content between the backticks
                text_block_match = re.match(
                    r"```text\s*(.*?)\s*```", docs_text, re.DOTALL
                )
                if text_block_match:
                    docs = text_block_match.group(1).strip()
                else:
                    # Otherwise use everything after the separator
                    docs = docs_text.strip()

        # Parse docs for tags if it exists
        if docs:
            docs = docs.replace("```python\n", "").replace("\n```", "")
            # Find common doc tag patterns like @param, @returns, etc.
            tag_pattern = re.compile(r"@(\w+)\s+(.+?)(?=\n@|\Z)", re.DOTALL)
            for match in tag_pattern.finditer(docs):
                tag_name = match.group(1)
                tag_text = match.group(2).strip()
                tags.append((tag_name, tag_text))

        return text, docs, tags

    async def _process_hover_with_timeout(
        self, file_name: str, line: int, character: int
    ) -> multilspy_types.Hover | None:
        try:
            return await asyncio.wait_for(
                self.async_lsp.request_hover(file_name, line, character),
                timeout=self.hover_timeout,
            )
        except TimeoutError:
            self.logger.warning(
                f"Hover request timed out after {self.hover_timeout}s for position {line}:{character}"
            )
            return None
        except Exception:
            self.logger.exception(
                f"Error in hover request at ({file_name}, {line}, {character})"
            )
            return None

    def save_to_file(self, nodes: list[NodeHover], output_path: str) -> None:
        # Convert dataclasses to dictionaries
        node_dicts = [asdict(node) for node in nodes]

        # Convert any Enum values to their string representation
        def _process_enum_values(obj):
            if isinstance(obj, dict):
                return {k: _process_enum_values(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_process_enum_values(item) for item in obj]
            if isinstance(obj, Enum):
                return obj.value
            return obj

        node_dicts = _process_enum_values(node_dicts)

        # Write to file
        Path(output_path).write_text(json.dumps(node_dicts, indent=2), encoding="utf-8")

        self.logger.info(f"Saved {len(nodes)} nodes to {output_path}")

    async def _process_file_with_ast(self, file_path: str | Path) -> list[NodeHover]:
        self.logger.info("Processing code with AST")

        # Read file content
        content = Path(file_path).read_text(encoding="utf-8")

        twoslash_nodes: list[NodeHover] = []

        # Extract symbols using AST
        symbols: list[Symbol] = extract_symbols(content)

        print(f"Symbols before filtering: {len(symbols)}")
        # Save symbols in symbols.json
        Path("symbols.json").write_text(
            json.dumps([asdict(symbol) for symbol in symbols], indent=2),
            encoding="utf-8",
        )
        # Filter out the symbols
        symbols = [symbol for symbol in symbols if symbol.type in self.symbol_kinds]
        print(f"Symbols after filtering: {len(symbols)}")

        # Start the LSP server for hover information
        async with self.async_lsp.start_server():
            # Process hover requests in batches
            self.logger.info(
                f"Processing {len(symbols)} hover requests in batches of {self.batch_size}"
            )

            # Process in chunks to avoid overwhelming the LSP server
            for i in range(0, len(symbols), self.batch_size):
                batch = symbols[i : i + self.batch_size]

                # Create hover tasks for this batch
                hover_tasks = []
                for symbol in batch:
                    print(
                        f"Processing symbol: {symbol.text} with params: {file_path}, {symbol.end.line}, {symbol.end.character}"
                    )
                    line = symbol.end.line - 1
                    if symbol.end.line == symbol.start.line:
                        character = (
                            symbol.start.character
                            + (symbol.end.character - symbol.start.character) // 2
                        )
                    else:
                        character = symbol.end.character - 1
                    hover_task = self._process_hover_with_timeout(
                        file_path, line, character
                    )
                    hover_tasks.append(hover_task)

                self.logger.info(
                    f"Processing batch {i // self.batch_size + 1}/{(len(symbols) + self.batch_size - 1) // self.batch_size} ({len(batch)} symbols)"
                )

                # Process all hover requests in this batch in parallel
                hover_results: list[NodeHover] = await asyncio.gather(*hover_tasks)

                # Process results for this batch
                # for (name, line, character, length, absolute_pos), hover_info in zip(
                #     batch, hover_results, strict=False
                # ):
                for symbol, hover_info in zip(batch, hover_results, strict=False):
                    text, docs, tags = self._postprocess_hover_info(hover_info)

                    if not text:
                        self.logger.debug(
                            f"No text info available for symbol: {symbol.text}"
                        )
                        continue
                    length = symbol.end.character - symbol.start.character
                    line = symbol.start.line - 1
                    character = symbol.start.character
                    target = symbol.text
                    absolute_pos = TextUtils.get_index_from_line_col(
                        content, line, symbol.start.character
                    )

                    node = NodeHover(
                        start=absolute_pos,
                        length=length,
                        line=line,
                        character=character,
                        target=target,
                        text=text,
                        docs=docs,
                        tags=tags,
                    )

                    twoslash_nodes.append(node)
                    self.logger.info(f"Added hover info for symbol: {symbol.text}")

                await asyncio.sleep(0.1)

        return twoslash_nodes

    def process_file_with_ast(self, file_path: str | Path) -> list[NodeHover]:
        return asyncio.run(self._process_file_with_ast(file_path))


"""Command-line interface for PyTwoslash."""
app = App(help="Generate Shiki Twoslash hover information for Python files")


@app.default
def process(
    file_path: Annotated[str, Parameter(help="Path to the Python file to process")],
    project_path: Annotated[
        str, Parameter(help="Path to the Python project/venv directory")
    ],
    output: Annotated[
        str | None, Parameter(["-o", "--output"], help="Path to the output JSON file")
    ] = None,
    verbose: Annotated[
        bool,
        Parameter(
            ["-v", "--verbose"],
            help="Enable verbose output",
        ),
    ] = False,
    symbol_kinds: Annotated[
        set[SymbolType],
        Parameter(
            "--symbol-kinds",
            help="Comma-separated list of symbol kinds to include (e.g., 'class, method, function')",
        ),
    ] = DEFAULT_SYMBOL_KINDS,
    include_all_symbols: Annotated[
        bool,
        Parameter(
            "--include-all-symbols",
            help="Include all symbol kinds instead of filtering",
        ),
    ] = False,
    hover_timeout: Annotated[
        float,
        Parameter(
            "--hover-timeout",
            help="Maximum time in seconds to wait for hover information",
        ),
    ] = 10.0,
    batch_size: Annotated[
        int,
        Parameter(
            "--batch-size",
            help="Number of hover requests to process in a single batch",
        ),
    ] = 20,
):
    """Process a Python file to generate Twoslash hover information."""
    log_level = logging.INFO if verbose else logging.WARNING

    # Parse symbol kinds
    symbol_kinds_set = None
    if include_all_symbols:
        symbol_kinds_set = set(SymbolType)
    else:
        symbol_kinds_set = set()
        symbol_kinds_set.update(symbol_kinds)

    twoslash = PyTwoslash(
        project_path,
        verbose,
        log_level,
        symbol_kinds_set,
        hover_timeout,
        batch_size,
    )

    print(f"Processing file {file_path}")
    if verbose:
        print(f"Including symbol kinds: {[k.name for k in twoslash.symbol_kinds]}")
        print(f"Hover timeout: {hover_timeout}s")
        print(f"Processing in batches of {batch_size}")

    nodes = twoslash.process_file_with_ast(file_path)
    if not output:
        output = f"{file_path}.nodes.json"
    twoslash.save_to_file(nodes, output)

    print(f"Successfully generated hover information for {file_path}")
    print(f"Output saved to {output}")
    print(f"Generated {len(nodes)} nodes")


if __name__ == "__main__":
    app()
