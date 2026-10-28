The function takes a string and escapes control chars, backslash, and 127. We need 8 cases with substantial work. The regex substitution over a long string.

Let me create strings of varying lengths and densities of special characters.

Cases:
1. Long string with no special chars (pure ASCII printable) - regex scans whole thing.
2. Long string with many newlines/tabs.
3. String with all control chars 0-31 heavily.
4. String with many backslashes.
5. Mixed random with seed.
6. String with unicode characters (non-ASCII above 127) - these aren't escaped, just scanned.
7. Very long string ~500k chars.
8. String with 127 char (DEL) mixed.

Keep output under 100k values. A string is one value. Under 1M values for args.

Let me size so each call takes ~1ms-200ms. re.sub on a few hundred KB string takes maybe a few ms.

Let me build strings.

For "no special chars" - 1,000,000 chars of printable ASCII. re.sub scans - probably ~10-50ms.

Let's do sizes around 200k-1M.

Let me write.

For diversity:
- mostly printable, 1M chars
- 500k chars with 10% newlines
- 200k chars all control chars
- 300k chars 30% backslashes
- random mix with seed, 400k
- unicode heavy, 500k
- alternating pattern
- DEL chars

Output: escaped string. For all-control-chars string of 200k, output is 200k*4 = 800k chars - that's one value, fine (under 100k values means count of values, a string is one value). Actually "keep what it returns ... under about 100 000 values" - a single string is one value. But memory... 800k chars is fine.

Actually careful: args rendered before/after - string rendered. 1M chars is fine.

Let me write it.

def _printable(n, seed): rng, chars from printable ascii range.

Let me just do it.

Use random.Random(0) for generation.

Cases:

1. "plain-ascii-1M": 1_000_000 printable chars.
2. "newlines-dense": 500_000 chars, 15% '\n'.
3. "all-controls": 200_000 chars cycling through 0-31 randomly.
4. "backslash-heavy": 300_000 chars, 40% backslash.
5. "mixed-random": 400_000 chars random from full 0-127.
6. "unicode-heavy": 500_000 chars from range 128-0x10FFFF.
7. "del-and-controls": 300_000 chars with 127 and controls.
8. "tabs-and-cr": 500_000 chars with tabs and carriage returns.

checks:
- empty string
- single char
- string with only backslash/control

Let me write code.

For unicode generation, avoid surrogates (0xD800-0xDFFF) which cause issues in some contexts. Actually re.sub on a str with surrogates works in Python but let's avoid to be safe when printing/rendering. Use range 128-0xD7FF and 0xE000-0x10FFFF.

Let me write.