*This activity has been created as part of the 42 curriculum by ziwang.*

# Agent Smith

## Description

Agent Smith is a small code-agent framework for MBPP and SWE-bench. The model does
not directly control files or Docker. It writes a short Python action, the sandbox
executes that action, and the real result is returned to the model. This creates the
required Thought -> Code -> Observation loop.

The same loop works with different OpenAI-compatible providers. The LLM client
tracks tokens, requests, retries, and latency, while MCP supplies the tools that are
available for the current benchmark.

## Instructions

The project requires Python 3.10, [uv](https://docs.astral.sh/uv/), and Docker.

```sh
uv sync
cp .env.example .env
```

Put free-quota API keys in `.env`. A comma-separated list enables key rotation:

```dotenv
OPENROUTER_API_KEYS=first_key,second_key
GROQ_API_KEYS=first_key,second_key
```

Run an MBPP task:

```sh
uv run python -m agent_mbpp \
  --task-file task.json \
  --output solution.json \
  --model-name provider/model \
  --provider-url https://provider.example/v1
```

Run a SWE-bench task in the same way:

```sh
uv run python -m agent_swebench \
  --task-file task.json \
  --output solution.json \
  --model-name provider/model \
  --provider-url https://provider.example/v1
```

Run the provided moulinette from its own directory. If it is stored inside this
repository, the student path is `..`:

```sh
cd moulinette
uv sync
./quickstart.sh mbpp \
  --student-path .. \
  --model-name "openai/gpt-4.1-nano" \
  --provider-url "https://openrouter.ai/api/v1"
```

To call `run-agent` directly, return to the project root first. The command run
by `run-agent` inherits the current directory, so starting it inside
`moulinette/` prevents Python from finding `agent_mbpp`:

```sh
cd ..
uv run --project moulinette moulinette_eval run-agent 120 \
  "uv run python -m agent_mbpp --task-file task.json --output solution.json"
uv run --project moulinette moulinette_eval validate mbpp task.json solution.json
```

Make sure `task.json` is an MBPP task. A SWE-bench task contains fields such as
`instance_id` and must be passed to `agent_swebench` instead.

Use a plain URL in shell commands. Markdown link syntax such as
`[https://...](https://...)` is not a valid provider URL.

The model and endpoint can instead be set in `config/models.json`. To choose a
nonstandard key variable, add `--api-key-env VARIABLE_NAME`.

Start the interactive sandbox with no MCP server:

```sh
uv run sandbox
```

Connect one of this project's MCP servers:

```sh
uv run sandbox --mcp-stdio "uv run python mcp_tools_mbpp.py"
uv run sandbox --mcp-stdio "uv run python mcp_tools_swebench.py --task-file task.json"
uv run sandbox --mcp-server http://127.0.0.1:8000/mcp
```

Type Python at the prompt. A blank line finishes a multiline block, `exit` quits,
and `Ctrl+D` sends EOF.

## System architecture

```text
CLI
 |
 v
Agent loop <----> LLM provider
 |
 v
Sandbox controller ----> isolated Python worker
 |                              |
 |                              +-- final_answer()
 v
MCP client <----> MCP server <----> MBPP tests or SWE-bench Docker repository
```

- `agent_smith/agent/` contains the shared loop and task limits.
- `agent_smith/llm/` contains provider calls and response-format extraction.
- `agent_smith/sandbox/` contains the Docker sandbox, restricted worker, and REPL.
- `agent_smith/mcp/` discovers MCP capabilities and exposes the two project servers.
- `agent_smith/tools/` implements repository and Docker operations for SWE-bench.
- `agent_smith/models/` contains the Pydantic input, output, provider, and sandbox models.
- `agent_mbpp/` and `agent_swebench/` provide the required module CLIs.
- `config/` contains example model and sandbox settings.

The two `mcp_tools_*.py` files stay at repository root because the subject requires
that exact location. They only forward to the implementations in `src/mcp/servers/`.

## Agent loop

For each iteration, the agent:

1. checks the remaining iteration, token, and wall-clock budgets;
2. sends the task, tool manual, and recent observations to the model;
3. extracts one action from Python, XML, Hermes JSON, ReAct, DSML, or MiniMax output;
4. executes the normalized Python action in the sandbox;
5. records the raw response, executed code, observation, metrics, and retry count;
6. returns the real observation to the model; and
7. stops when the sandbox receives `final_answer(...)` or a hard limit is reached.

MBPP accepts valid Python source. SWE-bench accepts a nonempty Git patch only after
the task's evaluation script succeeds. Repeated actions and invalid submissions are
returned as explicit observations instead of silently consuming iterations.

## Sandbox design

Generated Python runs in a separate Docker container. Docker disables networking,
drops Linux capabilities, prevents privilege gain, limits processes and RAM, and is
removed after use. Inside the worker, an AST check and audit hook enforce the import
allowlist, filesystem allowlist, restricted builtins, timeout, and output limit from
`config/sandbox.json`.

MCP tools execute outside this Python sandbox. The sandbox dynamically creates
wrappers from the connected server's tool schemas, including parameter names and
types in its manual. `final_answer()` is injected by the sandbox itself and is never
an MCP tool. Variables remain available between iterations because the worker stays
alive for one task.

## Tool implementation details

The SWE-bench MCP server exposes every mandatory tool:

- `read_file`, `edit_file`, and `list_files` provide restricted repository access;
- `search_code`, `search_function_or_class_definition_in_code`, and
  `find_references` locate code and symbols;
- `run_command` and `run_python` run bounded diagnostics;
- `run_tests` executes the task's supplied evaluation script; and
- `get_patch` returns `git -c core.fileMode=false diff` while excluding test changes.

The MBPP server exposes `run_tests`, which executes candidate code and each supplied
assertion in a fresh sandbox. Both servers also expose a task resource and an MCP
prompt. Tool implementations are independent from the agent loop and can be tested
through the sandbox CLI.

## Benchmark results and analysis

The included benchmark contains 15 successful runs: five models evaluated on the
same three SWE-bench tasks. GPT-4.1 Nano used the fewest total iterations (22) and
had no retries. Qwen required 27 retries and had the highest wall-clock time, while
DeepSeek used the most input tokens. Full per-run results, provider reliability,
intermediary metrics, the ablation, and conclusions are in
[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md). The backing JSON files are in `runs/`.

To print a fresh summary without changing the saved logs:

```sh
uv run python -m src.report runs/*/*.json
```

More detailed explanations of the implementation are in [doc/PROJECT.md](doc/PROJECT.md)
and [doc/LEARNING.md](doc/LEARNING.md).

## Resources

- [Python 3.10 documentation](https://docs.python.org/3.10/)
- [Python asyncio documentation](https://docs.python.org/3.10/library/asyncio.html)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Docker security documentation](https://docs.docker.com/engine/security/)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [SWE-bench documentation](https://www.swebench.com/)

AI was used to review the initial code, explain `asyncio` and subprocesses, diagnose
provider-format and repetition failures, improve the response extractor and sandbox
feedback, organize files, and edit documentation. The implementation and benchmark
traces were checked locally; benchmark values in the report are calculated from the
saved JSON files.
