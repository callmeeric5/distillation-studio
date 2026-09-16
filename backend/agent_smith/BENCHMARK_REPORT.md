# Model Benchmark Report

## Setup

Five models were compared through OpenAI-compatible APIs. GPT-4.1 Nano, DeepSeek,
Gemini, and MiniMax used OpenRouter; Qwen used Groq. Every model ran the same three
SWE-bench tasks:

- `django__django-11066`, a database-routing bug in Django content types;
- `sympy__sympy-14711`, an operator edge case in the vector module; and
- `sympy__sympy-18189`, a symbol-ordering bug in the Diophantine solver.

This set covers two repositories and three different kinds of behavior while
remaining small enough to inspect each trace manually. The 15 backing solution JSON
files are stored under `runs/<model>/`. Every saved run has `success: true`, and
these final results were retained after successful task validation.

## Results

| Model | Task | Pass | Iterations | Input tokens | Output tokens | Time (s) |
|---|---|:---:|---:|---:|---:|---:|
| GPT-4.1 Nano | django-11066 | Pass | 8 | 48,006 | 553 | 29.89 |
| GPT-4.1 Nano | sympy-14711 | Pass | 6 | 11,067 | 323 | 21.70 |
| GPT-4.1 Nano | sympy-18189 | Pass | 8 | 19,990 | 463 | 74.59 |
| DeepSeek V4 Flash | django-11066 | Pass | 6 | 35,551 | 661 | 37.76 |
| DeepSeek V4 Flash | sympy-14711 | Pass | 19 | 146,703 | 4,137 | 189.00 |
| DeepSeek V4 Flash | sympy-18189 | Pass | 6 | 34,815 | 745 | 86.08 |
| Gemini 3.1 Flash Lite | django-11066 | Pass | 13 | 87,711 | 2,213 | 43.47 |
| Gemini 3.1 Flash Lite | sympy-14711 | Pass | 10 | 67,565 | 708 | 38.20 |
| Gemini 3.1 Flash Lite | sympy-18189 | Pass | 16 | 81,701 | 1,155 | 63.14 |
| MiniMax M2.7 | django-11066 | Pass | 11 | 37,070 | 838 | 44.88 |
| MiniMax M2.7 | sympy-14711 | Pass | 13 | 40,172 | 1,924 | 46.04 |
| MiniMax M2.7 | sympy-18189 | Pass | 7 | 22,944 | 700 | 79.34 |
| Qwen 3.6 27B | django-11066 | Pass | 8 | 25,282 | 878 | 158.96 |
| Qwen 3.6 27B | sympy-14711 | Pass | 13 | 43,314 | 2,056 | 314.11 |
| Qwen 3.6 27B | sympy-18189 | Pass | 14 | 51,734 | 2,293 | 385.34 |

All runs stayed below the SWE-bench limits of 30 iterations, 300,000 input tokens,
10,000 output tokens, and 900 seconds.

## Provider reliability

Mean response time is the sum of recorded step request times divided by all HTTP
attempts, including retries. Availability is successful model responses divided by
all HTTP attempts. It measures API reliability during this small experiment, not
general provider uptime.

| Model | Provider | Requests | Retries | Mean response/request | Availability |
|---|---|---:|---:|---:|---:|
| GPT-4.1 Nano | OpenRouter | 22 | 0 | 1.40 s | 100.0% |
| DeepSeek V4 Flash | OpenRouter | 32 | 1 | 7.72 s | 96.9% |
| Gemini 3.1 Flash Lite | OpenRouter | 41 | 2 | 1.18 s | 95.1% |
| MiniMax M2.7 | OpenRouter | 31 | 0 | 2.40 s | 100.0% |
| Qwen 3.6 27B | Groq | 62 | 27 | 12.93 s | 56.5% |

OpenRouter was available throughout the final runs. Its four models needed only
three retries across 126 requests. Groq returned frequent rate-limit responses for
Qwen: 27 extra attempts across 35 successful steps. Those waits explain most of
Qwen's 858.41 seconds of aggregate wall-clock time.

## Intermediary metrics

Two trace-level metrics were inspected manually:

1. **First target-file access** is the first step that reads or edits a production
   file present in the final patch.
2. **Submission gap** counts iterations from the first passing post-edit test to the
   successful `final_answer` step. A value of 2 is the normal path when the agent
   runs tests, obtains the patch, and submits it in separate actions.

| Model | Task | First target-file access | First passing test | Final answer | Submission gap |
|---|---|---:|---:|---:|---:|
| GPT-4.1 Nano | django-11066 | 5 | 6 | 8 | 2 |
| GPT-4.1 Nano | sympy-14711 | 2 | 4 | 6 | 2 |
| GPT-4.1 Nano | sympy-18189 | 2 | 4 | 8 | 4 |
| DeepSeek V4 Flash | django-11066 | 1 | 4 | 6 | 2 |
| DeepSeek V4 Flash | sympy-14711 | 2 | 17 | 19 | 2 |
| DeepSeek V4 Flash | sympy-18189 | 1 | 4 | 6 | 2 |
| Gemini 3.1 Flash Lite | django-11066 | 2 | 9 | 13 | 4 |
| Gemini 3.1 Flash Lite | sympy-14711 | 2 | 8 | 10 | 2 |
| Gemini 3.1 Flash Lite | sympy-18189 | 2 | 14 | 16 | 2 |
| MiniMax M2.7 | django-11066 | 2 | 8 | 11 | 3 |
| MiniMax M2.7 | sympy-14711 | 1 | 7 | 13 | 6 |
| MiniMax M2.7 | sympy-18189 | 1 | 4 | 7 | 3 |
| Qwen 3.6 27B | django-11066 | 3 | 6 | 8 | 2 |
| Qwen 3.6 27B | sympy-14711 | 2 | 8 | 13 | 5 |
| Qwen 3.6 27B | sympy-18189 | 2 | 12 | 14 | 2 |

DeepSeek's 17 steps before a passing test on `sympy-14711` show inefficient source
exploration. MiniMax and Qwen found a working `sympy-14711` change earlier, but then
spent six and five iterations respectively on extra checks and submission. GPT-4.1
Nano most consistently followed the short test -> patch -> submit sequence.

## Ablation study

During development, Qwen 3.6 27B on `sympy__sympy-14711` was run with the original
prompt and permissive loop. It repeated reads and searches until the configured
20-iteration limit and failed without `final_answer`. The loop was then changed to
return explicit feedback for repeated actions and the prompt was changed to require
the test -> `get_patch()` -> `final_answer(get_patch())` sequence. On the same task
and model, the final saved run passed in 13 iterations.

| Version | Model and task | Result | Iterations |
|---|---|:---:|---:|
| Before repetition/submission guidance | Qwen 3.6 27B, sympy-14711 | Fail | 20 (limit) |
| After repetition/submission guidance | Qwen 3.6 27B, sympy-14711 | Pass | 13 |

The old failed trace was removed during workspace cleanup, so its token and latency
values are unavailable and are deliberately not estimated. The comparison supports
the narrow conclusion that explicit progress and submission feedback prevented this
observed loop; it does not isolate model quality or provider latency.

## Conclusions

GPT-4.1 Nano is the best default for this measured pipeline. It solved all three
tasks in 22 total iterations, used 79,063 input tokens, needed no retries, and had
the shortest aggregate wall-clock time at 126.19 seconds.

MiniMax is the second practical choice when GPT-4.1 Nano is unavailable. It also had
no retries and used 100,186 input tokens, though its submission discipline was less
consistent. Gemini was fast at the API level but used 39 iterations and 236,977
input tokens. DeepSeek solved all tasks but its `sympy-14711` exploration raised its
token cost to 217,069 input tokens. Qwen can solve the tasks, but this Groq route can
be disregarded for the final pipeline because its 27 retries and 56.5% observed
availability made it much slower than the alternatives.
