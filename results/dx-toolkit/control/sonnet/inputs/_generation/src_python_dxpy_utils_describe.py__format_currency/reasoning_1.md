The function `format_currency(value, meta, currency_locale=None)`. It uses locale module. Calls `locale.setlocale(locale.LC_ALL, currency_locale)`. This changes global locale state. Also `locale.currency(value, grouping=True)`.

The work is tiny — formatting a number. Each call is microseconds. But we need 8 cases. The function does very little work. We just need realistic inputs.

meta is `desc['currency']` which has 'dxCode', 'symbol', 'symbolPosition'. Let's look at the currency metadata structure. From format_currency_from_meta: meta['symbol'], meta['symbolPosition'], and locale_from_currency_code uses meta['dxCode'].

So meta like {'dxCode': 0, 'symbol': '$', 'symbolPosition': 'left'}.

Cases: different values, different meta, different locales. dxCode 0 -> 'en_US', 1 -> 'en_GB', other -> None -> fallback to format_currency_from_meta.

Also passing currency_locale explicitly.

Note: locale.setlocale is global and persists — but that's fine since it's deterministic. However, calling setlocale repeatedly with same locale is fine.

Potential issue: locale 'en_US' may not be available in the environment, which raises locale.Error — caught and falls back. That's fine, deterministic.

Cases should be diverse: large values, negative, zero, values with many digits, different symbol positions, different dxCodes.

Let me write 8 cases:

1. dxCode 0 (en_US locale path), value 1234.56
2. dxCode 1 (en_GB), value 9876543.21
3. dxCode unknown (e.g. 99) -> fallback meta, symbolPosition left
4. dxCode unknown -> fallback meta, symbolPosition right
5. negative value with meta
6. zero value
7. explicit currency_locale='en_US'
8. large value with many digits, e.g. 1234567890123.45

Values should be floats. Let's make them realistic: usage amounts.

The timing: each call is microseconds, so total work tiny. That's fine — we can't do much. But the instructions say one call should take roughly 1ms-200ms. This function is just fast. We'll just do our best. Maybe use large numbers to make formatting slower? Not much. It's fine.

Actually maybe we can make the work more substantial by... no, the function is fixed. Just provide inputs.

Let me keep it simple and correct.

checks(): edge inputs — None value? value None would fail in format_currency_from_meta (value < 0). But may raise, that's allowed. meta missing keys? Let's do:
- value 0, meta with dxCode 0
- value None, meta {...} -> raises
- meta empty dict, value 1.0 -> KeyError

These may raise, fine.

Let me write.

For meta, must include 'symbol', 'symbolPosition', 'dxCode'. For locale path, only dxCode matters (symbol etc not used). For fallback path, symbol and symbolPosition used.

Write code.

def _meta(dxCode, symbol, symbolPosition): return {...}

cases list with lambdas returning (value, meta) or call(value, meta, currency_locale=...).

Use `call` for keyword args.

Let's write:

```python
from dxpy.utils.describe import format_currency

def _meta(dxCode, symbol, symbolPosition):
    return {"dxCode": dxCode, "symbol": symbol, "symbolPosition": symbolPosition}

def checks():
    return [
        ("zero-en-us", lambda: (0, _meta(0, "$", "left"))),
        ("none-value", lambda: (None, _meta(0, "$", "left"))),
        ("empty-meta", lambda: (1.0, {})),
    ]

def cases():
    return [
        ("en-us-small", lambda: (1234.56, _meta(0, "$", "left"))),
        ("en-gb-large", lambda: (9876543.21, _meta(1, "£", "left"))),
        ("unknown-code-left", lambda: (42.0, _meta(99, "€", "left"))),
        ("unknown-code-right", lambda: (123456.789, _meta(7, "kr", "right"))),
        ("negative", lambda: (-98765.43, _meta(99, "$", "left"))),
        ("zero-usage", lambda: (0.0, _meta(0, "$", "left"))),
        ("explicit-locale", lambda: call(1234567.89, _meta(99, "$", "left"), currency_locale="en_US")),
        ("huge-value", lambda: (1234567890123.45, _meta(1, "£", "left"))),
    ]
```

Wait, checks: empty meta with value 1.0 — format_currency: currency_locale None -> locale_from_currency_code(meta['dxCode']) -> KeyError since meta empty. It's not locale.Error, so raises KeyError. Good, may raise.

none-value: value None -> locale path for dxCode 0 -> setlocale then locale.currency(None, grouping=True) -> probably TypeError. Actually may raise. Fine.

Hmm, but if locale en_US is not available, setlocale raises locale.Error -> caught -> format_currency_from_meta(None, meta) -> None < 0 -> TypeError. Still raises. Fine.

Good. That's it.

One concern: setlocale changes global state and could affect other things, but it's the function's own behavior.

I think this is fine.