The function reads a file and returns a set of stripped lines. Cases: different file sizes and content. Need files under WORKDIR. The thunk returns (file_path,).

Note the function reads the file each call; so files must exist. Keep thunk cheap: just return path.

Let's write 8 cases with varied sizes and content: small, medium, large, many duplicates, blank lines, whitespace, long lines, unicode, etc.

Careful: output is a set of strings, must stay under 100k values. So keep lines under ~50k.

Let's build files at module level.

Cases:
1. small typical: 100 lines
2. medium: 5,000 lines random words
3. large: 50,000 lines
4. duplicates: 20,000 lines drawn from small vocabulary (set small)
5. whitespace/blank lines: mixed
6. long lines: few hundred very long lines
7. unicode: 10,000 lines with unicode
8. sorted/alphabetical? maybe numeric-ish lines.

Keep each file under 100MB. Fine.

checks: empty file, single line, file with only newline, maybe None path -> raises. checks may raise. Let's do empty file, single line, and None path (TypeError). Actually None path raises TypeError - fine.

Let's write.

For blank lines: lines that are empty string after strip -> adds "". Fine.

Let me write the code.

Use random.Random(0) for generation.

Time: reading 50k lines ~ few ms. Maybe use larger to hit ~ms. 200k lines? Output set would be up to 200k values > 100k limit. Keep under 100k lines. Let's use 60,000 lines for the largest with some duplicates so set < 100k. Actually output set size counts; 60k distinct is fine.

Let's make the big case 80,000 lines with duplicates from 40,000 vocabulary → set of 40k.

Fine.

File writing at module level under 10s.

Write files:

_W1 = WORKDIR / "common_small.txt"
etc.

Let me write helper _write(name, lines).

For the long-lines case, lines could be 10,000 chars each, 500 lines → 5MB. Fine.

Let's produce.