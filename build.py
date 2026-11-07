#!/usr/bin/env python3
"""Build the daily web page and email from an edition file.

Usage:
  python3 -I build.py 2026-11-06 [--lang ru] [--base-url https://example.github.io/ai-digest]

English reads editions/<date>.json and writes digests/<date>.html and emails/<date>.html.
Russian (--lang ru) reads editions/<date>.ru.json and writes ru/digests/<date>.html and
ru/emails/<date>.html. The email is a bullet summary of the stories flagged "main", each
linking to its story on the web edition. It opens with a "question of the day" (a
non-technical hook) and ends with its answer and one evergreen article, plus a link to the same edition in the other
language. The list of editions in en.html (or ru/index.html) is refreshed between the
markers. The site's own index.html just forwards visitors to the Russian home page.

The email needs the public site address. Pass --base-url, or the literal {{BASE_URL}}
placeholder stays in so you can see what will be filled in.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

STR = {
    "en": {
        "html_lang": "en",
        "prefix": "",
        "home_file": "en.html",
        "other": ("ru/", "По-русски"),
        "lead_prefix": r"^Lead story: ",
        "home": "Home",
        "learn_heading": "Learn something this week",
        "hello": "Hi Dad,",
        "email_intro": "Here is what happened in AI today. Each item links to the full story, with plain-language explanations of anything unfamiliar. One disclosure: this was written by Claude, an AI made by Anthropic.",
        "read_more": "Read more and the background",
        "also": "Also on the website today: %s.",
        "full": "Today&rsquo;s full edition",
        "all": "All explainers and lessons",
        "qotd": "Question of the day",
        "qotd_answer": "Answer to the question of the day",
        "see_end": "The answer is at the end of this email.",
        "noq": "The edition needs a \"question\" with q, teaser, answer, url and source.",
        "need": "The email needs 3 to 5 stories flagged main; found %d.",
        "noemail": "Story %s is flagged main but has no email summary.",
    },
    "ru": {
        "html_lang": "ru",
        "prefix": "ru/",
        "home_file": "index.html",
        "other": ("", "English version"),
        "lead_prefix": r"^Главная новость: ",
        "home": "Главная",
        "learn_heading": "Чему научиться на этой неделе",
        "hello": "Привет, пап!",
        "email_intro": "Вот что произошло в мире ИИ сегодня. Каждый пункт ведёт к полной истории с простыми объяснениями всего незнакомого. Небольшое пояснение: это письмо написал Claude — ИИ, созданный компанией Anthropic.",
        "read_more": "Подробнее и предыстория",
        "also": "Также сегодня на сайте: %s.",
        "full": "Полный выпуск за сегодня",
        "all": "Все пояснения и уроки",
        "qotd": "Вопрос дня",
        "qotd_answer": "Ответ на вопрос дня",
        "see_end": "Ответ — в конце письма.",
        "noq": "В выпуске нужен блок \"question\" с полями q, teaser, answer, url и source.",
        "need": "Для письма нужно от 3 до 5 новостей с пометкой main; найдено %d.",
        "noemail": "У новости %s есть пометка main, но нет краткого текста для письма.",
    },
}


def load(date, lang):
    name = date + (".ru" if lang == "ru" else "") + ".json"
    with open(os.path.join(HERE, "editions", name), encoding="utf-8") as f:
        return json.load(f)


def sections(stories):
    order, groups = [], {}
    for s in stories:
        name = s.get("section", "")
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(s)
    return [(n, groups[n]) for n in order]


def card(s, root):
    parts = ['<div class="card" id="%s">' % html.escape(s["id"])]
    parts.append("<h2>%s</h2>" % s["title"])
    for p in s["body"]:
        parts.append("<p>%s</p>" % p)
    if s.get("known"):
        parts.append('<p class="known">%s</p>' % s["known"])
    if s.get("learn"):
        parts.append('<p class="learn">%s</p>' % s["learn"])
    parts.append("</div>")
    return "\n".join(parts).replace("{R}", root)


def question(ed, t):
    """The question of the day: an everyday hook that opens the email, answered at
    the end with one evergreen article (it does not have to be news)."""
    q = ed.get("question") or {}
    if not all(q.get(k) for k in ("q", "teaser", "answer", "url", "source")):
        raise SystemExit(t["noq"])
    note = (" (%s)" % q["note"]) if q.get("note") else ""
    link = '<a href="%s">%s</a>%s' % (html.escape(q["url"]), q["source"], note)
    return q, link


def build_page(ed, t):
    root = ".."
    out = []
    out.append("""<!doctype html>
<html lang="%s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>%s</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<main>
<nav class="top"><a href="../%s">%s</a></nav>
<h1>%s</h1>
<p class="small">%s</p>
""" % (t["html_lang"], html.escape(ed["title"]), t["home_file"], t["home"], html.escape(ed["title"]), ed["intro"]))
    q, link = question(ed, t)
    out.append('<div class="card" id="question">\n<h2>%s: %s</h2>\n<p>%s</p>\n<p class="learn">%s</p>\n</div>'
               % (t["qotd"], q["q"], q["answer"], link))
    for name, stories in sections(ed["stories"]):
        if name:
            out.append("<h2>%s</h2>" % html.escape(name))
        for s in stories:
            out.append(card(s, root))
    if ed.get("learn_box"):
        out.append('<h2>%s</h2>\n<div class="card">\n<p>%s</p>\n</div>'
                   % (t["learn_heading"], ed["learn_box"].replace("{R}", root)))
    out.append('<footer class="small">\n<p>%s</p>\n<p>%s</p>\n</footer>\n</main>\n</body>\n</html>\n'
               % (ed.get("footer_known", ""), ed.get("footer_trust", "")))
    return "\n".join(out)


def build_email(ed, site, t):
    """site is the site root; this language's pages live under site/<prefix>."""
    base = site + "/" + t["prefix"].rstrip("/") if t["prefix"] else site
    page = "%s/digests/%s.html" % (base, ed["date"])
    other_prefix, other_label = t["other"]
    other_page = "%s/%sdigests/%s.html" % (site, other_prefix, ed["date"])
    main = [s for s in ed["stories"] if s.get("main")]
    if not 3 <= len(main) <= 5:
        raise SystemExit(t["need"] % len(main))
    items = []
    for s in main:
        if not s.get("email"):
            raise SystemExit(t["noemail"] % s["id"])
        title = re.sub(t["lead_prefix"], "", s["title"])
        title = title[0].upper() + title[1:]
        items.append(
            '<li style="margin:0 0 16px 0"><strong>%s.</strong> %s '
            '<a href="%s#%s">%s</a>.</li>'
            % (title, s["email"], page, s["id"], t["read_more"]))
    others = [s for s in ed["stories"] if not s.get("main")]
    more = ""
    if others:
        names = ", ".join(s["title"] for s in others)
        more = "<p>%s</p>" % (t["also"] % html.escape(names, quote=False))
    q, link = question(ed, t)
    hook = "<p><strong>%s:</strong> %s %s <em>%s</em></p>" % (t["qotd"], q["q"], q["teaser"], t["see_end"])
    answer = "<p><strong>%s.</strong> %s %s.</p>" % (t["qotd_answer"], q["answer"], link)
    return """<!-- Email for %s (%s). Generated by build.py. -->
<div style="max-width:620px;font-family:Georgia,serif;font-size:17px;line-height:1.6;color:#1f2328">
<p>%s</p>
<p>%s</p>
%s
<ul style="padding-left:20px">
%s
</ul>
%s
%s
<p><a href="%s">%s</a> &middot; <a href="%s/%s">%s</a> &middot; <a href="%s">%s</a></p>
<p style="font-size:14px;color:#5b6168">%s</p>
</div>
""" % (ed["date"], t["html_lang"], t["hello"], t["email_intro"], hook, "\n".join(items), more, answer,
       page, t["full"], base, t["home_file"], t["all"], other_page, other_label,
       ed.get("email_footer", ""))


def refresh_index(lang, t):
    suffix = ".ru" if lang == "ru" else ""
    eds = sorted(f[:-len(suffix + ".json")] for f in os.listdir(os.path.join(HERE, "editions"))
                 if f.endswith(suffix + ".json") and (lang == "ru" or not f.endswith(".ru.json")))
    lines = []
    for d in reversed(eds):
        e = load(d, lang)
        lines.append('  <li><a href="digests/%s.html">%s</a></li>' % (d, html.escape(e["label"])))
    path = os.path.join(HERE, t["prefix"] + t["home_file"])
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = "<!-- editions:start -->\n" + "\n".join(lines) + "\n  <!-- editions:end -->"
    text, n = re.subn(r"<!-- editions:start -->.*?<!-- editions:end -->", lambda m: new, text, flags=re.S)
    if n != 1:
        raise SystemExit(path + " is missing the editions markers.")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    date = args[0]
    lang = args[args.index("--lang") + 1] if "--lang" in args else "en"
    if lang not in STR:
        raise SystemExit("Unknown language: " + lang)
    t = STR[lang]
    base = "{{BASE_URL}}"
    if "--base-url" in args:
        base = args[args.index("--base-url") + 1].rstrip("/")
    ed = load(date, lang)
    for sub in ("digests", "emails"):
        os.makedirs(os.path.join(HERE, t["prefix"] + sub), exist_ok=True)
    with open(os.path.join(HERE, t["prefix"] + "digests", date + ".html"), "w", encoding="utf-8") as f:
        f.write(build_page(ed, t))
    with open(os.path.join(HERE, t["prefix"] + "emails", date + ".html"), "w", encoding="utf-8") as f:
        f.write(build_email(ed, base, t))
    refresh_index(lang, t)
    print("Built %sdigests/%s.html and %semails/%s.html" % (t["prefix"], date, t["prefix"], date))


if __name__ == "__main__":
    main()
