The function is O(events) with a set lookup. 100000 events should be fast... but the "second run" took over 20s. Why? Because the function is called many times? No, each case is timed once per measurement but repeated. Actually the issue: the timing harness runs each input many times. With 100k events, one call is maybe 10ms. Running many times... but they say "took over 20s" on second run.

Wait, actually the real problem: the events list is huge and the harness renders arguments before and after each call to check mutation. 100000 events with tuples -> rendering takes huge time. The rule says keep each input's data under about 1,000,000 values. 100000 tuples of 3 = 300000 values, under 1M. But rendering may be slow.

Actually more likely: reduce sizes drastically. Let's use ~5000 events instead of 100000.

Also the harness likely deep-copies / compares args. Let me just reduce to manageable sizes. Let's target one call ~1-50ms.

The function iterates over all events. 5000 events is trivial (~1ms). Let's use maybe 20000 events.

Actually the "took over 20s" is suspicious. Maybe the issue is that remaining is a set and the function checks `actor in remaining`. That's fine.

Hmm, maybe the problem: the harness renders args before/after. Rendering a list of 100k tuples repeatedly could be slow. Let's cut to 10000 events.

Let me set sizes to 10000 events, actors pools smaller.

Let me rewrite with 10000 events each.