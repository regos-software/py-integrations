# Scenario Engine

`scenario/engine.py` is the domain-neutral JSON workflow runner.

It executes declarative workflow primitives:

- template resolution;
- condition DSL;
- direct calls to injected tools;
- bounded foreach loops;
- generic operations such as `lookup_one`, `build_payload`,
  `build_payload_bundle`, `group_rows`, `poll_tool_until`, `download_url` and
  `parse_structured_file`.

It must not contain:

- hardcoded provider API method names;
- domain-specific lookup operations;
- domain-specific payload builders;
- business scenario branches.

Business behavior belongs in profile data: tool profiles, scenario profiles,
runtime rules, render rules and follow-up suggestions. Provider transport lives
under `providers/`, and tool execution policy lives under `tool_runtime/`.
