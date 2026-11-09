import random

from backend.stopwords import filter

STOP_WORDS = [
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "further", "once", "here", "there", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "should", "now", "i", "me", "my", "we", "our", "you", "your", "he",
    "him", "his", "she", "her", "it", "its", "they", "them", "their",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "having", "do", "does", "did", "doing", "would",
    "could", "should", "ought", "as", "until", "while", "of", "because",
    "how", "why", "where",
]

NON_STOP_WORDS = [
    "cat", "dog", "house", "tree", "car", "book", "computer", "science",
    "technology", "data", "model", "system", "network", "algorithm",
    "python", "code", "function", "variable", "object", "class", "method",
    "instance", "module", "package", "library", "framework", "database",
    "server", "client", "request", "response", "error", "exception",
    "debug", "test", "performance", "energy", "measurement", "benchmark",
    "analysis", "result", "output", "input", "process", "thread", "memory",
    "cpu", "gpu", "disk", "file", "directory", "path", "url", "http",
    "https", "www", "example", "com", "org", "net", "io", "github",
    "stackoverflow", "google", "amazon", "microsoft", "apple", "linux",
    "windows", "macos", "android", "ios", "javascript", "rust", "golang",
    "java", "c", "c++", "ruby", "php", "swift", "kotlin", "scala",
    "haskell", "lisp", "prolog", "fortran", "cobol", "pascal", "basic",
    "assembly", "binary", "hexadecimal", "decimal", "octal", "integer",
    "float", "string", "boolean", "array", "list", "tuple", "dictionary",
    "set", "queue", "stack", "heap", "graph", "tree", "map", "reduce",
    "filter", "sort", "search", "insert", "delete", "update", "create",
    "read", "write", "open", "close", "start", "stop", "run", "execute",
    "compile", "interpret", "parse", "tokenize", "analyze", "synthesize",
    "optimize", "parallelize", "distribute", "scale", "deploy", "monitor",
    "log", "trace", "profile", "benchmark", "measure", "compare",
    "evaluate", "validate", "verify", "test", "assert", "expect", "mock",
    "stub", "fake", "dummy", "sample", "population", "mean", "median",
    "mode", "variance", "standard", "deviation", "correlation",
    "regression", "classification", "clustering", "neural", "network",
    "deep", "learning", "machine", "artificial", "intelligence", "natural",
    "language", "processing", "computer", "vision", "robotics",
    "automation", "control", "signal", "image", "video", "audio", "text",
    "speech", "recognition", "generation", "translation",
    "summarization", "question", "answering", "chatbot", "agent",
    "environment", "reward", "policy", "value", "function",
    "approximation", "gradient", "descent", "backpropagation", "forward",
    "backward", "layer", "neuron", "weight", "bias", "activation", "relu",
    "sigmoid", "tanh", "softmax", "cross", "entropy", "loss", "accuracy",
    "precision", "recall", "f1", "score", "confusion", "matrix", "roc",
    "auc", "curve", "plot", "chart", "graph", "figure", "table", "row",
    "column", "cell", "header", "footer", "page", "document", "report",
    "summary", "abstract", "introduction", "conclusion", "reference",
    "citation", "bibliography", "appendix", "section", "subsection",
    "paragraph", "sentence", "word", "character", "letter", "number",
    "digit", "symbol", "punctuation", "space", "tab", "newline",
    "carriage", "return", "line", "feed", "form", "vertical", "tab",
    "backspace", "delete", "escape", "shift", "control", "alt", "option",
    "command", "meta", "super", "hyper", "function", "key", "keyboard",
    "mouse", "trackpad", "touchscreen", "stylus", "joystick", "gamepad",
    "controller", "remote", "sensor", "actuator", "motor", "servo",
    "stepper", "solenoid", "relay", "transistor", "diode", "resistor",
    "capacitor", "inductor", "transformer", "battery", "power", "supply",
    "voltage", "current", "resistance", "ohm", "watt", "ampere", "volt",
    "circuit", "board", "chip", "processor", "microcontroller", "arduino",
    "raspberry", "pi", "esp32", "esp8266", "stm32", "atmega", "pic",
    "avr", "arm", "x86", "risc", "cisc", "gpu", "tpu", "npu", "fpga",
    "asic", "soc", "pcb", "solder", "wire", "cable", "connector", "plug",
    "jack", "port", "usb", "hdmi", "displayport", "vga", "dvi",
    "ethernet", "wifi", "bluetooth", "nfc", "rfid", "gps", "gsm", "lte",
    "5g", "4g", "3g", "2g", "1g", "ip", "tcp", "udp", "http", "https",
    "ftp", "smtp", "pop3", "imap", "ssh", "telnet", "dns", "dhcp", "nat",
    "vpn", "proxy", "firewall", "router", "switch", "hub", "modem",
    "access", "point", "repeater", "bridge", "gateway", "server",
    "client", "peer", "node", "host", "domain", "subdomain", "url",
    "uri", "urn", "isbn", "doi", "pmid", "arxiv", "biorxiv", "medrxiv",
    "ssrn", "researchgate", "academia", "jstor", "pubmed", "scopus",
    "web", "science", "wos", "ieee", "acm", "springer", "elsevier",
    "wiley", "taylor", "francis", "sage", "oxford", "cambridge",
    "harvard", "yale", "stanford", "mit", "caltech", "berkeley", "cmu",
    "gatech", "uiuc", "umich", "ucla", "ucsd", "ucsb", "ucdavis",
    "ucirvine", "ucsc", "ucr", "ucmerced", "ucb", "ucsf",
]


def _make_text(n_words, stop_ratio, seed, punctuation=False, numbers=False,
               urls=False, emojis=False, newline_freq=0.0):
    rng = random.Random(seed)
    parts = []
    for _ in range(n_words):
        if rng.random() < stop_ratio:
            w = rng.choice(STOP_WORDS)
        else:
            w = rng.choice(NON_STOP_WORDS)
        parts.append(w)
        if punctuation and rng.random() < 0.15:
            parts.append(rng.choice([".", ",", "!", "?", ";", ":", "-", "(", ")"]))
        if numbers and rng.random() < 0.05:
            parts.append(str(rng.randint(0, 10**6)))
        if urls and rng.random() < 0.02:
            parts.append(f"https://example.com/{rng.randint(0, 1000)}")
        if emojis and rng.random() < 0.05:
            parts.append(rng.choice(["😀", "🚀", "🌟", "🔥", "💡", "📊", "🤖", "🌍", "🎉", "✨"]))
        if newline_freq > 0 and rng.random() < newline_freq:
            parts.append("\n")
    return " ".join(parts)


_TEXT_TYPICAL = _make_text(2000, 0.4, 0, punctuation=True)
_TEXT_LONG = _make_text(10000, 0.4, 1, punctuation=True)
_TEXT_VERY_LONG = _make_text(15000, 0.4, 2, punctuation=True)
_TEXT_ALL_STOP = _make_text(5000, 1.0, 3, punctuation=False)
_TEXT_NO_STOP = _make_text(8000, 0.0, 4, punctuation=False)
_TEXT_PUNCT_NUM_URL = _make_text(5000, 0.3, 5, punctuation=True, numbers=True, urls=True)
_TEXT_UNICODE_EMOJI = _make_text(3000, 0.3, 6, punctuation=True, emojis=True)
_TEXT_MANY_LINES = _make_text(8000, 0.4, 7, punctuation=True, newline_freq=0.1)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("whitespace", lambda: ("   \n\t  ",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("typical-article", lambda: (_TEXT_TYPICAL,)),
        ("long-article", lambda: (_TEXT_LONG,)),
        ("very-long", lambda: (_TEXT_VERY_LONG,)),
        ("all-stopwords", lambda: (_TEXT_ALL_STOP,)),
        ("no-stopwords", lambda: (_TEXT_NO_STOP,)),
        ("punctuation-numbers-urls", lambda: (_TEXT_PUNCT_NUM_URL,)),
        ("unicode-emoji", lambda: (_TEXT_UNICODE_EMOJI,)),
        ("many-short-lines", lambda: (_TEXT_MANY_LINES,)),
    ]
