#!/usr/bin/env python3
"""Stop an agent run at its dollar budget without telling the agent there is one.

    python cost_guard.py --pid PID --model MODEL --budget USD  <&5 >&6

`claude --max-budget-usd` enforces a budget by putting "USD budget: $x/$y;
$z remaining" into the model's context on every turn, and Sonnet's runs of
Oct 20 stopped after three units "working to a tight spending budget" of which
they had spent 2%. So run_all.sh passes no budget to claude; this process reads
the session's stream-json transcript as it is written (standard input, opened
before the harness locks ~/energy-exp), estimates what has been spent, and
interrupts the agent when the estimate reaches the budget -- as the session
timeout does, with SIGINT to `timeout`, which passes it on.

The estimate is from the usage on each assistant message, at list prices.
Input-side tokens are exact; output tokens are not in the stream until the
message ends, so they are taken from the text and tool calls themselves and
from the thinking-token events. `--check FILE...` compares the estimate with
the cost each finished transcript reports.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

PRICES = {  # USD per million tokens: input, output, cache write (5 min), cache read
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
}
LONG_PROMPT = {"claude-haiku-5-5": (100_000, 5.0)}
"""Haiku charges five times as much for a request whose prompt passes 100K tokens."""
CHARS_PER_TOKEN = 3.5
POLL_S = 10.0
GRACE_S = 120.0
"""After SIGINT, how long the agent has to stop before it is killed, as `timeout -k 2m`."""


class Estimate:
    def __init__(self, model: str):
        self.prices = PRICES.get(model, max(PRICES.values()))
        self.long_prompt = LONG_PROMPT.get(model)
        self.inputs: dict[str, tuple[int, int, int]] = {}
        self.chars: dict[str, int] = {}
        self.reported: dict[str, int] = {}
        self.thinking = 0
        self.reported_total: float | None = None

    def add(self, event: dict) -> None:
        kind = event.get("type")
        if kind == "assistant":
            message = event.get("message") or {}
            mid = message.get("id") or str(len(self.inputs))
            usage = message.get("usage") or {}
            self.inputs[mid] = (usage.get("input_tokens") or 0,
                                usage.get("cache_creation_input_tokens") or 0,
                                usage.get("cache_read_input_tokens") or 0)
            self.reported[mid] = max(self.reported.get(mid, 0), usage.get("output_tokens") or 0)
            for block in message.get("content") or []:
                body = block.get("text") or block.get("thinking") or json.dumps(block.get("input") or "")
                self.chars[mid] = self.chars.get(mid, 0) + len(body)
        elif kind == "system" and event.get("subtype") == "thinking_tokens":
            self.thinking += event.get("estimated_tokens_delta") or 0
        elif kind == "result":
            self.reported_total = event.get("total_cost_usd")

    def _rate(self, prompt: int) -> float:
        limit, factor = self.long_prompt or (0, 1.0)
        return factor if limit and prompt > limit else 1.0

    def usd(self) -> float:
        p_in, p_out, p_write, p_read = self.prices
        spent = 0.0
        for mid, (i, w, r) in self.inputs.items():
            rate = self._rate(i + w + r)
            output = max(self.reported.get(mid, 0), self.chars.get(mid, 0) / CHARS_PER_TOKEN)
            spent += rate * (i * p_in + w * p_write + r * p_read + output * p_out)
        # Thinking is reported for the session, not per message: at the base rate.
        return (spent + self.thinking * p_out) / 1e6


def _children(pid: int) -> list[int]:
    try:
        return [int(c) for c in Path(f"/proc/{pid}/task/{pid}/children").read_text().split()]
    except (OSError, ValueError):
        return []


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop(pid: int, log) -> None:
    """SIGINT to the agent, as its timeout would send; SIGKILL if it is still there after GRACE_S."""
    try:
        os.kill(pid, signal.SIGINT)
    except OSError:
        return
    deadline = time.monotonic() + GRACE_S
    while time.monotonic() < deadline and _alive(pid):
        time.sleep(2)
    if _alive(pid):
        for child in _children(pid):
            try:
                os.kill(child, signal.SIGKILL)
            except OSError:
                pass
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        log({"killed_after_s": GRACE_S})


def guard(pid: int, model: str, budget: float) -> int:
    def log(row: dict) -> None:
        print(json.dumps({"t": round(time.time(), 1), **row}), flush=True)

    estimate, pending = Estimate(model), ""
    log({"watching": pid, "model": model, "budget_usd": budget})
    while _alive(pid):
        chunk = sys.stdin.read()
        if chunk:
            pending += chunk
            *lines, pending = pending.split("\n")
            for line in lines:
                try:
                    estimate.add(json.loads(line))
                except ValueError:
                    pass
        if estimate.usd() >= budget:
            log({"stopped": True, "estimated_usd": round(estimate.usd(), 4)})
            _stop(pid, log)
            return 0
        time.sleep(POLL_S)
    log({"agent_ended": True, "estimated_usd": round(estimate.usd(), 4)})
    return 0


def check(paths: list[str], model: str | None) -> int:
    for path in paths:
        events = [json.loads(l) for l in open(path) if l.strip()]
        name = model or next((e.get("model") for e in events if e.get("type") == "system"
                              and e.get("subtype") == "init"), "")
        estimate = Estimate(name)
        for event in events:
            estimate.add(event)
        print(f"{path}: {name} estimated ${estimate.usd():.4f}, reported ${estimate.reported_total}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pid", type=int, help="the `timeout` process running the agent")
    parser.add_argument("--model")
    parser.add_argument("--budget", type=float)
    parser.add_argument("--check", nargs="+", metavar="TRANSCRIPT")
    args = parser.parse_args()
    if args.check:
        return check(args.check, args.model)
    return guard(args.pid, args.model, args.budget)


if __name__ == "__main__":
    sys.exit(main())
