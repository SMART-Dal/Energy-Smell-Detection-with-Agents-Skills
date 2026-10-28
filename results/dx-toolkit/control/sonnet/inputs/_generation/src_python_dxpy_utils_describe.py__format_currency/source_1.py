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
        ("en-gb-large", lambda: (9876543.21, _meta(1, "\u00a3", "left"))),
        ("unknown-code-left", lambda: (42.0, _meta(99, "\u20ac", "left"))),
        ("unknown-code-right", lambda: (123456.789, _meta(7, "kr", "right"))),
        ("negative", lambda: (-98765.43, _meta(99, "$", "left"))),
        ("zero-usage", lambda: (0.0, _meta(0, "$", "left"))),
        ("explicit-locale", lambda: call(1234567.89, _meta(99, "$", "left"), currency_locale="en_US")),
        ("huge-value", lambda: (1234567890123.45, _meta(1, "\u00a3", "left"))),
    ]
