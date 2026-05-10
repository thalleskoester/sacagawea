---
name: Filter Language
description: Implement a Python library that parses a small filter language into a pure AST and evaluates it against in-memory dictionaries with structured errors, safety limits, and extension points.
spec: .docs/features/.wip/00001-filter-language/spec.md
---

# Execution Plan - Filter Language

## Purpose / Big Picture

This plan implements the v1 filter language described in `spec.md`. After the work is complete, a Python developer can install the `sacagawea` package, call `parse(query)` to produce a pure abstract filter tree, call `interpret(ast, data)` to filter a list of dictionaries, or call `evaluate(query, data)` as a convenience wrapper.

The end-to-end demo is a developer running a filter such as `[roles].query([role], [role].[name].eq("root"))` against in-memory dictionaries and receiving a `FinalResult` whose `result` contains the original matching dictionaries in input order and whose `elapsed` is a non-negative millisecond duration.

## Technical Context

* **Feature Categories**: `library-sdk`, `parser-compiler`
* **Branch Name**: `ai/feature/filter-language`
* **Language/Version**: Python `>=3.14`
* **Primary Dependencies**: Standard library only. The v1 parser uses a handwritten lexer and recursive-descent parser; no parser dependency is allowed for v1.
* **Packaging**: Existing `uv` project that must remain setuptools-backed and be configured with `src/sacagawea` package discovery, as defined in `.docs/features/.wip/00001-filter-language/assets/packaging.md`.
* **Storage**: N/A. The library operates on caller-provided in-memory Python values and must not persist data.
* **Testing**: `pytest==9.0.3`, `ruff==0.15.10`, `ty==0.0.30`, configured through `pyproject.toml`.
* **Current Repository State**: `src/` exists but is empty. There is no `tests/` directory, no package module, and no parser or interpreter code. This document is the feature execution plan.

## Constraints

* Implement v1 as a Python backend library, not as a web service, CLI, frontend, SQL compiler, or ORM compiler.
* Public entry points must be `parse(query: str, config: FilterConfig | None = None) -> AST`, `interpret(ast: AST, data: list[dict], config: FilterConfig | None = None) -> FinalResult`, and `evaluate(query: str, data: list[dict], config: FilterConfig | None = None) -> FinalResult`.
* `evaluate(...)` must use the same `FilterConfig` instance for parsing and interpretation.
* `FinalResult.result` must contain the original matching dictionary objects in original input order. It must not contain copies.
* `FinalResult.elapsed` must be a non-negative `float` measured in milliseconds with a monotonic clock.
* Parser output must be a pure data AST with no Python callables, bound host objects, compiled regex objects, or interpreter-specific state.
* Parsing must not consult runtime data, runtime function registries, method registries, or interpreter-specific method definitions.
* The grammar must parse function and method names generically and must not special-case runtime method names, including `.query(...)`.
* Runtime validation and interpretation must determine method existence, global function existence, argument counts, argument types, alias validity, alias scope, and whether predicate positions evaluate to `Boolean`.
* Field references, chained paths, and bare paths may parse successfully, but the default runtime must reject them with `invalid-predicate` when they are used where a predicate is required.
* The in-memory interpreter must accept only a top-level list whose items are dictionaries. Python class instances and object attribute access are out of scope.
* Filter strings must be treated as untrusted input.
* The parser and interpreter must not use Python `eval`, `exec`, dynamic imports, object attribute access, callables or methods discovered from filter source, AST nodes, record values, or host objects, or any Python execution primitive to evaluate filters. Explicitly configured `FilterConfig` extension callables (`RegexEvaluator` and `GlobalFunction`) are the only allowed runtime extension invocation path.
* Field visibility policy is the host application's responsibility. The library must not add v1 field allowlists or denylists.
* User literals are limited to `String`, `Integer`, and `Decimal`. Boolean, null, list, dictionary, date, time, and datetime literals are not part of v1 syntax.
* Runtime/internal types are `String`, `Integer`, `Decimal`, `Boolean`, `List`, `Dictionary`, `Date`, `Time`, `DateTime`, and `Null`.
* Python value mapping must avoid subclass ambiguity: `None`, then `bool`, then `datetime.datetime`, then `datetime.date`, then `datetime.time`, then `int`, then finite `float`, then `str`, then `list`, then `dict`.
* Non-finite floats and unsupported Python values must raise `unsupported-runtime-value` when reached.
* Missing fields and missing path segments must raise structured runtime exceptions. `isNull()` must not treat missing data as null.
* `.regex(...)` must use regex semantics, default to Python `re.search`, and be case-sensitive.
* The default Python regex evaluator's catastrophic-backtracking risk must be documented, along with the custom regex evaluator escape hatch.
* Runtime validation must follow reachability. Record-dependent errors in short-circuited branches must not be raised for that record.
* Evaluation must fail on the first structured runtime exception and must not return partial matches.
* `FilterConfig` settings must be scoped to the call that receives them and must not mutate process-global language behavior.
* Safety limits must cover maximum source length, parse tree depth, function or method argument count, path depth, and query nesting. Limit counting rules must be deterministic, documented, tested, and overrideable through `FilterConfig`.
* Filter source, methods, global functions, and runtime extensions must not raise, lower, disable, or mutate the effective `SafetyLimits` for a call; limits are supplied only by `FilterConfig` before parsing or evaluation begins.
* Every structured exception must inherit from a common library base exception and expose a stable programmatic identity plus the required machine-readable context fields from the spec.
* Direct `Time` and `DateTime` comparison must require timezone-aware runtime values and timezone-aware string arguments. `Date` comparison accepts `YYYY-MM-DD`.
* `Time` comparison normalizes offsets into UTC time-of-day and ignores date rollover.
* Dictionary keys that are not strings are ignored by path lookup and alias/root-field collision checks.

## Artifacts

These artifacts are settled before implementation and must be treated as stable v1 implementation contracts. Each asset lives in its own file.

| Type | Path | Description |
|---|---|---|
| `packaging` | `.docs/features/.wip/00001-filter-language/assets/packaging.md` | `uv`/setuptools packaging contract, `src/sacagawea` layout, package discovery, package name, inactive legacy empty declarations, and README metadata requirement. |
| `public-api` | `.docs/features/.wip/00001-filter-language/assets/public-api.md` | Public entry points `parse`, `interpret`, `evaluate`, plus exported data objects and exception names. |
| `parser-strategy` | `.docs/features/.wip/00001-filter-language/assets/parser-strategy.md` | Standard-library handwritten lexer and recursive-descent parser decision for v1. |
| `ast-contract` | `.docs/features/.wip/00001-filter-language/assets/ast-contract.md` | Concrete pure-data AST root, source span, and expression node variants. |
| `grammar-contract` | `.docs/features/.wip/00001-filter-language/assets/grammar-contract.md` | v1 syntax for whitespace, comments, trailing commas, string escapes, numeric literals, identifiers, bracketed paths, global calls, method calls, and unsupported literal forms. |
| `safety-limits` | `.docs/features/.wip/00001-filter-language/assets/safety-limits.md` | Default v1 safety limit values and deterministic counting rules. |
| `filter-config` | `.docs/features/.wip/00001-filter-language/assets/filter-config.md` | Immutable call-scoped configuration contract for safety limits, regex evaluator, and global functions. |
| `runtime-values` | `.docs/features/.wip/00001-filter-language/assets/runtime-values.md` | Runtime/internal type names, runtime value wrapper expectations, and Python value mapping order. |
| `runtime-method-model` | `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md` | Supported methods for `List`, `Dictionary`, `Boolean`, `Integer`, `Decimal`, `String`, `Date`, `Time`, `DateTime`, and `Null`, including method arity and type rules. |
| `runtime-extensions` | `.docs/features/.wip/00001-filter-language/assets/runtime-extensions.md` | Regex evaluator, default global functions, custom global functions, and runtime context contracts. |
| `temporal-format-contract` | `.docs/features/.wip/00001-filter-language/assets/temporal-formats.md` | Accepted `Date`, `Time`, and `DateTime` string formats and timezone-awareness rules. |
| `error-contract` | `.docs/features/.wip/00001-filter-language/assets/errors.md` | Stable structured error identities, base exception hierarchy, and required context fields. |
| `assertion-suite` | `.docs/features/.wip/00001-filter-language/assets/assertions.md` | Required assertion coverage statuses for the spec's Happy Path, Edge Cases, Error States, Anti-Behaviors, and Integration sections. |

---

## Phase 00001: Package Contract Skeleton

### Slice goal

Create an installable package skeleton with the public API names, contract-defined data containers, exception hierarchy, default configuration object, and test harness. This slice proves that downstream implementation slices have a real library surface to build behind.

### Context

The repository is a `uv` Python project with an empty `src/` directory. `pyproject.toml` currently declares `package = true` but has no package discovery configured and no `README.md`, even though `readme = "README.md"` is declared. A minimal package skeleton is a true blocker because no parser, interpreter, or tests can import the library yet.

For this phase, "contract skeleton" means public classes, functions, and immutable data containers exist with the names and fields defined in the asset files. Later phases fill in parser and interpreter behavior behind this stable surface.

### Outcomes

After this phase, `pytest`, `ruff`, and `ty` can run against a real package. A developer can import `sacagawea`, inspect the public entry points, construct a `FilterConfig`, and inspect default `SafetyLimits`.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00001` | - | Configure packaging exactly as described in `.docs/features/.wip/00001-filter-language/assets/packaging.md` and add the minimal README required by the project metadata. |
| `T00002` | `T00001` | Add the public package module that exports every name listed in `.docs/features/.wip/00001-filter-language/assets/public-api.md`. |
| `T00003` | `T00001` | Add the immutable public pure-data containers from `.docs/features/.wip/00001-filter-language/assets/ast-contract.md`, `.docs/features/.wip/00001-filter-language/assets/public-api.md`, `.docs/features/.wip/00001-filter-language/assets/safety-limits.md`, and `.docs/features/.wip/00001-filter-language/assets/filter-config.md`. If the implementation later uses a runtime value wrapper from `.docs/features/.wip/00001-filter-language/assets/runtime-values.md`, keep it internal. |
| `T00004` | `T00001` | Add the structured exception hierarchy, including every exception class listed in `.docs/features/.wip/00001-filter-language/assets/public-api.md` and all fixed `code` values, `message`, `cause`, base classes, and context-field support from `.docs/features/.wip/00001-filter-language/assets/errors.md`. |
| `T00005` | `T00002`, `T00003`, `T00004` | Implement temporary `parse`, `interpret`, and `evaluate` bodies that preserve signatures and use `FilterConfig.default()` when config is omitted. Do not add a temporary public error identity; parser and interpreter behavior phases own public exception behavior. |
| `T00006` | `T00001` | Create `tests/` with import, public API, `FilterConfig()` and `FilterConfig.default()` equivalence, documented `FilterConfig` field defaults, `SafetyLimits()` and `SafetyLimits.default()` defaults, keyword construction and readable field tests for every public immutable data object, exception hierarchy, context-field, and data-container immutability tests. Initialize the assertion matrix entries covered by this phase. |
| `T00007` | `T00006` | Run `pytest`, `ruff`, `ty`, and a minimal package import check through the repository's `uv` workflow; fix package-layout and type-checking issues before moving to parser work. |

### Acceptance criteria

* Every name listed in `.docs/features/.wip/00001-filter-language/assets/public-api.md` is importable from the package root and included in the public export contract.
* The package root exists at `src/sacagawea/__init__.py`; no root-level `sacagawea/` package is used for v1.
* `pyproject.toml` uses `[tool.setuptools.packages.find]` with `where = ["src"]`, and the old empty `[tool.setuptools] packages = []` and `py-modules = []` declarations are removed or otherwise not active.
* `README.md` exists before Phase 00001 quality gates run because project metadata references it.
* `FilterConfig.default()` and `FilterConfig()` return equivalent immutable or mutation-safe default configuration values with `SafetyLimits.default()`, `regex_evaluator is None`, `include_default_global_functions is True`, and an empty `global_functions` mapping.
* `SafetyLimits.default()` and `SafetyLimits()` produce immutable values with exactly the documented default limit values from `.docs/features/.wip/00001-filter-language/assets/safety-limits.md`.
* `AST(root=..., source_span=...)` is constructible, immutable, and is the object returned by `parse(...)` once parser behavior is implemented.
* All structured exceptions inherit from the exact base hierarchy in `.docs/features/.wip/00001-filter-language/assets/errors.md` and expose `message`, `code`, `cause`, and required context fields.
* A minimal `uv`-managed import check can import `sacagawea` through the configured package layout.
* `pytest`, `ruff`, and `ty` pass for the skeleton package.

---

## Phase 00002: Generic Parser And Pure AST

### Slice goal

Implement syntactic parsing into the stable pure-data AST without runtime validation. This slice makes `parse(query)` useful on its own and proves that the standard-library parser can represent all v1 expression shapes generically.

### Context

The parser must understand filter-language syntax but must not know whether runtime methods or functions exist. An AST is a plain data representation of parsed structure using `.docs/features/.wip/00001-filter-language/assets/ast-contract.md`. It must distinguish literals, bracketed paths, global function calls, method calls, argument order, and source locations.

### Outcomes

After this phase, developers can parse valid examples from the spec, inspect a pure AST, and receive structured syntax or limit errors for malformed source. Runtime method validity, predicate validity, alias rules, and type checks are still intentionally deferred.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00008` | `T00007` | Implement the handwritten lexer and recursive-descent parser from `.docs/features/.wip/00001-filter-language/assets/parser-strategy.md` using the AST node classes from `.docs/features/.wip/00001-filter-language/assets/ast-contract.md`. |
| `T00009` | `T00008` | Implement lexical handling for whitespace, `//` line comments, `/* ... */` block comments, bracketed identifiers, function and method identifiers, parentheses, dots, commas, string delimiters, and numeric literal forms. |
| `T00010` | `T00009` | Implement string literal unescaping for `\\`, `\"`, `\'`, `\n`, and `\t`, with structured syntax errors for unsupported escapes and unterminated strings. |
| `T00011` | `T00009` | Implement integer and decimal parsing for all valid numeric literal forms from `.docs/features/.wip/00001-filter-language/assets/grammar-contract.md`, preserving `Integer` versus `Decimal` literal category in the AST. |
| `T00012` | `T00009`, `T00010`, `T00011` | Implement expression parsing for bracketed paths, global calls, path-receiver method calls, call arguments that may themselves be expressions, trailing commas, and whitespace around separators such as `[first_name] . eq ( "john" , )`. |
| `T00013` | `T00012` | Enforce parse-time safety limits for source length, parse tree depth, function or method argument count, and path depth using `FilterConfig.safety_limits` and the deterministic counting rules from `.docs/features/.wip/00001-filter-language/assets/safety-limits.md`. |
| `T00014` | `T00012` | Reject unsupported syntactic forms with `syntax-error`, including non-ASCII identifiers, identifiers that start with digits, hyphens in function or method symbols, list literals, dictionary literals, boolean literals, null literals, date literals, time literals, datetime literals, incomplete calls, malformed paths, and method-call receivers that are not path expressions such as literal receivers, global-call receivers, and method-call receivers. |
| `T00015` | `T00013`, `T00014` | Add parser tests covering valid examples, every AST node variant and required field from `.docs/features/.wip/00001-filter-language/assets/ast-contract.md`, semantic AST shape equivalence excluding `source_span`, exact root and child source spans on single-line input, multiline input, comments, whitespace around separators, and escaped strings, comments as AST-free trivia, string escapes in both quote styles including unsupported escape failures, numeric forms, arbitrary valid function symbols and invalid symbols, trailing commas in function and method calls without extra arguments, rejected non-path method receivers, default and overridden `ParseLimitExceededError` failures with exact `limit_name`, `limit_value`, and `actual_value`, deterministic limit counting rules, and syntax-error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00016` | `T00015` | Run `pytest`, `ruff`, and `ty`; resolve parser and AST typing issues. |

### Acceptance criteria

* `parse('[first_name].eq("john")')` returns a pure AST without consulting runtime data or method registries.
* `parse('[first_name] . eq ( "john" , )')` produces the same expression topology, literal values, path segments, function names, method names, and argument order as `parse('[first_name].eq("john")')`, excluding `source_span`; all `source_span` values reflect the actual input source.
* The parser accepts comments, calls nested inside argument lists, chained paths, valid decimal forms, valid string escapes, and trailing commas.
* The parser treats `.query(...)`, `and(...)`, `or(...)`, `not(...)`, unknown method names, and unknown function names as generic call structures.
* Malformed syntax raises `FilterParseError`; exceeded parse-time limits raise `ParseLimitExceededError` with code `limit-exceeded`, required context fields, and catchability through `LimitExceededError`.
* Parser tests prove that AST source spans and syntax or limit error spans match `.docs/features/.wip/00001-filter-language/assets/ast-contract.md` across literals, paths, global calls, method calls, calls nested in arguments, comments, whitespace, and trailing commas.
* Parser tests prove that AST nodes contain no Python callables, bound host objects, compiled regex objects, runtime state, process-global state, lists, dictionaries, sets, or other mutable collections; path segments and call arguments are tuples.
* Parser tests prove that configured parse-time safety limits override defaults for only the current call.
* Project metadata and parser modules contain no parser generator or parser-combinator dependency or import; the parser implementation uses only the Python standard library.

---

## Phase 00003: Minimal In-Memory Predicate Evaluation

### Slice goal

Implement the first complete parse-to-interpret path for equality and simple comparisons against top-level dictionary fields. This slice demonstrates the library's core value before adding the full method surface.

### Context

The in-memory interpreter evaluates an AST against a top-level list of dictionary records. A predicate is an expression that evaluates to `Boolean`. A bare field path is not a predicate in v1, even though it parses successfully.

### Outcomes

After this phase, `[first_name].eq("john")`, `[age].ge(21)`, `[balance].lt(.5)`, and `[name].gt("Jane")` work through both `interpret(parse(query), data)` and `evaluate(query, data)`.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00017` | `T00016` | Validate that `interpret(...)` receives a top-level list and that every item is a dictionary; raise `InvalidRecordError` for unsupported top-level shapes or supported runtime values in unsupported record positions, using `record_index=None` for non-list top-level data and integer indexes for non-dictionary list items. |
| `T00018` | `T00017` | Implement runtime value classification for `String`, `Integer`, `Decimal`, `Boolean`, `List`, `Dictionary`, `Date`, `Time`, `DateTime`, and `Null` using the mapping order from `.docs/features/.wip/00001-filter-language/assets/runtime-values.md`, carrying logical path context for classified root field values when available. |
| `T00019` | `T00018` | Implement root dictionary field resolution for single-segment paths, ignoring non-string keys and raising `missing-field-or-path-segment` for missing string keys. |
| `T00020` | `T00019` | Implement method dispatch for `eq`, `gt`, `ge`, `lt`, and `le` on `String`, `Integer`, and `Decimal`, including numeric cross-comparison between integers and decimals. |
| `T00021` | `T00020` | Implement predicate enforcement for the top-level expression, raising `invalid-predicate` for bare paths or non-Boolean results. Predicate argument enforcement for logical functions and `.query(...)` is introduced in the phases that add those call forms. |
| `T00022` | `T00020`, `T00021` | Implement `interpret(...)` record iteration, first-error failure behavior, preservation of original matching dictionary objects, no mutation of input records, input order, and `FinalResult.elapsed`. |
| `T00023` | `T00022` | Implement `evaluate(...)` as parse plus interpret using the same config object and measuring elapsed time across both phases. |
| `T00024` | `T00023` | Add tests for equality, numeric comparisons, string comparisons, empty input, input-record non-mutation, original-object preservation, result ordering, invalid records for supported runtime values in unsupported record positions, unsupported top-level or list-item values raising `unsupported-runtime-value`, missing fields, unsupported methods, wrong argument count, wrong argument type, invalid predicate, a runtime classification matrix for every category in `.docs/features/.wip/00001-filter-language/assets/runtime-values.md`, unsupported and non-finite values only failing when reached, required error context fields, omitted-config default behavior, and elapsed timing. Update the assertion matrix for assertions covered by this phase. |
| `T00025` | `T00024` | Run `pytest`, `ruff`, and `ty`; resolve runtime and typing issues. |

### Acceptance criteria

* The first spec happy path works: parsing and evaluating `[first_name].eq("john")` returns only records whose `first_name` is exactly `"john"`.
* Numeric and string comparison methods behave according to the v1 type model.
* `interpret(ast, data)` and `evaluate(query, data)` produce the same `FinalResult.result` for supported expressions.
* Implemented `parse`, `interpret`, and `evaluate` calls with omitted `config` use `FilterConfig.default()` behavior consistently after parser and interpreter behavior replaces skeleton bodies.
* `FinalResult.elapsed` is numeric, non-negative, and measured with a monotonic clock.
* Missing fields, invalid records, unsupported methods, wrong argument counts, wrong argument types, unsupported runtime values, and bare-path predicates raise structured runtime exceptions with required context fields, including path context for root-field `unsupported-runtime-value` errors.
* Unsupported or non-finite values in unreferenced fields do not fail evaluation, while the same values fail with `unsupported-runtime-value` when the queried path reaches them.
* Supported runtime values in unsupported interpreter positions raise `invalid-record`; unmappable Python values in those positions raise `unsupported-runtime-value`.
* Evaluation does not mutate the input list or dictionaries, and matching results contain the original dictionary objects.
* Evaluation fails on the first runtime exception and does not return partial matches.

---

## Phase 00004: Null, Boolean, Numeric, And Regex Methods

### Slice goal

Complete null checks across all runtime values plus the non-temporal Boolean, numeric truthiness, and string regex method surface. This slice keeps these method behaviors independently demoable before global function extension work.

### Context

These methods are runtime behavior. The parser only provides generic method-call AST nodes. Method arity and argument type rules come from `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md`. `.regex(...)` uses the regex evaluator from `FilterConfig`, defaulting to Python `re.search` semantics, with the callable contract defined in `.docs/features/.wip/00001-filter-language/assets/runtime-extensions.md`.

### Outcomes

After this phase, developers can evaluate filters such as `[is_active].isTrue()`, `[count].isFalse()`, `[deleted_at].isNull()`, and `[title].regex(".*snow white.*")`, including configured regex evaluator behavior.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00026` | `T00025` | Implement `isNull()` for every resolved field or path value, returning true only when the existing value is Python `None`. |
| `T00027` | `T00026` | Implement `isTrue()` and `isFalse()` for `Boolean`, `Integer`, and `Decimal`, including true Boolean classification before integer classification and numeric zero/nonzero truthiness. |
| `T00028` | `T00027` | Implement `.regex(<string>)` for `String` using the configured regex evaluator contract, with default case-sensitive Python `re.search` behavior. |
| `T00029` | `T00028` | Raise `InvalidRegexError` for invalid default regex patterns, propagate library-defined structured exceptions raised by custom regex evaluators unchanged, validate that custom regex evaluators return `bool`, and wrap unexpected custom evaluator exceptions or invalid return values in a library-defined structured exception that preserves the original exception as `cause`, without adding an error identity outside the closed spec. |
| `T00030` | `T00029` | Add tests for Boolean methods, numeric truthiness, `isNull()` on every runtime/internal type, missing-is-not-null behavior, regex partial matching, custom regex evaluator use, custom regex structured exception propagation, custom regex non-`bool` returns, invalid regex, method arity errors, method wrong-argument-type errors, config isolation between regex calls, and required error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00031` | `T00030` | Run `pytest`, `ruff`, and `ty`; resolve null, Boolean, numeric, and regex method issues. |

### Acceptance criteria

* `[is_active].isTrue()` returns true only for Python `True`, and Python `True`/`False` are not treated as integers.
* `[count].isTrue()` and `[count].isFalse()` follow zero/nonzero numeric truthiness.
* `[deleted_at].isNull()` returns true only when the key exists and the value is `None`; missing fields still raise missing-path errors.
* `.regex(...)` matches partial strings via `re.search`, is case-sensitive, and raises `InvalidRegexError` for invalid default regex patterns.
* A caller can provide a custom regex evaluator and `.regex(...)` uses it without changing the AST.
* Custom regex evaluators must return `bool`; library-defined structured exceptions propagate unchanged, and unexpected custom evaluator failures are wrapped in a library-defined structured exception that preserves the original exception as `cause`.
* `isNull()` tests cover each runtime/internal type, proving existing non-null values return false, `Null` returns true, and missing fields/path segments still raise `missing-field-or-path-segment`.
* Method arity failures use `wrong-argument-count`; method argument type failures use `wrong-argument-type`.

---

## Phase 00005: Configured Logical Functions

### Slice goal

Implement default and configured global functions. This slice provides Boolean composition, short-circuiting, and the custom global function extension point without bundling it into method work.

### Context

Default logical functions are runtime language objects, not parser concepts. `and(...)` and `or(...)` are variadic and short-circuit left to right. `not(...)` accepts exactly one argument. Custom global functions are configured through `FilterConfig` and use the runtime extension contract from `.docs/features/.wip/00001-filter-language/assets/runtime-extensions.md`.

### Outcomes

After this phase, developers can evaluate compound filters such as `and([is_active].isTrue(), [title].regex(".*snow white.*"))`, register a custom global function, replace or remove default global functions for one call, and rely on short-circuit behavior to prevent record-dependent errors in unreached branches.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00032` | `T00031` | Implement effective global function registry resolution from `FilterConfig`, including default-included and default-excluded registries, `and(...)`, `or(...)`, and `not(...)` with required arity, left-to-right evaluation, Boolean predicate enforcement, short-circuit behavior, and `None` removal overlays. |
| `T00033` | `T00032` | Implement the custom global function runtime context capabilities from `.docs/features/.wip/00001-filter-language/assets/runtime-extensions.md`, including unevaluated argument expressions, `evaluate`, `evaluate_predicate`, `argument_count`, `record_index`, call-scoped `config`, structured exception propagation or wrapping, and classification of returned raw Python values through the runtime value model. Before `.query(...)` support exists, evaluations happen only in root scope; query phases wire the same helpers into active alias scopes. |
| `T00034` | `T00033` | Add tests for custom global functions, `include_default_global_functions=False`, default function replacement/removal, no-op removal of absent functions, config isolation between calls, logical arity errors, invalid logical predicates, short-circuit success, short-circuit non-evaluation of record-dependent failures, runtime context capabilities, unsupported custom-function return values, non-Boolean predicate-position custom returns, custom structured exception propagation, extension failure wrapping, and required error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00035` | `T00034` | Run `pytest`, `ruff`, and `ty`; fix only failures caused by this phase's implementation. Contract changes require updating the owning plan asset before proceeding and cannot change the closed spec. |

### Acceptance criteria

* `and(...)`, `or(...)`, and `not(...)` enforce their arity and predicate rules through the effective `FilterConfig` global function registry and short-circuit left to right.
* A caller can register, replace, or remove a global function for one call without mutating default behavior in another call.
* Custom global functions can evaluate arguments through the runtime context and either return raw Python values that the interpreter classifies through the runtime value model or raise library-defined structured exceptions.
* Custom global function calls in predicate position must classify to `Boolean`; otherwise they raise `invalid-predicate`.
* Unsupported custom global function return values raise `unsupported-runtime-value` with the context fields required by the closed spec.
* Any function arity failure surfaced by default or custom global function handling uses `wrong-argument-count`; custom functions can raise that structured exception unchanged.
* Unexpected custom global function failures are wrapped in a library-defined structured exception that preserves the original exception as `cause`, as required by the closed spec.
* Tests prove that record-dependent errors in unreached logical branches are not raised for that record.

---

## Phase 00006: Chained Dictionary Paths

### Slice goal

Add nested dictionary path access beyond root fields. This slice lets filters traverse in-memory dictionary records end to end without introducing temporal comparison rules yet.

### Context

Chained path access walks through dictionaries by string keys that match the filter-language identifier rules. Dictionary keys that are not strings are ignored by path lookup. Access through unsupported receiver types is an invalid path access, not a missing key.

### Outcomes

After this phase, filters can traverse expressions such as `[customer].[address].[city].eq("Paris")` and receive precise structured errors for missing nested keys or invalid traversal through non-dictionary values.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00036` | `T00035` | Extend path resolution to chained dictionary access with `missing-field-or-path-segment` for missing keys and `invalid-path-access` for traversal through unsupported receiver types. |
| `T00037` | `T00036` | Preserve logical path information through nested resolution so `missing-field-or-path-segment`, `invalid-path-access`, `unsupported-method`, and `unsupported-runtime-value` errors expose the required context fields. |
| `T00038` | `T00037` | Add tests for nested dictionary paths, missing root keys, missing nested keys, invalid traversal through scalar values, non-string dictionary keys being ignored, unsupported values only failing when reached through nested paths, and required error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00039` | `T00038` | Run `pytest`, `ruff`, and `ty`; resolve chained-path issues. |

### Acceptance criteria

* `[customer].[address].[city].eq("Paris")` resolves through dictionary keys and filters correctly.
* Missing root fields and missing nested path segments raise `missing-field-or-path-segment`; invalid traversal receivers raise `invalid-path-access`.
* Non-string dictionary keys are ignored by path lookup.
* Errors introduced by this phase use the exact identities and context fields from `.docs/features/.wip/00001-filter-language/assets/errors.md`.

---

## Phase 00007: List Query Baseline

### Slice goal

Implement the baseline `.query(<item_alias>, <query>)` behavior for runtime lists, including scalar and dictionary list items.

### Context

The parser treats `.query(...)` as a generic method call. Only the runtime method contract validates that the first argument is a single bracketed segment and establishes alias scope for the body.

### Outcomes

After this phase, developers can filter records with list predicates such as `[roles].query([role], [role].[name].eq("root"))` and `[last_ips].query([ip], [ip].regex("10\\.238\\.115\\..*"))`. Nested query scopes, alias collision policy, and root-field collision policy are completed in the next phase. The baseline query nesting limit is enforced here because even the outermost `.query(...)` call has runtime query depth.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00040` | `T00039` | Implement `.query(...)` dispatch only for runtime `List`, returning true when at least one list item satisfies the nested predicate and false for empty lists. This query baseline depends on chained dictionary paths, not on temporal behavior. |
| `T00041` | `T00040` | Validate `.query(...)` arity, reject invalid first arguments with `invalid-alias-declaration` when the alias is not exactly one bracketed segment, and enforce that the query body evaluates to `Boolean`, raising `invalid-predicate` for bare paths, aliases, or non-Boolean body results. |
| `T00042` | `T00041` | Implement single-query alias scope tracking so the first path segment resolves to the active item alias inside the query body and otherwise resolves against the root record. |
| `T00043` | `T00042` | Wire custom global function context evaluation helpers through the active single-query alias scope so configured functions called inside a query body evaluate paths with the same alias visibility as built-in runtime evaluation. |
| `T00044` | `T00043` | Ensure item evaluation failures inside `.query(...)` fail the whole evaluation immediately, nonmatching but valid items continue to later items, matching items stop evaluation before later items, and `maximum_query_nesting` is enforced for every reached `.query(...)` call with the outermost reached query counted as depth 1. |
| `T00045` | `T00044` | Add tests for dictionary list items, scalar list items, empty lists, mixed scalar/dictionary lists, invalid alias declaration, query body predicate validation, custom global functions called inside query bodies with active aliases, first-match short-circuit before invalid later items, item failure propagation, unsupported receiver type, query nesting default and override limit failures for baseline calls, method arity/type errors, and required error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00046` | `T00045` | Run `pytest`, `ruff`, and `ty`; resolve baseline query behavior issues. |

### Acceptance criteria

* `[roles].query([role], [role].[name].eq("root"))` returns true when at least one role dictionary matches.
* `[last_ips].query([ip], [ip].regex("10\\.238\\.115\\..*"))` supports scalar list item aliases.
* Empty lists return false without error.
* Invalid alias declarations, invalid query body predicates, unsupported query receivers, and query nesting limit failures raise the required structured errors.
* A matching item short-circuits `.query(...)` before evaluating later items, including invalid later items.
* `.query(...)` method arity failures use `wrong-argument-count`; method argument type failures use `wrong-argument-type`, except invalid alias shape which raises `invalid-alias-declaration`.

---

## Phase 00008: Nested Query Scope Rules And Limits

### Slice goal

Complete nested `.query(...)` semantics, alias visibility, alias collision policy, root-field collision policy, sibling alias reuse, and query nesting limits.

### Context

Alias names resolve before root fields only while active, and outer aliases remain visible inside nested query bodies. Query nesting is a runtime limit because the parser must not special-case the `.query(...)` method name.

### Outcomes

After this phase, nested query examples from the spec work, sibling alias reuse is valid, active alias shadowing is rejected, root-field collisions are rejected when reached, and configured query nesting limits are enforced.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00047` | `T00046` | Implement nested alias scope tracking so inner query bodies can reference both outer aliases and their own item alias. |
| `T00048` | `T00047` | Extend custom global function context evaluation helpers through nested alias scopes so configured functions see the same active aliases as built-in runtime evaluation. |
| `T00049` | `T00048` | Implement alias collision detection across active outer and current query scopes while allowing alias reuse in separate sibling query calls. |
| `T00050` | `T00049` | Implement runtime alias/root-field collision detection for the current root record, ignoring non-string dictionary keys. |
| `T00051` | `T00050` | Extend `maximum_query_nesting` enforcement through nested `.query(...)` validation and evaluation, preserving the counting rule that the outermost reached query has nesting depth 1. |
| `T00052` | `T00051` | Add tests for nested queries referencing outer aliases, sibling alias reuse, alias collisions, root-field collisions, custom global functions called inside nested query bodies with outer and inner aliases, non-string root keys being ignored for collision checks, nested query nesting default and override limits, deterministic query nesting counting, and required error context fields. Update the assertion matrix for assertions covered by this phase. |
| `T00053` | `T00052` | Run `pytest`, `ruff`, and `ty`; resolve nested query and limit issues. |

### Acceptance criteria

* Nested queries can reference outer aliases and inner aliases according to scope rules.
* Reusing an alias in sibling query calls is valid, but shadowing an active alias raises `alias-collision`.
* Root records containing a string key that collides with a reached query alias raise `runtime-alias-root-field-collision`.
* Query nesting default and override limit failures raise `RuntimeLimitExceededError` with code `limit-exceeded`, deterministic context, and catchability through `LimitExceededError`.

---

## Phase 00009: Temporal Components And Comparisons

### Slice goal

Add temporal component access and date/time/datetime comparisons for Python temporal values supplied by host records.

### Context

Temporal runtime values are supplied by Python records, not by filter-language literals. `Date`, `Time`, and `DateTime` comparison methods accept string arguments and parse them at runtime. Temporal components such as `[created_at].[year]` are derived integer comparison values with the explicit component method surface from `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md`.

### Outcomes

After this phase, filters can access `[created_at].[year]`, compare Python `date` values to `YYYY-MM-DD` strings, compare timezone-aware `time` values, and compare timezone-aware `datetime` values to accepted ISO 8601 strings.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00054` | `T00053` | Implement temporal component access for `Date`, `Time`, and `DateTime`, exposing the integer components listed in `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md`. |
| `T00055` | `T00054` | Implement `eq`, `gt`, `ge`, `lt`, and `le` for runtime values classified as `Date`, excluding `datetime.datetime` receivers, against `YYYY-MM-DD` string arguments from `.docs/features/.wip/00001-filter-language/assets/temporal-formats.md`. |
| `T00056` | `T00055` | Implement timezone-aware `Time` comparison against accepted time strings, normalizing offsets to UTC time-of-day and ignoring date rollover. |
| `T00057` | `T00056` | Implement timezone-aware `DateTime` comparison against accepted datetime strings, normalizing offsets and comparing represented instants. |
| `T00058` | `T00057` | Raise `invalid-temporal-string` for unparsable or wrong-format temporal strings and `temporal-awareness-mismatch` for direct time or datetime comparison with non-timezone-aware runtime values or string arguments. Add tests for date comparisons, `datetime.datetime` dispatching as `DateTime` rather than `Date`, time and datetime comparisons using `Z`, `+00:00`, and negative offsets, time rollover normalization while ignoring date rollover, temporal components, exact accepted and rejected temporal formats, parseable naive Time/DateTime strings raising `temporal-awareness-mismatch`, syntactically wrong temporal strings raising `invalid-temporal-string`, temporal component method dispatch, component unsupported-method failures, method arity/type failures, required error context fields, and assertion matrix entries covered by this phase. Run `pytest`, `ruff`, and `ty`; resolve temporal issues. |

### Acceptance criteria

* `[created_at].[year].eq(2026)` and `[created_at].[hour].ge(9)` expose temporal components as integers.
* `Date`, `Time`, and `DateTime` comparison methods accept only the specified string formats and raise structured temporal errors for invalid or awareness-mismatched inputs.
* Time comparison normalizes offsets into UTC time-of-day and treats `09:30:00Z` and `06:30:00-03:00` as equal.
* Time comparison tests include rollover cases such as `23:30:00-02:00` normalizing to `01:30:00Z` and `00:30:00+02:00` normalizing to `22:30:00Z`, proving date rollover is ignored after UTC time-of-day normalization.
* Tests cover every listed `Date`, `Time`, and `DateTime` component; component methods are limited to `isNull`, `eq`, `gt`, `ge`, `lt`, and `le`; `isTrue()` and `isFalse()` on temporal components raise `unsupported-method`.
* Temporal method arity failures use `wrong-argument-count`; temporal method argument type failures use `wrong-argument-type`.
* Errors introduced by this phase use the exact identities and context fields from `.docs/features/.wip/00001-filter-language/assets/errors.md`.

---

## Phase 00010: Public Documentation And Assertion Matrix

### Slice goal

Document the completed public contract and map the spec assertions to executable coverage. This slice verifies that behavior introduced earlier is understandable and traceable without postponing error design to the end.

### Context

Earlier phases must introduce the exact structured errors required by their behavior. This phase publishes coverage evidence, documents how to use the library safely, and records any intentional v1 limitations. It must not become a catch-all implementation phase; missing behavior or missing tests must send work back to the behavior phase that owns the assertion.

### Outcomes

After this phase, host applications can understand the public API, AST reuse model, configuration contract, default safety limits, regex risk, field-visibility responsibility, extension points, and v1 non-goals.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00059` | `T00058` | Verify that each earlier behavior phase already introduced its required error identities, method arity/type failures, function arity failures, and context-field tests against `.docs/features/.wip/00001-filter-language/assets/errors.md`, `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md`, and `.docs/features/.wip/00001-filter-language/assets/runtime-extensions.md`. If coverage is missing, return the work to the owning behavior phase instead of adding catch-all tests here. |
| `T00060` | `T00059` | Add documentation for public API usage, AST purity, default safety limits, deterministic limit counting, runtime type mapping, custom regex evaluator risk, custom global function extension, field visibility responsibility, and v1 non-goals. |
| `T00061` | `T00060` | Create or update the maintained assertion matrix so every assertion in `.docs/features/.wip/00001-filter-language/assets/assertions.md` is mapped to `covered` or `covered-by-contract`, no assertion remains unmapped, and every earlier phase's assertion-matrix updates are reconciled against the final implementation. Any unmapped assertion blocks this phase and must be fixed in its owning behavior phase. |
| `T00062` | `T00061` | Verify that the Phase 00003 integration tests already prove the interpreter does not mutate input records and returns original dictionary objects; do not add duplicate late regression coverage unless those tests are moved back into the owning phase. |
| `T00063` | `T00062` | Run `pytest`, `ruff`, and `ty`; fix only failures caused by documentation or assertion-matrix work. Contract changes require updating the owning plan asset before proceeding and cannot change the closed spec. |

### Acceptance criteria

* Every error identity listed in `.docs/features/.wip/00001-filter-language/assets/errors.md` is distinguishable without parsing the message.
* Every error identity exposes the required machine-readable context fields from `.docs/features/.wip/00001-filter-language/assets/errors.md`.
* Public docs explain the three entry points, `FinalResult`, `FilterConfig`, AST reuse, safety limits, regex risk, custom global functions, custom regex evaluators, field visibility responsibility, and v1 non-goals.
* Public docs and contract checks make the AST contract the stable interpreter input boundary; `INT-006` is marked `covered-by-contract` through AST contract tests and documentation.
* Every runtime method in `.docs/features/.wip/00001-filter-language/assets/runtime-methods.md`, including `.query(...)` and temporal component methods, has `wrong-argument-count` and `wrong-argument-type` coverage, except invalid `.query(...)` alias shape which raises `invalid-alias-declaration`.
* The assertion matrix contains every assertion ID from `.docs/features/.wip/00001-filter-language/assets/assertions.md`, uses only `covered` or `covered-by-contract`, contains no documented exclusions, and blocks completion if any assertion cannot be implemented.
* Tests from the owning behavior phases cover the complete public error hierarchy and all required context fields introduced by implemented behavior.
* Phase 00003 integration tests prove input dictionaries are not mutated and matched results contain the original dictionary objects.

---

## Phase 00011: Release Readiness And Contract Lock

### Slice goal

Prepare the v1 implementation for use as a stable library by locking the public contract, validating packaging, and removing implementation artifacts that are not part of the supported surface.

### Context

The spec says each stable language version has a stable AST contract tied to the library version. Before considering v1 complete, the package must be installable and its public surface must match the documented contract.

### Outcomes

After this phase, the package can be built or installed locally, public imports work from an installed environment, all quality gates pass, and the implementation has a clear v1 contract boundary.

### Tasks

| ID | Depends On | Description |
|---|---|---|
| `T00064` | `T00063` | Verify packaging metadata, package discovery, README references, and source distribution/wheel build behavior for the `src/sacagawea` package. |
| `T00065` | `T00064` | Add or update public export tests so every stable API name from `.docs/features/.wip/00001-filter-language/assets/public-api.md` is importable from the package root, and `__all__` advertises only documented stable names. |
| `T00066` | `T00065` | Run the test suite from a clean installed package context to catch missing package data, import-path assumptions, AST contract drift, or docs/metadata issues. |
| `T00067` | `T00066` | Run a documented anti-behavior verification pass: static scans for `eval`, `exec`, evaluation-time dynamic imports, object attribute access paths, SQL/ORM imports, and non-extension callable dispatch; executable tests for unsupported literal rejection, no input mutation, original-object result identity, and safety-limit isolation after a public call begins. Record the commands, reviewed files, and test names as release evidence. |
| `T00068` | `T00067` | Record final release notes or WIP completion notes in the feature docs, including any intentional v1 limitations and future extension points. |
| `T00069` | `T00068` | Run final `pytest`, `ruff`, and `ty` gates; fix release-blocking failures. |

### Acceptance criteria

* The package can be installed or built using the repository's `uv` workflow.
* Public package imports match the v1 documented API.
* Installed-package tests verify the exported `AST` root, `SourceSpan`, and expression node variants match `.docs/features/.wip/00001-filter-language/assets/ast-contract.md`, including field names, tuple fields, immutability, and span semantics.
* Quality gates pass in both source-tree and installed-package contexts.
* The final anti-behavior evidence lists the static scan patterns, reviewed evaluator/parser modules, and executable tests proving no Python execution primitives, object attribute access, mutation, SQL/ORM translation, unsupported literal support, or non-extension callable invocation in the v1 evaluator.
* Feature documentation records the completed v1 behavior and known non-goals.

---

## Changelog Entry 00001: 2026-05-10

Initial execution plan created from `.docs/features/.wip/00001-filter-language/spec.md`.

### What was changed

* Added a self-contained vertical-slice execution plan for the v1 filter-language library.
* Sequenced implementation from package skeleton through parser, scalar runtime, logical functions, temporal values, `.query(...)` aliases, configuration extensions, assertion coverage, documentation, and release readiness.
* Captured the stable artifacts, constraints, acceptance criteria, and task dependencies needed for later AI agents or engineers to implement the feature without rereading the entire planning conversation.

## Changelog Entry 00002: 2026-05-10

Revised the plan after review to settle implementation assets before slicing and keep one file per asset.

### What was changed

* Registered dedicated asset files for public API, parser strategy, AST, safety limits, `FilterConfig`, runtime extensions, runtime values, and structured errors.
* Settled the parser strategy as a standard-library handwritten lexer and recursive-descent parser for v1.
* Moved `FilterConfig`, regex evaluator, custom global function, safety-limit, AST, and error contracts out of later implementation tasks and into registered assets.
* Moved regex and global function extension behavior into the scalar/logical runtime phase so configured validation is not hard-coded to defaults first.
* Split chained dictionary paths from temporal behavior so nested path traversal can be implemented and verified before temporal parsing and timezone comparison rules.
* Converted the late error-completion phase into documentation and assertion-matrix work; each behavior phase now owns the structured errors it introduces.

## Changelog Entry 00003: 2026-05-10

Revised the plan after a second review to close remaining asset and slicing gaps.

### What was changed

* Added one-file assets for packaging, grammar, runtime methods, temporal formats, and assertion coverage.
* Replaced remaining `spec.md` artifact anchors with dedicated asset files.
* Settled package discovery through the packaging asset.
* Settled public package-root exports and dedicated exception-class strategy.
* Registered a structured extension-failure wrapper in the plan assets for unexpected custom extension failures.
* Restricted method-call AST receivers to path expressions for v1.
* Split scalar methods from configured logical functions.
* Split list query baseline behavior from nested alias scope, collision, and query nesting rules.
* Removed documented exclusions from assertion-matrix planning; all spec assertions must be covered or covered by contract.

## Changelog Entry 00004: 2026-05-10

Revised the plan after a full artifact review to remove remaining hidden contract decisions.

### What was changed

* Split `limit-exceeded` into parse-time and runtime public subclasses while preserving a shared `LimitExceededError` catch-all and stable code value.
* Settled public default construction for `FilterConfig` and `SafetyLimits`.
* Clarified custom global function return values as raw Python values classified through the runtime value model.
* Moved `.query(...)` alias, collision, resolution, and failure semantics into the runtime-method asset.
* Added dictionary `isNull()` and explicit temporal component method contracts.
* Made grammar expressions and assertion coverage self-contained in their asset files.
* Fixed malformed Markdown table cells in `FilterConfig`.
* Removed a Phase 00003 predicate-enforcement dependency leak for future logical/query argument behavior.

## Changelog Entry 00005: 2026-05-10

Reviewed the execution plan against every registered asset file and tightened plan gates where asset contracts were only implied.

### What was changed

* Added explicit Phase 00001 packaging, public export, default construction, immutable data-object, and exception hierarchy acceptance gates.
* Strengthened parser tasks and acceptance criteria for path-only method receivers, exact source spans, mutable-collection bans, parse-limit subclassing, grammar edge cases, and the no-parser-dependency rule.
* Added runtime value classification coverage for the full mapping order, reachability-only failures, root path context, and non-dictionary list item validation.
* Clarified configured extension invocation as the only callable escape hatch and aligned custom regex evaluator failures with the structured extension wrapper described by the plan assets.
* Moved baseline `.query(...)` nesting-limit enforcement into the first `.query(...)` phase and added predicate-body validation plus first-match short-circuit coverage.
* Tightened temporal implementation coverage for exact accepted formats, `datetime.datetime` dispatch, offset suffixes, rollover behavior, naive temporal strings, and temporal component method limits.
* Made assertion-matrix maintenance incremental across phases and added final gates forbidding unmapped assertions or documented exclusions.

## Changelog Entry 00006: 2026-05-10

Final review pass to align the execution plan with the closed spec and remove remaining execution risks.

### What was changed

* Reordered the middle runtime phases so list query behavior and nested query scope rules land before temporal behavior, matching the primary end-to-end demo's real dependencies.
* Moved custom global function alias-scope wiring into the `.query(...)` phases, where alias scopes actually exist.
* Removed plan language that implied new spec error identities for invalid configuration or runtime extension failures.
* Made Phase 00010 a coverage-publication and documentation phase instead of a late catch-all implementation phase.
* Replaced the final anti-behavior review task with concrete static-scan and executable-test evidence requirements.
* Kept `spec.md` closed; contract changes must go through plan assets only and must not revise the closed spec.
