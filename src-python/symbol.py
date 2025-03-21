import ast
import keyword
import tokenize
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

OPP_MAPPING = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.FloorDiv: "//",
}


class SymbolType(StrEnum):
    COMMENT = "comment"
    KEYWORD = "keyword"
    CONSTANT = "constant"
    VARIABLE = "variable"
    FUNCTION = "function"
    CLASS = "class"
    BASE_CLASS = "base_class"
    DECORATOR = "decorator"
    OPERATOR = "operator"
    ATTRIBUTE = "attribute"
    MODULE = "module"


@dataclass
class Position:
    line: int
    character: int


@dataclass
class Symbol:
    type: SymbolType
    text: str
    start: Position
    end: Position


def _extract_from_tokens(code_str: str) -> list[Symbol]:
    symbols: list[Symbol] = []
    try:
        tokens = list(tokenize.generate_tokens(StringIO(code_str).readline))
        for token in tokens:
            start_line, start_col = token.start
            end_line, end_col = token.end
            text = token.string
            if token.type == tokenize.COMMENT:
                symbol = Symbol(
                    type=SymbolType.COMMENT,
                    text=text,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=end_line, character=end_col),
                )
                symbols.append(symbol)
            elif token.type == tokenize.NAME and keyword.iskeyword(text):
                symbol = Symbol(
                    type=SymbolType.KEYWORD,
                    text=text,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=end_line, character=end_col),
                )
                symbols.append(symbol)
            elif token.type in {tokenize.NUMBER, tokenize.STRING}:
                symbol = Symbol(
                    type=SymbolType.CONSTANT,
                    text=text,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=end_line, character=end_col),
                )
                symbols.append(symbol)
    except tokenize.TokenError:
        pass
    return symbols


def _extract_from_ast(tree: ast.AST, code_str: str) -> list[Symbol]:
    symbols: list[Symbol] = []
    lines = code_str.splitlines()

    for node in ast.walk(tree):
        match node:
            # Decorators (for functions and classes)
            case (
                ast.FunctionDef(decorator_list=decorators)
                | ast.AsyncFunctionDef(decorator_list=decorators)
                | ast.ClassDef(decorator_list=decorators)
            ) if decorators:
                for decorator in decorators:
                    match decorator:
                        case ast.Name(id=name):
                            start_line = decorator.lineno
                            start_col = decorator.col_offset + 1  # After '@'
                            end_col = start_col + len(name)
                            symbol = Symbol(
                                type=SymbolType.DECORATOR,
                                text=name,
                                start=Position(line=start_line, character=start_col),
                                end=Position(line=start_line, character=end_col),
                            )
                            symbols.append(symbol)
                        case ast.Attribute(attr=attr):
                            start_line = decorator.lineno
                            start_col = (
                                decorator.col_offset
                                + lines[start_line - 1][decorator.col_offset :].find(
                                    "." + attr
                                )
                                + 1
                            )
                            end_col = start_col + len(attr)
                            symbol = Symbol(
                                type=SymbolType.DECORATOR,
                                text=attr,
                                start=Position(line=start_line, character=start_col),
                                end=Position(line=start_line, character=end_col),
                            )
                            symbols.append(symbol)
                        case ast.Call(func=func):
                            match func:
                                case ast.Name(id=name):
                                    start_line = decorator.lineno
                                    start_col = decorator.col_offset + 1
                                    end_col = start_col + len(name)
                                    symbol = Symbol(
                                        type=SymbolType.DECORATOR,
                                        text=name,
                                        start=Position(
                                            line=start_line, character=start_col
                                        ),
                                        end=Position(
                                            line=start_line, character=end_col
                                        ),
                                    )
                                    symbols.append(symbol)

            # Function definitions (regular and async)
            case ast.FunctionDef(name=name) | ast.AsyncFunctionDef(name=name):
                start_line = node.lineno
                prefix = (
                    "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                )
                start_col = node.col_offset + len(prefix)
                end_col = start_col + len(name)
                symbol = Symbol(
                    type=SymbolType.FUNCTION,
                    text=name,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)
                for arg in node.args.args:
                    arg_name = arg.arg
                    arg_start = start_col + lines[start_line - 1][start_col:].find(
                        arg_name
                    )
                    arg_end = arg_start + len(arg_name)
                    symbol = Symbol(
                        type=SymbolType.VARIABLE,
                        text=arg_name,
                        start=Position(line=start_line, character=arg_start),
                        end=Position(line=start_line, character=arg_end),
                    )
                    symbols.append(symbol)

            # Class definitions with inheritance
            case ast.ClassDef(name=name, bases=bases):
                start_line = node.lineno
                start_col = node.col_offset + len("class ")
                end_col = start_col + len(name)
                symbol = Symbol(
                    type=SymbolType.CLASS,
                    text=name,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)
                for base in bases:
                    match base:
                        case ast.Name(id=base_name):
                            base_start = start_col + lines[start_line - 1][
                                start_col:
                            ].find(base_name)
                            base_end = base_start + len(base_name)
                            symbol = Symbol(
                                type=SymbolType.BASE_CLASS,
                                text=base_name,
                                start=Position(line=start_line, character=base_start),
                                end=Position(line=start_line, character=base_end),
                            )
                            symbols.append(symbol)

            # Assignments
            case ast.Assign(targets=targets):
                for target in targets:
                    match target:
                        case ast.Name(id=name):
                            start_line = target.lineno
                            start_col = target.col_offset
                            end_col = start_col + len(name)
                            symbol = Symbol(
                                type=SymbolType.VARIABLE,
                                text=name,
                                start=Position(line=start_line, character=start_col),
                                end=Position(line=start_line, character=end_col),
                            )
                            symbols.append(symbol)

            # Annotated assignments
            case ast.AnnAssign(target=ast.Name(id=name)):
                start_line = node.target.lineno
                start_col = node.target.col_offset
                end_col = start_col + len(name)
                symbol = Symbol(
                    type=SymbolType.VARIABLE,
                    text=name,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)

            # Global and Nonlocal
            case ast.Global(names=names) | ast.Nonlocal(names=names):
                start_line = node.lineno
                prefix = "global " if isinstance(node, ast.Global) else "nonlocal "
                start_col = node.col_offset + len(prefix)
                for name in names:
                    name_start = start_col + lines[start_line - 1][start_col:].find(
                        name
                    )
                    name_end = name_start + len(name)
                    symbol = Symbol(
                        type=SymbolType.VARIABLE,
                        text=name,
                        start=Position(line=start_line, character=name_start),
                        end=Position(line=start_line, character=name_end),
                    )
                    symbols.append(symbol)

            # Imports
            case ast.Import(names=names):
                start_line = node.lineno
                start_col = node.col_offset
                end_line = getattr(node, "end_lineno", start_line)
                end_col = getattr(node, "end_col_offset", start_col + len(str(node)))
                text = "import " + ", ".join(alias.name for alias in names)
                symbol = Symbol(
                    type=SymbolType.MODULE,
                    text=text,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=end_line, character=end_col),
                )
                symbols.append(symbol)

            case ast.ImportFrom(module=module, names=names):
                start_line = node.lineno
                start_col = node.col_offset
                end_line = getattr(node, "end_lineno", start_line)
                end_col = getattr(node, "end_col_offset", start_col + len(str(node)))
                text = f"from {module} import " + ", ".join(
                    alias.name for alias in names
                )
                symbol = Symbol(
                    type=SymbolType.MODULE,
                    text=text,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=end_line, character=end_col),
                )
                symbols.append(symbol)

            # Lambda
            case ast.Lambda(args=args):
                start_line = node.lineno
                start_col = node.col_offset + len("lambda ")
                end_col = start_col + 6
                symbol = Symbol(
                    type=SymbolType.FUNCTION,
                    text="lambda",
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)
                for arg in args.args:
                    arg_name = arg.arg
                    arg_start = start_col + lines[start_line - 1][start_col:].find(
                        arg_name
                    )
                    arg_end = arg_start + len(arg_name)
                    symbol = Symbol(
                        type=SymbolType.VARIABLE,
                        text=arg_name,
                        start=Position(line=start_line, character=arg_start),
                        end=Position(line=start_line, character=arg_end),
                    )
                    symbols.append(symbol)

            # Function calls (e.g., torch.randn)
            case ast.Call(func=func, args=args):
                match func:
                    case ast.Name(id=name):
                        start_line = func.lineno
                        start_col = func.col_offset
                        end_col = start_col + len(name)
                        symbol = Symbol(
                            type=SymbolType.FUNCTION,
                            text=name,
                            start=Position(line=start_line, character=start_col),
                            end=Position(line=start_line, character=end_col),
                        )
                        symbols.append(symbol)
                    case ast.Attribute(attr=attr):
                        start_line = func.lineno
                        start_col = func.col_offset + lines[start_line - 1][
                            func.col_offset :
                        ].find("." + attr)
                        end_col = start_col + len(attr) + 1
                        symbol = Symbol(
                            type=SymbolType.FUNCTION,
                            text=attr,
                            start=Position(line=start_line, character=start_col + 1),
                            end=Position(line=start_line, character=end_col),
                        )
                        symbols.append(symbol)
                for arg in args:
                    match arg:
                        case ast.Name(id=name):
                            arg_start = arg.col_offset
                            arg_end = arg_start + len(name)
                            symbol = Symbol(
                                type=SymbolType.VARIABLE,
                                text=name,
                                start=Position(line=arg.lineno, character=arg_start),
                                end=Position(line=arg.lineno, character=arg_end),
                            )
                            symbols.append(symbol)

            # Binary operators
            case ast.BinOp(left=left, op=op):
                op_name = OPP_MAPPING.get(type(op), "op")
                start_line = node.lineno
                start_col = left.end_col_offset
                end_col = start_col + len(op_name)
                symbol = Symbol(
                    type=SymbolType.OPERATOR,
                    text=op_name,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)

            # Unary operators
            case ast.UnaryOp(op=op):
                op_name = {
                    ast.Invert: "~",
                    ast.Not: "not",
                    ast.UAdd: "+",
                    ast.USub: "-",
                }.get(type(op), "op")
                start_line = node.lineno
                start_col = node.col_offset
                end_col = start_col + len(op_name)
                symbol = Symbol(
                    type=SymbolType.OPERATOR,
                    text=op_name,
                    start=Position(line=start_line, character=start_col),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)

            # Attributes (non-call)
            case ast.Attribute(attr=attr) if not isinstance(node, ast.Call):
                start_line = node.lineno
                start_col = node.col_offset + lines[start_line - 1][
                    node.col_offset :
                ].find("." + attr)
                end_col = start_col + len(attr) + 1
                symbol = Symbol(
                    type=SymbolType.ATTRIBUTE,
                    text=attr,
                    start=Position(line=start_line, character=start_col + 1),
                    end=Position(line=start_line, character=end_col),
                )
                symbols.append(symbol)

            case _:
                pass

    return symbols


def extract_symbols(code_str: str) -> list[Symbol]:
    symbols = _extract_from_tokens(code_str)
    try:
        tree = ast.parse(code_str)
        symbols.extend(_extract_from_ast(tree, code_str))
    except SyntaxError:
        pass
    symbols.sort(key=lambda x: (x.start.line, x.start.character))
    return symbols


# Example usage with the updated PyTorch script
if __name__ == "__main__":
    # Load code from ./example.py.ex
    code = Path("example.py.ex").read_text(encoding="utf-8")
    result = extract_symbols(code)
    for symbol in result:
        print(
            f"Type: {symbol.type:<12} Text: {symbol.text:<20} "
            f"Start: {symbol.start.line}:{symbol.start.character} "
            f"End: {symbol.end.line}:{symbol.end.character}"
        )
