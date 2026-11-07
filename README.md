# The AI Digest

A plain-language daily AI news site plus a short email for one reader. Everything is static HTML, published with GitHub Pages at https://astroninja389.github.io/aidigest/. Every page asks search engines not to index it.

## Layout
- `editions/<date>.json`: the day's stories (the only file written by hand or by the daily task)
- `build.py`: turns an edition into `digests/<date>.html` (full page) and `emails/<date>.html` (bullet email)
- `explainers/`, `learn/`: short background pages the stories link to
- `x-summary.html`: what researchers and journalists on X pointed to
- `robots.txt`, `_config.yml`: keep search engines away and keep build inputs off the published site

## Russian version
`ru/` mirrors the whole site (home, explainers, lessons, X page). Each edition has a Russian twin, `editions/<date>.ru.json`, with the same story ids and the same `main` flags. Build it with `python3 -I build.py <date> --lang ru`, which writes `ru/digests/<date>.html` and `ru/emails/<date>.html`. The English and Russian pages link to each other from their home pages.

## Daily flow
1. Gather stories from checked sources (the source list is kept outside this repository). AI-related news only.
2. Write `editions/<date>.json`. Flag 3 to 5 stories `"main": true` and give each a one-paragraph `"email"` summary. Say plainly what is and isn't established, and disclose when a story involves Anthropic.
3. Add or update explainer pages for any new term a story uses.
4. Run `python3 -I build.py <date> --base-url https://astroninja389.github.io/aidigest` and the same with `--lang ru`.
5. Publish the site, then create the email from `ru/emails/<date>.html` (the email is Russian only).

X is read-only: no posting, replying, liking, reposting or following.
