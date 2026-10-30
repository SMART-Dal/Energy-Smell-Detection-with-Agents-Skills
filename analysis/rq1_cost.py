"""RQ1, what each run cost: money, tokens, time, tool calls and subagents.

Claude Code reports its own accounting in the transcript (transcript.jsonl), on
every line of type "result". These numbers grow during a session, so the LAST
result line holds the whole run. We copy them as Claude Code gives them and
never add result lines of one run together.

From the last result line:
  cost_usd            total_cost_usd: Claude Code's price of the session, at list
                      prices, subagents included
  output_tokens       modelUsage -> outputTokens (thinking included)
  thinking_tokens     modelUsage -> thinkingTokens (the part of the output spent thinking)
  input_tokens        modelUsage -> inputTokens (not read from the prompt cache)
  cache_read_tokens   modelUsage -> cacheReadInputTokens
  cache_write_tokens  modelUsage -> cacheCreationInputTokens
  api_minutes         duration_api_ms: time spent waiting for the model, added up
                      over all requests, subagents included (so it can be longer
                      than the session when subagents run at the same time)
  subagents           subagent_stats -> spawned: subagents started in the session

From the rest of the run:
  agent_minutes       run.json agent_seconds: how long the agent's session lasted
  main_tool_calls     tool calls of the main agent (transcript, no parent_tool_use_id)
  subagent_tool_calls tool calls made inside subagents (with a parent_tool_use_id)
  main_wait_calls     main-agent calls that only wait: the Monitor tool, or a Bash
                      command that starts with "sleep"
  confirmed_repairs   repairs with our verdict confirmed or partial (review/results.jsonl)

Writes to analysis/output/rq1/:
  cost_per_run.csv            one row per run
  cost_per_skill_model.csv    the three repositories added up, per skill and model,
                              with the cost per confirmed repair
  cost_per_model.csv          the same per model, all skills and repositories
  cost_summary.json           totals over the 18 runs

Run:  python3 analysis/rq1_cost.py
"""

from common import (MODEL_NAMES, MODELS, OUTPUT_DIR, SAVES, SKILL_NAMES, SKILLS, all_runs,
                    percent, read_json, read_jsonl, run_folder, write_csv, write_json)

OUT = OUTPUT_DIR / "rq1"   # where this script writes

# The numbers that are added up over runs in the per-skill and per-model tables
ADDED = ["cost_usd", "agent_minutes", "api_minutes", "input_tokens", "output_tokens",
         "thinking_tokens", "cache_read_tokens", "cache_write_tokens", "main_tool_calls",
         "subagent_tool_calls", "main_wait_calls", "subagents", "confirmed_repairs"]


def cost_of(repo, skill, model):
    """The accounting of one run, as a dictionary."""
    folder = run_folder(repo, skill, model)
    events = read_jsonl(folder / "transcript.jsonl")

    # The last result line holds the totals of the whole session
    last = None
    for event in events:
        if event.get("type") == "result":
            last = event
    usage = list(last["modelUsage"].values())           # one entry: each run used one model
    if len(usage) != 1:
        raise SystemExit(f"{folder}: expected one model in modelUsage, found {len(usage)}")
    usage = usage[0]

    # Tool calls: count each tool_use id once, split by who made the call
    main_calls = set()
    subagent_calls = set()
    wait_calls = set()
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event["message"]["content"]:
            if block.get("type") != "tool_use":
                continue
            if event.get("parent_tool_use_id"):         # made inside a subagent
                subagent_calls.add(block["id"])
            else:                                       # made by the main agent
                main_calls.add(block["id"])
                command = (block.get("input") or {}).get("command") or ""
                if block["name"] == "Monitor" or command.strip().startswith("sleep"):
                    wait_calls.add(block["id"])

    confirmed = 0
    for repair in read_jsonl(folder / "review" / "results.jsonl"):
        if repair["status"] in SAVES:
            confirmed = confirmed + 1

    stats = last.get("subagent_stats") or {}            # missing when no subagent was started
    row = {}
    row["repo"] = repo
    row["skill"] = SKILL_NAMES[skill]
    row["model"] = MODEL_NAMES[model]
    row["cost_usd"] = round(last["total_cost_usd"], 2)
    row["agent_minutes"] = round(read_json(folder / "run.json")["agent_seconds"] / 60, 1)
    row["api_minutes"] = round(last["duration_api_ms"] / 60000, 1)
    row["input_tokens"] = usage["inputTokens"]
    row["output_tokens"] = usage["outputTokens"]
    row["thinking_tokens"] = usage["thinkingTokens"]
    row["pct_output_thinking"] = percent(usage["thinkingTokens"], usage["outputTokens"])
    row["cache_read_tokens"] = usage["cacheReadInputTokens"]
    row["cache_write_tokens"] = usage["cacheCreationInputTokens"]
    row["main_tool_calls"] = len(main_calls)
    row["subagent_tool_calls"] = len(subagent_calls)
    row["main_wait_calls"] = len(wait_calls)
    row["subagents"] = stats.get("spawned", 0)
    row["subagent_types"] = " ".join(f"{name}:{count}" for name, count in (stats.get("by_type") or {}).items())
    row["confirmed_repairs"] = confirmed
    return row


def added_up(rows, labels):
    """The ADDED numbers summed over `rows`, plus the shares and ratios built from the sums."""
    total = dict(labels)
    for name in ADDED:
        value = 0
        for row in rows:
            value = value + row[name]
        total[name] = round(value, 2) if isinstance(value, float) else value
    total["pct_output_thinking"] = percent(total["thinking_tokens"], total["output_tokens"])
    total["output_tokens_thousands"] = round(total["output_tokens"] / 1000)        # for the table
    total["cache_read_tokens_millions"] = round(total["cache_read_tokens"] / 10**6, 1)
    if total["confirmed_repairs"]:
        total["usd_per_confirmed_repair"] = round(total["cost_usd"] / total["confirmed_repairs"], 2)
    else:
        total["usd_per_confirmed_repair"] = None
    return total


def main():
    per_run = []
    for repo, skill, model in all_runs():
        per_run.append(cost_of(repo, skill, model))
    write_csv(per_run, OUT / "cost_per_run.csv")

    per_skill_model = []
    for model in MODELS:
        for skill in SKILLS:
            rows = []
            for row in per_run:
                if row["skill"] == SKILL_NAMES[skill] and row["model"] == MODEL_NAMES[model]:
                    rows.append(row)
            per_skill_model.append(added_up(rows, {"model": MODEL_NAMES[model],
                                                   "skill": SKILL_NAMES[skill]}))
    write_csv(per_skill_model, OUT / "cost_per_skill_model.csv")

    per_model = []
    for model in MODELS:
        rows = []
        for row in per_run:
            if row["model"] == MODEL_NAMES[model]:
                rows.append(row)
        per_model.append(added_up(rows, {"model": MODEL_NAMES[model]}))
    write_csv(per_model, OUT / "cost_per_model.csv")

    write_json(added_up(per_run, {"runs": len(per_run)}), OUT / "cost_summary.json")
    print("wrote", OUT / "cost_*")


if __name__ == "__main__":
    main()
