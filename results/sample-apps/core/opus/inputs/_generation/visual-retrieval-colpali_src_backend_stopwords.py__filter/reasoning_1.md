We need to write inputs for `filter(text)` in `backend/stopwords.py`. It uses `nlp = spacy.blank("en")`, a blank English pipeline (only tokenizer). So `nlp(text)` produces a Doc with tokens, and `token.is_stop` — for a blank pipeline, is_stop is False by default unless the tokenizer sets it? Actually spacy.blank("en") has a tokenizer but no stop words data? Let's think: `token.is_stop` checks `self.vocab[self.lex_id].is_stop`? In spaCy, `is_stop` comes from the lexeme's `is_stop` flag, which is set by the language's stop words list if available. For `spacy.blank("en")`, the vocab is empty of stop words unless loaded. Actually `spacy.blank("en")` creates a blank English language with a tokenizer; the stop words are not loaded because stop words come from the `lex_attrs` and `stop_words` in the language data. For blank, I believe `is_stop` is False for all tokens. Let me recall: `spacy.blank("en")` gives `nlp.vocab` empty. The `Token.is_stop` property returns `self.lex.is_stop`. The Lexeme's is_stop defaults to False. So with blank en, no token is a stop word. Hmm, but then `filter` would just return the text tokenized and joined by spaces. Still, that's the function's behavior; we just need inputs.

Wait—but maybe the repository does something else. The task says imports: `import spacy` and `nlp = spacy.blank("en")`. So indeed stop words may not be active. But maybe spaCy's blank("en") does load stop words? Let me think carefully. In spaCy v3, `spacy.blank("en")` creates a blank pipeline with a tokenizer. Stop words are part of the language data loaded via `spacy.load("en_core_web_sm")`. Blank models don't include them. However, there is `nlp.Defaults.stop_words`? Actually `spacy.blank("en")` uses the `English` class? No—blank uses `spacy.lang.en.English` and `English.Defaults`. The English defaults include stop words? Let me recall: `spacy.lang.en.stop_words.STOP_WORDS` is a set. The `English` class has `stop_words` attribute? In spaCy v3, `Language.Defaults` has `stop_words`? Hmm. Actually, `spacy.blank("en")` creates `English()` with default config. The tokenizer uses `lex_attr_getters` including `IS_STOP` which uses the language's stop words. I think blank English does include stop words because the stop words are defined in the language module, not the model. Let me verify from memory: In spaCy v3, `spacy.blank("en")` and then `nlp("the cat")` — `doc[0].is_stop`? I believe it returns True for "the". Actually yes, I recall that `spacy.blank("en")` does have stop words; the stop words are part of the language defaults. Let me check: `spacy.lang.en.English.Defaults.stop_words`? Hmm.

Let me think about spaCy source. In `spacy/lang/en/__init__.py`, there's `class English(Language): ...` and `class Defaults(Language.Defaults): ...`? Actually the stop words are in `spacy/lang/en/stop_words.py` as `STOP_WORDS`. And `spacy/lang/en/__init__.py` imports and sets `lex_attr_getters`? In spaCy v3, the `Language` class has a `Defaults` class with `stop_words`? Hmm.

Actually, in spaCy v3, the stop words are added to the vocab by the `Language` initialization? I recall that `spacy.blank("en")` does have stop words. Let me search memory: There's a known issue that blank models don't have stop words? Actually I think in spaCy v2, `spacy.blank("en")` had stop words because the language data was bundled. In v3, the language data (stop words, tokenizer exceptions) are still in the library for English, so blank("en") should have them. The pipeline components (tagger, parser, ner) are not loaded, but the tokenizer and lex_attrs including stop words are.

I'll assume `is_stop` works for common words. But even if not, the function still runs and produces output. Our inputs just need to be realistic text.

The function takes a single string `text`, runs `nlp(text)`, filters out stop tokens, joins remaining tokens with spaces. If all tokens are stop words, returns original text.

We need 8 measured cases, diverse, realistic. Since it's a text filter, inputs are strings. We need to make the function do substantial work: long texts, many tokens. But one call must be ~1ms-200ms. spaCy blank tokenizer is fast; tokenizing 100k characters maybe ~10-50ms. Let's aim for texts of varying sizes: e.g., 10k, 50k, 100k, 200k characters. Also different content: all stop words (returns original), no stop words, mixed, punctuation, numbers, URLs, emojis, long words, unicode, etc.

We must be careful: `nlp(text)` returns a Doc; tokens list comprehension. Output is a string. The output length is compared; keep under 100k values. A string of 200k chars is fine (it's one value). Actually "keep what it returns ... under about 100 000 values" — a string is one value. So fine.

Also arguments are rendered before and after to see if changed — text is immutable, so fine.

Building inputs: generate text with a fixed seed. We can use `random.Random(0)`.

We need 8 cases. Let's design:

1. "typical-sentence": a few sentences, ~500 chars.
2. "long-article": ~50k chars of mixed English text with stop words.
3. "all-stopwords": text made entirely of stop words (e.g., "the a an and or but ..."), length ~10k. This triggers the `len(tokens)==0` branch returning original.
4. "no-stopwords": text with no stop words (e.g., random words from a set of non-stop words, or numbers/URLs), ~20k.
5. "mixed-with-punctuation": text with lots of punctuation, newlines, numbers, ~30k.
6. "unicode-emoji": text with emojis and unicode, ~10k.
7. "very-long": ~200k chars, mixed.
8. "many-short-lines": text with many newlines and short lines, ~50k.

But we need to ensure the function runs without error. spaCy tokenizer handles all text.

We should check: does `spacy.blank("en")` require downloading? No, it's built-in. But is spaCy installed? The task says "Use only the standard library, the repository itself and packages the repository already imports." The repository imports spacy, so it's available. Good.

We need to import `from backend.stopwords import filter`. The module is at `visual-retrieval-colpali/src/backend/stopwords.py`. The import path given: `from backend.stopwords import filter`. So presumably the working directory includes `visual-retrieval-colpali/src` in sys.path, or the repo root is set up. We just use the import as specified.

Now, generating text. We need realistic text. We can create a word list of common English words, some stop words, some not. Use random.Random(0) to generate.

Let's create a vocabulary of common words. Stop words in spaCy English include: "the", "a", "an", "and", "or", "but", "if", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "would", "could", "should", "ought", "i'm", etc. Actually spaCy's stop words list is large.

For our "all-stopwords" case, we can just use a list of known stop words. We can hardcode a set of stop words. But we need to be sure they are recognized as stop words by `spacy.blank("en")`. If blank en doesn't have stop words, this case would not trigger the branch. But it doesn't matter for correctness; the function will still run. However, to be safe, we could check dynamically? No, we can't run at module level to check? We could, but it's not necessary. The task is about performance; the branch is just one path. We can include a case with all stop words regardless.

Actually, let's think: if blank("en") has no stop words, then `is_stop` is always False, and `tokens` is never empty (unless text is empty or whitespace only). So the "all-stopwords" case would just return the tokenized text. Still a valid case.

But we want diverse paths. We can include an empty string case in checks.

Let's write the code.

We need a helper to generate text from a word list. Let's define module-level word lists.

Stop words list (hardcoded, common):
STOP_WORDS = ["the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", "i", "me", "my", "we", "our", "you", "your", "he", "him", "his", "she", "her", "it", "its", "they", "them", "their", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "would", "could", "should", "ought", "as", "until", "while", "of", "because", "how", "why", "where"]

Non-stop words: common nouns, verbs, adjectives: "cat", "dog", "house", "tree", "car", "book", "computer", "science", "technology", "data", "model", "system", "network", "algorithm", "python", "code", "function", "variable", "object", "class", "method", "instance", "module", "package", "library", "framework", "database", "server", "client", "request", "response", "error", "exception", "debug", "test", "performance", "energy", "measurement", "benchmark", "analysis", "result", "output", "input", "process", "thread", "memory", "cpu", "gpu", "disk", "file", "directory", "path", "url", "http", "https", "www", "example", "com", "org", "net", "io", "github", "stackoverflow", "google", "amazon", "microsoft", "apple", "linux", "windows", "macos", "android", "ios", "javascript", "rust", "golang", "java", "c", "c++", "ruby", "php", "swift", "kotlin", "scala", "haskell", "lisp", "prolog", "fortran", "cobol", "pascal", "basic", "assembly", "binary", "hexadecimal", "decimal", "octal", "integer", "float", "string", "boolean", "array", "list", "tuple", "dictionary", "set", "queue", "stack", "heap", "graph", "tree", "map", "reduce", "filter", "sort", "search", "insert", "delete", "update", "create", "read", "write", "open", "close", "start", "stop", "run", "execute", "compile", "interpret", "parse", "tokenize", "analyze", "synthesize", "optimize", "parallelize", "distribute", "scale", "deploy", "monitor", "log", "trace", "profile", "benchmark", "measure", "compare", "evaluate", "validate", "verify", "test", "assert", "expect", "mock", "stub", "fake", "dummy", "sample", "population", "mean", "median", "mode", "variance", "standard", "deviation", "correlation", "regression", "classification", "clustering", "neural", "network", "deep", "learning", "machine", "artificial", "intelligence", "natural", "language", "processing", "computer", "vision", "robotics", "automation", "control", "signal", "image", "video", "audio", "text", "speech", "recognition", "generation", "translation", "summarization", "question", "answering", "chatbot", "agent", "environment", "reward", "policy", "value", "function", "approximation", "gradient", "descent", "backpropagation", "forward", "backward", "layer", "neuron", "weight", "bias", "activation", "relu", "sigmoid", "tanh", "softmax", "cross", "entropy", "loss", "accuracy", "precision", "recall", "f1", "score", "confusion", "matrix", "roc", "auc", "curve", "plot", "chart", "graph", "figure", "table", "row", "column", "cell", "header", "footer", "page", "document", "report", "summary", "abstract", "introduction", "conclusion", "reference", "citation", "bibliography", "appendix", "section", "subsection", "paragraph", "sentence", "word", "character", "letter", "number", "digit", "symbol", "punctuation", "space", "tab", "newline", "carriage", "return", "line", "feed", "form", "feed", "vertical", "tab", "backspace", "delete", "escape", "shift", "control", "alt", "option", "command", "meta", "super", "hyper", "function", "key", "keyboard", "mouse", "trackpad", "touchscreen", "stylus", "joystick", "gamepad", "controller", "remote", "sensor", "actuator", "motor", "servo", "stepper", "solenoid", "relay", "transistor", "diode", "resistor", "capacitor", "inductor", "transformer", "battery", "power", "supply", "voltage", "current", "resistance", "ohm", "watt", "ampere", "volt", "circuit", "board", "chip", "processor", "microcontroller", "arduino", "raspberry", "pi", "esp32", "esp8266", "stm32", "atmega", "pic", "avr", "arm", "x86", "risc", "cisc", "gpu", "tpu", "npu", "fpga", "asic", "soc", "pcb", "solder", "wire", "cable", "connector", "plug", "jack", "port", "usb", "hdmi", "displayport", "vga", "dvi", "ethernet", "wifi", "bluetooth", "nfc", "rfid", "gps", "gsm", "lte", "5g", "4g", "3g", "2g", "1g", "ip", "tcp", "udp", "http", "https", "ftp", "smtp", "pop3", "imap", "ssh", "telnet", "dns", "dhcp", "nat", "vpn", "proxy", "firewall", "router", "switch", "hub", "modem", "access", "point", "repeater", "bridge", "gateway", "server", "client", "peer", "node", "host", "domain", "subdomain", "url", "uri", "urn", "urn", "isbn", "doi", "pmid", "arxiv", "biorxiv", "medrxiv", "ssrn", "researchgate", "academia", "jstor", "pubmed", "scopus", "web", "science", "wos", "ieee", "acm", "springer", "elsevier", "wiley", "taylor", "francis", "sage", "oxford", "cambridge", "harvard", "yale", "stanford", "mit", "caltech", "berkeley", "cmu", "gatech", "uiuc", "umich", "ucla", "ucsd", "ucsb", "ucdavis", "ucirvine", "ucsc", "ucr", "ucmerced", "ucb", "ucsf", "ucsf", "ucsd", "ucsb", "ucsc", "ucr", "ucmerced", "ucb", "ucsf"]

That's too many. Let's keep it simpler: a list of ~200 common non-stop words. We can generate random text by sampling from these.

Actually, we can generate text by sampling words from a combined list, with some probability of stop words. For the "all-stopwords" case, sample only from STOP_WORDS. For "no-stopwords", sample only from NON_STOP_WORDS. For mixed, sample from both.

Also add punctuation, numbers, URLs, emojis.

Let's define:

```python
import random
from backend.stopwords import filter

STOP_WORDS = ["the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", "i", "me", "my", "we", "our", "you", "your", "he", "him", "his", "she", "her", "it", "its", "they", "them", "their", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "would", "could", "should", "ought", "as", "until", "while", "of", "because", "how", "why", "where"]

NON_STOP_WORDS = ["cat", "dog", "house", "tree", "car", "book", "computer", "science", "technology", "data", "model", "system", "network", "algorithm", "python", "code", "function", "variable", "object", "class", "method", "instance", "module", "package", "library", "framework", "database", "server", "client", "request", "response", "error", "exception", "debug", "test", "performance", "energy", "measurement", "benchmark", "analysis", "result", "output", "input", "process", "thread", "memory", "cpu", "gpu", "disk", "file", "directory", "path", "url", "http", "https", "www", "example", "com", "org", "net", "io", "github", "stackoverflow", "google", "amazon", "microsoft", "apple", "linux", "windows", "macos", "android", "ios", "javascript", "rust", "golang", "java", "c", "c++", "ruby", "php", "swift", "kotlin", "scala", "haskell", "lisp", "prolog", "fortran", "cobol", "pascal", "basic", "assembly", "binary", "hexadecimal", "decimal", "octal", "integer", "float", "string", "boolean", "array", "list", "tuple", "dictionary", "set", "queue", "stack", "heap", "graph", "tree", "map", "reduce", "filter", "sort", "search", "insert", "delete", "update", "create", "read", "write", "open", "close", "start", "stop", "run", "execute", "compile", "interpret", "parse", "tokenize", "analyze", "synthesize", "optimize", "parallelize", "distribute", "scale", "deploy", "monitor", "log", "trace", "profile", "benchmark", "measure", "compare", "evaluate", "validate", "verify", "test", "assert", "expect", "mock", "stub", "fake", "dummy", "sample", "population", "mean", "median", "mode", "variance", "standard", "deviation", "correlation", "regression", "classification", "clustering", "neural", "network", "deep", "learning", "machine", "artificial", "intelligence", "natural", "language", "processing", "computer", "vision", "robotics", "automation", "control", "signal", "image", "video", "audio", "text", "speech", "recognition", "generation", "translation", "summarization", "question", "answering", "chatbot", "agent", "environment", "reward", "policy", "value", "function", "approximation", "gradient", "descent", "backpropagation", "forward", "backward", "layer", "neuron", "weight", "bias", "activation", "relu", "sigmoid", "tanh", "softmax", "cross", "entropy", "loss", "accuracy", "precision", "recall", "f1", "score", "confusion", "matrix", "roc", "auc", "curve", "plot", "chart", "graph", "figure", "table", "row", "column", "cell", "header", "footer", "page", "document", "report", "summary", "abstract", "introduction", "conclusion", "reference", "citation", "bibliography", "appendix", "section", "subsection", "paragraph", "sentence", "word", "character", "letter", "number", "digit", "symbol", "punctuation", "space", "tab", "newline", "carriage", "return", "line", "feed", "form", "feed", "vertical", "tab", "backspace", "delete", "escape", "shift", "control", "alt", "option", "command", "meta", "super", "hyper", "function", "key", "keyboard", "mouse", "trackpad", "touchscreen", "stylus", "joystick", "gamepad", "controller", "remote", "sensor", "actuator", "motor", "servo", "stepper", "solenoid", "relay", "transistor", "diode", "resistor", "capacitor", "inductor", "transformer", "battery", "power", "supply", "voltage", "current", "resistance", "ohm", "watt", "ampere", "volt", "circuit", "board", "chip", "processor", "microcontroller", "arduino", "raspberry", "pi", "esp32", "esp8266", "stm32", "atmega", "pic", "avr", "arm", "x86", "risc", "cisc", "gpu", "tpu", "npu", "fpga", "asic", "soc", "pcb", "solder", "wire", "cable", "connector", "plug", "jack", "port", "usb", "hdmi", "displayport", "vga", "dvi", "ethernet", "wifi", "bluetooth", "nfc", "rfid", "gps", "gsm", "lte", "5g", "4g", "3g", "2g", "1g", "ip", "tcp", "udp", "http", "https", "ftp", "smtp", "pop3", "imap", "ssh", "telnet", "dns", "dhcp", "nat", "vpn", "proxy", "firewall", "router", "switch", "hub", "modem", "access", "point", "repeater", "bridge", "gateway", "server", "client", "peer", "node", "host", "domain", "subdomain", "url", "uri", "urn", "urn", "isbn", "doi", "pmid", "arxiv", "biorxiv", "medrxiv", "ssrn", "researchgate", "academia", "jstor", "pubmed", "scopus", "web", "science", "wos", "ieee", "acm", "springer", "elsevier", "wiley", "taylor", "francis", "sage", "oxford", "cambridge", "harvard", "yale", "stanford", "mit", "caltech", "berkeley", "cmu", "gatech", "uiuc", "umich", "ucla", "ucsd", "ucsb", "ucdavis", "ucirvine", "ucsc", "ucr", "ucmerced", "ucb", "ucsf"]
```

That's a bit long but fine. We can trim. Actually, we don't need that many. Let's use a smaller set of ~100 words to keep code readable.

We can generate text by:

```python
def _make_text(n_words, stop_ratio, seed, punctuation=True, numbers=False, urls=False, emojis=False):
    rng = random.Random(seed)
    words = []
    for _ in range(n_words):
        if rng.random() < stop_ratio:
            words.append(rng.choice(STOP_WORDS))
        else:
            words.append(rng.choice(NON_STOP_WORDS))
    text = " ".join(words)
    if punctuation:
        # randomly insert punctuation
        ...
    return text
```

But we need diverse cases. Let's think about what makes the function do work: number of tokens. spaCy tokenizer is fast; 100k tokens maybe ~50ms. Let's aim for cases with token counts from 1k to 100k.

Actually, `nlp(text)` on a 200k character string might take ~100-200ms. That's within range. Let's test mentally: spaCy tokenizer processes ~1M chars/sec? Maybe 500k-1M chars/sec. 200k chars ~0.2-0.4s. Might be over 200ms. Let's be safe: max 100k chars for the largest case. We can have a "very-long" case with ~80k chars.

We need 8 cases. Let's design:

1. "short-sentence": ~100 chars, typical.
2. "medium-article": ~10k chars, mixed stop words.
3. "long-article": ~50k chars, mixed.
4. "very-long": ~100k chars, mixed.
5. "all-stopwords": ~5k chars of only stop words. Triggers branch if stop words work.
6. "no-stopwords": ~10k chars of only non-stop words.
7. "punctuation-numbers": ~20k chars with lots of punctuation, numbers, URLs.
8. "unicode-emoji": ~5k chars with emojis and unicode.

But we need to ensure the function doesn't error on emojis. spaCy handles unicode fine.

Also, we need `checks()` with 2-3 small edge inputs: empty string, whitespace only, maybe None? But the function expects a string; passing None would raise. The instructions say checks may raise. So we can include `None` as an odd type. But the function would raise TypeError. That's fine for checks (identical behavior). Let's include empty string, single word, and None.

Wait: "checks(): 2 or 3 small edge inputs (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise." So we can have:

- ("empty", lambda: ("",))
- ("whitespace", lambda: ("   \n\t  ",))
- ("none", lambda: (None,))

But if None raises, both original and modified should raise the same. That's fine.

Now, for cases, we need exactly 8 measured inputs. We'll define them.

Let's write helper functions to generate text.

We need to be careful about memory: building all inputs under 10s. Generating random text with a few hundred words is fast.

Let's write:

```python
def _random_text(n_words, stop_ratio, seed, punctuation=False, numbers=False, urls=False, emojis=False):
    rng = random.Random(seed)
    parts = []
    for _ in range(n_words):
        r = rng.random()
        if r < stop_ratio:
            w = rng.choice(STOP_WORDS)
        else:
            w = rng.choice(NON_STOP_WORDS)
        parts.append(w)
        if punctuation and rng.random() < 0.1:
            parts.append(rng.choice([".", ",", "!", "?", ";", ":", "-", "(", ")"]))
        if numbers and rng.random() < 0.05:
            parts.append(str(rng.randint(0, 10**6)))
        if urls and rng.random() < 0.02:
            parts.append(f"https://example.com/{rng.randint(0, 1000)}")
        if emojis and rng.random() < 0.05:
            parts.append(rng.choice(["😀", "🚀", "🌟", "🔥", "💡", "📊", "🤖", "🌍", "🎉", "✨"]))
    return " ".join(parts)
```

But joining with spaces might put punctuation separated by spaces. That's fine; tokenizer will handle.

We can also create text with newlines.

For the "all-stopwords" case, we can just generate from STOP_WORDS with stop_ratio=1.0.

For "no-stopwords", stop_ratio=0.0.

For mixed, stop_ratio=0.3 or 0.5.

Let's decide on sizes (number of words):
- short: 20 words (but that's too small, maybe 1ms? Actually spaCy loading might dominate? The nlp object is loaded at module import, so tokenization of 20 words is microseconds. That's fine, but it might be too fast to measure? The task says one call should take roughly 1ms to 200ms. 20 words might be <1ms. Let's make the smallest case ~500 words (~3k chars) which might be ~1-2ms. Actually spaCy tokenizer is fast; 500 words might be ~0.5ms. Let's aim for at least 2000 words for the smallest measured case. 2000 words ~12k chars. That might take ~5-10ms. Good.

Let's set:
1. "typical-article": 2000 words, stop_ratio=0.4, punctuation=True, seed=0. ~12k chars.
2. "long-article": 10000 words, stop_ratio=0.4, punctuation=True, seed=1. ~60k chars.
3. "very-long": 20000 words, stop_ratio=0.4, punctuation=True, seed=2. ~120k chars. Might be ~100ms. Let's check: 20k words ~120k chars. spaCy tokenizer maybe 500k chars/s -> 0.24s. That might be over 200ms. Let's reduce to 15000 words (~90k chars). Or we can measure? We can't measure here. Let's be conservative: max 15000 words.
4. "all-stopwords": 5000 words, stop_ratio=1.0, seed=3. ~30k chars.
5. "no-stopwords": 8000 words, stop_ratio=0.0, seed=4. ~48k chars.
6. "punctuation-numbers": 5000 words, stop_ratio=0.3, punctuation=True, numbers=True, urls=True, seed=5. ~30k chars.
7. "unicode-emoji": 3000 words, stop_ratio=0.3, punctuation=True, emojis=True, seed=6. ~18k chars.
8. "many-short-lines": 8000 words, stop_ratio=0.4, punctuation=True, but with newlines every few words? We can generate text with newlines.

For newlines, we can modify the generator to insert "\n" randomly.

Actually, we can have a separate helper for newlines.

Let's write a more flexible generator:

```python
def _make_text(n_words, stop_ratio, seed, punctuation=False, numbers=False, urls=False, emojis=False, newline_freq=0.0):
    rng = random.Random(seed)
    parts = []
    for i in range(n_words):
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
```

Wait, joining with spaces means newlines will have spaces around them. That's fine.

But for "many-short-lines", we want many newlines. We can set newline_freq=0.1.

Now, we need to import `filter`. The import is `from backend.stopwords import filter`. We must ensure the module is importable. The task says "Import the repository's modules exactly as shown in the task." So we just do that.

We also need to set up any module globals? The function uses `nlp` from its module. That's already defined at module level in the repository. We don't need to set anything.

Now, checks:

```python
def checks():
    return [
        ("empty", lambda: ("",)),
        ("whitespace", lambda: ("   \n\t  ",)),
        ("none", lambda: (None,)),
    ]
```

Cases:

```python
def cases():
    return [
        ("typical-article", lambda: (_make_text(2000, 0.4, 0, punctuation=True),)),
        ("long-article", lambda: (_make_text(10000, 0.4, 1, punctuation=True),)),
        ("very-long", lambda: (_make_text(15000, 0.4, 2, punctuation=True),)),
        ("all-stopwords", lambda: (_make_text(5000, 1.0, 3, punctuation=False),)),
        ("no-stopwords", lambda: (_make_text(8000, 0.0, 4, punctuation=False),)),
        ("punctuation-numbers-urls", lambda: (_make_text(5000, 0.3, 5, punctuation=True, numbers=True, urls=True),)),
        ("unicode-emoji", lambda: (_make_text(3000, 0.3, 6, punctuation=True, emojis=True),)),
        ("many-short-lines", lambda: (_make_text(8000, 0.4, 7, punctuation=True, newline_freq=0.1),)),
    ]
```

But we need to ensure each thunk is cheap. The `_make_text` function is called inside the lambda, which means it runs every time the thunk is called (before each timed call). The instructions say: "Setup is never timed: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed." So it's okay if the thunk builds the text, but "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it". If we build the text inside the thunk, it will be rebuilt for every timed call, which is not timed but could be slow and affect the measurement? Actually, the thunk runs before the timing starts for each call? The description: "We run the original function and a modified version of it on your inputs, each input many times in a row... Thunks run before the timing starts; only the call of the function is timed." So for each repetition, the thunk is called, then the function is called and timed. If the thunk is expensive, it adds overhead but not to the timed portion. However, it could make the overall process slow. Better to build the text once at module level and have the thunk return it. Since the function doesn't modify the text (strings immutable), we can reuse the same string.

So we should precompute the texts at module level.

Let's do:

```python
_TEXT_TYPICAL = _make_text(2000, 0.4, 0, punctuation=True)
_TEXT_LONG = _make_text(10000, 0.4, 1, punctuation=True)
_TEXT_VERY_LONG = _make_text(15000, 0.4, 2, punctuation=True)
_TEXT_ALL_STOP = _make_text(5000, 1.0, 3, punctuation=False)
_TEXT_NO_STOP = _make_text(8000, 0.0, 4, punctuation=False)
_TEXT_PUNCT_NUM_URL = _make_text(5000, 0.3, 5, punctuation=True, numbers=True, urls=True)
_TEXT_UNICODE_EMOJI = _make_text(3000, 0.3, 6, punctuation=True, emojis=True)
_TEXT_MANY_LINES = _make_text(8000, 0.4, 7, punctuation=True, newline_freq=0.1)
```

Then cases return lambdas that just return the precomputed text.

```python
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
```

This is clean and cheap.

Now, we need to ensure the texts are realistic. The word lists should be representative. Let's refine the word lists to be more realistic. Actually, for performance testing, the exact words don't matter much as long as tokenization work is similar. But we want diverse token types: some with punctuation attached, some numbers, some URLs, emojis.

One concern: `spacy.blank("en")` might not have stop words, so `is_stop` is always False. In that case, the "all-stopwords" case won't trigger the branch. But it's still a valid case. The function will tokenize and return all tokens joined. That's fine.

Another concern: The tokenizer might treat some words as stop words if the blank model does have them. Let's check: In spaCy v3, `spacy.blank("en")` does include stop words? I'm now fairly sure it does. Actually, I recall that `spacy.blank("en")` creates a blank pipeline but the `English` language class has a `Defaults` with `stop_words`? Let me think: In spaCy v3, the stop words are in `spacy/lang/en/stop_words.py` and are loaded into the vocab via the `Language` class's `Defaults`? I think the `Language` class has a `stop_words` attribute? Actually, in `spacy/language.py`, `Language.Defaults` has `stop_words = set()`. The English `Defaults` overrides it? Let me recall: `spacy/lang/en/__init__.py` has `class English(Language):` and `class Defaults(Language.Defaults):` with `stop_words = STOP_WORDS`. And `spacy.blank("en")` uses `English` class. So yes, stop words are included. So `is_stop` will be True for common stop words. Good.

Thus, the "all-stopwords" case will trigger the `len(tokens) == 0` branch and return the original text. That's a distinct path.

Now, we need to make sure the function doesn't raise. For "all-stopwords", if the text is all stop words, `tokens` is empty, returns original text. That's fine.

What about "no-stopwords"? All tokens are non-stop, so returns joined tokens.

What about text with only punctuation? Not included, but checks has whitespace.

Now, let's consider the size limits. The largest text: 15000 words. Average word length ~5-6 chars, plus spaces, plus punctuation. 15000 * 7 = 105k chars. That's under 200k. Token count ~15000-20000. The output string is similar length. Under 100k values? A string is one value. So fine.

Memory: 8 strings, total maybe 300k chars = 300KB. Very small.

Building time: generating 15000 words with random choices is fast, <0.1s. Total building all under 1s.

Now, we need to make sure the import works. The repository path: `visual-retrieval-colpali/src/backend/stopwords.py`. The import is `from backend.stopwords import filter`. So the working directory or sys.path must include `visual-retrieval-colpali/src`. The task says "Import the repository's modules exactly as shown in the task." So we just write `from backend.stopwords import filter`. The test harness presumably sets up the path.

We also need to import `random` and `spacy`? No, we only need `random` for generation. The function's module imports spacy. We don't need to import spacy ourselves.

Let's write the final code.

One more thing: The instructions say "Do not fake the environment either: no stand-in programs on PATH, no fake system files." We're not doing that.

Also, "Module globals the function reads must be set on the repository's own module". The function reads `nlp` from its module. We don't need to change it.

Now, let's write the code block.

We should include a docstring? Not necessary.

Let's double-check the word lists. I'll use a smaller set of stop words and non-stop words to keep code concise. The exact words don't matter much.

Stop words: I'll use a list of ~50 common ones.

Non-stop words: ~100 common words.

Let's write:

```python
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
```

That's a lot of words. Maybe too long. Let's trim to a more manageable size. We don't need that many. Let's use ~100 non-stop words. I'll pick a diverse set.

Actually, for the purpose of performance testing, the exact words don't matter. We can use a smaller list. Let's use:

```python
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
```

This is long but fine. Actually, I'll just use a smaller set to keep the code concise. The performance depends on tokenization, not vocabulary size. Let's use a list of 50 non-stop words and 50 stop words. That's enough diversity.

I'll write a compact version.

Let's finalize.

```python
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
```

This is fine. It's long but clear.

Now the generator:

```python
def _make_text(n_words, stop_ratio, seed, punctuation=False, numbers=False, urls=False, emojis=False, newline_freq=0.0):
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
```

Now precompute:

```python
_TEXT_TYPICAL = _make_text(2000, 0.4, 0, punctuation=True)
_TEXT_LONG = _make_text(10000, 0.4, 1, punctuation=True)
_TEXT_VERY_LONG = _make_text(15000, 0.4, 2, punctuation=True)
_TEXT_ALL_STOP = _make_text(5000, 1.0, 3, punctuation=False)
_TEXT_NO_STOP = _make_text(8000, 0.0, 4, punctuation=False)
_TEXT_PUNCT_NUM_URL = _make_text(5000, 0.3, 5, punctuation=True, numbers=True, urls=True)
_TEXT_UNICODE_EMOJI = _make_text(3000, 0.3, 6, punctuation=True, emojis=True)
_TEXT_MANY_LINES = _make_text(8000, 0.4, 7, punctuation=True, newline_freq=0.1)
```

Then checks and cases.

One more thing: The function `filter` is imported but not used in our code except as the target. That's fine.

Let's write the final answer.