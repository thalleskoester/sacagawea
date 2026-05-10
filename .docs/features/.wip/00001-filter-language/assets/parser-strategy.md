# Parser Strategy - V1

The v1 parser must be implemented with the Python standard library only, using a handwritten lexer and recursive-descent parser.

The implementation must not add a parser generator or parser-combinator dependency for v1. This keeps packaging simple for the initial library and makes source-span behavior fully controlled by the library.

The parser must produce the AST described in `ast-contract.md` and must enforce parse-time limits from `.docs/features/.wip/00001-filter-language/assets/safety-limits.md`.
