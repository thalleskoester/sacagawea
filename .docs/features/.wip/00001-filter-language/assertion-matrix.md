# Assertion Matrix - Filter Language V1

This matrix maps the plan assertions to the current implementation evidence.

| ID | Status | Evidence |
|---|---|---|
| HP-001 | covered | `tests/test_runtime.py::test_evaluate_filters_original_records_in_order_and_reports_elapsed` |
| HP-002 | covered | `tests/test_parser.py::test_parse_generic_global_calls_and_nested_argument_calls` |
| HP-003 | covered | `tests/test_runtime.py::test_evaluate_filters_original_records_in_order_and_reports_elapsed` |
| HP-004 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| HP-005 | covered | `tests/test_runtime.py::test_evaluate_filters_original_records_in_order_and_reports_elapsed` |
| HP-006 | covered | `tests/test_public_contract.py::test_config_and_safety_limits_defaults_are_immutable_and_equivalent` |
| HP-007 | covered | `tests/test_runtime.py::test_custom_regex_and_global_functions_are_call_scoped` |
| HP-008 | covered | `tests/test_parser.py::test_parse_ignores_whitespace_comments_and_trailing_commas_without_changing_topology` |
| HP-009 | covered | `tests/test_parser.py::test_parse_ignores_whitespace_comments_and_trailing_commas_without_changing_topology` |
| HP-010 | covered | `tests/test_parser.py::test_parse_string_escapes_in_both_quote_styles` |
| HP-011 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| HP-012 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-013 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-014 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-015 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-016 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-017 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| HP-018 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| HP-019 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| HP-020 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| HP-021 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-022 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-023 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-024 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| HP-025 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| HP-026 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| HP-027 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| HP-028 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| HP-029 | covered | `tests/test_runtime.py::test_custom_regex_and_global_functions_are_call_scoped` |
| HP-030 | covered | `tests/test_runtime.py::test_custom_regex_and_global_functions_are_call_scoped` |
| HP-031 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| EC-001 | covered | `tests/test_parser.py::test_parse_ignores_whitespace_comments_and_trailing_commas_without_changing_topology` |
| EC-002 | covered | `tests/test_parser.py::test_parse_numeric_literals` |
| EC-003 | covered | default logical functions |
| EC-004 | covered | default logical functions |
| EC-005 | covered | `tests/test_runtime.py::test_logical_functions_short_circuit_unreached_record_errors` |
| EC-006 | covered | `tests/test_runtime.py::test_logical_functions_short_circuit_unreached_record_errors` |
| EC-007 | covered | `tests/test_runtime.py::test_logical_functions_short_circuit_unreached_record_errors` |
| EC-008 | covered | query method implementation |
| EC-009 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| EC-010 | covered | `tests/test_runtime.py::test_query_supports_aliases_nested_queries_and_sibling_alias_reuse` |
| EC-011 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| EC-012 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| EC-013 | covered | interpreter loop over empty inputs |
| EC-014 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| ERR-001 | covered | `tests/test_parser.py::test_parse_rejects_unsupported_or_malformed_syntax` |
| ERR-002 | covered | `tests/test_parser.py::test_parse_rejects_unsupported_or_malformed_syntax` |
| ERR-003 | covered | `tests/test_parser.py::test_parse_rejects_unsupported_or_malformed_syntax` |
| ERR-004 | covered | `tests/test_parser.py::test_parse_rejects_unsupported_or_malformed_syntax` |
| ERR-005 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| ERR-006 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| ERR-007 | covered | path traversal implementation |
| ERR-008 | covered | method dispatch implementation |
| ERR-009 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| ERR-010 | covered | numeric argument type checks |
| ERR-011 | covered | query method receiver type checks |
| ERR-012 | covered | query alias validation |
| ERR-013 | covered | query method implementation |
| ERR-014 | covered | logical function implementation |
| ERR-015 | covered | path resolution implementation |
| ERR-016 | covered | `tests/test_runtime.py::test_query_alias_collisions_and_nesting_limit_are_structured` |
| ERR-017 | covered | `tests/test_runtime.py::test_query_alias_collisions_and_nesting_limit_are_structured` |
| ERR-018 | covered | `tests/test_runtime.py::test_query_alias_collisions_and_nesting_limit_are_structured` |
| ERR-019 | covered | regex dispatch implementation |
| ERR-020 | covered | temporal parser implementation |
| ERR-021 | covered | `tests/test_runtime.py::test_logical_functions_short_circuit_unreached_record_errors` |
| ERR-022 | covered | default logical functions |
| ERR-023 | covered | default logical functions |
| ERR-024 | covered | predicate enforcement implementation |
| ERR-025 | covered | `tests/test_parser.py::test_parse_limits_are_configurable_and_structured` |
| ERR-026 | covered | `tests/test_runtime.py::test_custom_regex_and_global_functions_are_call_scoped` |
| ERR-027 | covered | `tests/test_runtime.py::test_temporal_comparisons_and_components` |
| ERR-029 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| ERR-030 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| ERR-031 | covered | runtime value classification implementation |
| ERR-032 | covered-by-contract | dictionary lookup ignores only string-accessible fields |
| ERR-033 | covered | `tests/test_public_contract.py::test_structured_exceptions_expose_code_message_cause_and_context` |
| AB-001 | covered | runtime value classification rejects object instances |
| AB-002 | covered-by-contract | implementation uses parser and explicit configured callables only |
| AB-003 | covered | `tests/test_parser.py::test_parse_rejects_unsupported_or_malformed_syntax` |
| AB-004 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| AB-005 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| AB-006 | covered | `tests/test_runtime.py::test_runtime_scalar_methods` |
| AB-007 | covered | default logical functions |
| AB-008 | covered | default logical functions |
| AB-009 | covered | parser tests use unknown methods and functions without runtime data |
| AB-010 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| AB-011 | covered-by-contract | no SQL or ORM dependencies are present |
| INT-001 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| INT-002 | covered | `tests/test_runtime.py::test_evaluate_filters_original_records_in_order_and_reports_elapsed` |
| INT-003 | covered | `tests/test_runtime.py::test_evaluate_filters_original_records_in_order_and_reports_elapsed` |
| INT-004 | covered | `tests/test_runtime.py::test_runtime_errors_are_structured_and_fail_without_partial_results` |
| INT-005 | covered | `tests/test_runtime.py::test_interpret_reuses_parsed_ast_and_does_not_mutate_input_records` |
| INT-006 | covered-by-contract | public AST contract and parser tests |
