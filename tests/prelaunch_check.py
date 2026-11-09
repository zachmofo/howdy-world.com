#!/usr/bin/env python3
"""Static prelaunch checks for the Howdy World redesign. No network."""

from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)
    print(f"FAIL {message}")


def ok(message: str) -> None:
    print(f"PASS {message}")


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.h1 = 0
        self.metas: list[tuple[str, str]] = []
        self.links: list[tuple[str, str]] = []
        self.assets: list[str] = []
        self.forms = 0
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "h1":
            self.h1 += 1
        if "id" in data:
            self.ids.append(data["id"])
        if tag == "meta":
            self.metas.append((data.get("name", ""), data.get("content", "")))
            if data.get("property"):
                self.metas.append((data["property"], data.get("content", "")))
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href", "")
        if tag == "a" and data.get("href"):
            self.links.append((data["href"], data.get("target", "")))
        if tag in {"img", "script", "link"} and (data.get("src") or data.get("href")):
            ref = data.get("src") or data.get("href") or ""
            if tag != "a":
                self.assets.append(ref)
        if tag == "form":
            self.forms += 1


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def parse(path: str) -> tuple[str, Document]:
    text = read(path)
    document = Document()
    document.feed(text)
    return text, document


def local_target(url: str) -> Path | None:
    if url.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return None
    path = url.split("#", 1)[0].split("?", 1)[0]
    if path in {"", "/"}:
        path = "/index.html"
    if path.endswith("/"):
        path += "index.html"
    return ROOT / path.lstrip("/")


def check_local_refs(path: str, document: Document) -> None:
    missing = []
    for url in [href for href, _ in document.links] + document.assets:
        target = local_target(url)
        if target is not None and not target.exists():
            missing.append(url)
    if missing:
        fail(f"{path} missing local targets: {missing}")
    else:
        ok(f"{path} local links and assets resolve")


def main() -> int:
    index_text, index = parse("index.html")
    support_text, support = parse("support.html")
    missing_text, missing = parse("404.html")

    if index.h1 == 1:
        ok("homepage has one h1")
    else:
        fail(f"homepage h1 count is {index.h1}")

    if index.canonical == "https://howdy-world.com/":
        ok("homepage canonical is https://howdy-world.com/")
    else:
        fail(f"homepage canonical is {index.canonical!r}")

    robots_meta = [content for name, content in index.metas if name == "robots"]
    if robots_meta == ["index,follow"]:
        ok("homepage robots meta is index,follow")
    else:
        fail(f"homepage robots meta is {robots_meta!r}")

    if "noindex" in index_text.lower() or "noindex" in support_text.lower():
        fail("index or support contains noindex")
    else:
        ok("homepage and support are not noindex")

    if support.canonical == "https://howdy-world.com/support.html":
        ok("support canonical is set")
    else:
        fail(f"support canonical is {support.canonical!r}")

    if missing.h1 == 1 and any(name == "robots" and "noindex" in content for name, content in missing.metas):
        ok("404 has one h1 and noindex")
    else:
        fail("404 heading or noindex is wrong")

    banned = [
        "Review-only",
        "Design preview",
        "forms do not send",
        "Preview complete",
        "Simulation only",
        "has not sent",
        "mailto:",
        "gmail.com",
        "testimonial",
    ]
    for label, text in (("index", index_text), ("support", support_text), ("404", missing_text)):
        hits = [phrase for phrase in banned if phrase.lower() in text.lower()]
        if label == "404":
            hits = [phrase for phrase in hits if phrase.lower() != "noindex"]
        if hits:
            fail(f"{label} contains banned copy: {hits}")
        else:
            ok(f"{label} has no mockup banner, fake success, or invented mail")

    if index.forms == 1 and support.forms == 0:
        ok("homepage has one quote form and support has none")
    else:
        fail(f"form count index={index.forms} support={support.forms}")

    quote_action = 'action="https://zachmoffett.com/api/quote"'
    if quote_action in index_text and 'method="post"' in index_text and 'name="source" value="howdy-world"' in index_text:
        ok("quote form posts to zachmoffett.com and tags howdy-world")
    else:
        fail("quote form action, method, or source is wrong")
    required_fields = ("name", "email", "business", "location", "tier", "message", "company_website")
    missing_fields = [name for name in required_fields if f'name="{name}"' not in index_text]
    tier_options = all(option in index_text for option in ("Basic", "Standard", "Premium", "Not sure"))
    if not missing_fields and tier_options and "Select a tier" in index_text:
        ok("quote form keeps the zach field names and tiers")
    else:
        fail(f"quote fields missing: {missing_fields}")
    if "0x4AAAAAAFtp7kxdG920BkRZ" in index_text and "api.js?render=explicit" in index_text:
        ok("Turnstile uses the existing sitekey and explicit render")
    else:
        fail("Turnstile sitekey or explicit render is missing")
    quote_js = read("assets/quote.js")
    if (
        "turnstile.render" in quote_js
        and 'response-field-name": "cf-turnstile-response"' in quote_js
        and "event.preventDefault()" in quote_js
        and "HTMLFormElement.prototype.submit.call(form)" in quote_js
        and "resetWidget()" in quote_js
    ):
        ok("quote script renders Turnstile, blocks a tokenless submit, then navigates")
    else:
        fail("quote script is missing the explicit-render submit guard")
    success_at = index_text.find('id="quote-success"')
    success_tag = index_text[success_at:success_at + 80] if success_at != -1 else ""
    before_success = index_text[:success_at] if success_at != -1 else index_text
    if success_at != -1 and "hidden" in success_tag and "Request sent." not in before_success and 'sent === "1"' in index_text:
        ok("confirmation copy stays hidden unless the server returns sent=1")
    else:
        fail("confirmation copy is not gated on the server redirect")
    if "/#quote" in support_text and "https://zachmoffett.com/#quote" not in support_text:
        ok("support project links point at the homepage quote form")
    else:
        fail("support still sends project requests away from the homepage form")
    if "does not send messages" in index_text or "does not take project requests" in support_text:
        fail("dead-end contact copy remains")
    else:
        ok("dead-end contact copy is gone")

    order = [index_text.find(name) for name in ("stripewell", "bramblewick", "keelstone")]
    if all(index_text.count(f"card-{name}") == 1 for name in ("lawn", "bake", "keel")) and order[0] < order[1] < order[2]:
        ok("three samples are grouped in Stripewell, Bramblewick, Keelstone order")
    else:
        fail(f"sample gallery order/count is wrong: {order}")

    if index_text.count("· fictional") >= 3 and "fictional businesses" in index_text and "Not client projects." in index_text:
        ok("fictional labels are on the gallery")
    else:
        fail("fictional labels are missing")

    if "Not shipped client work" in index_text and "Ranch Office Hub" in index_text:
        ok("apps stay examples and Ranch Office Hub keeps its URL")
    else:
        fail("apps disclaimer or Ranch Office Hub link is missing")

    for needle in (
        "https://github.com/zachmofo",
        "https://youtube.com/@howdy-world-coding",
        "/learn.html",
        "/support.html",
        "/app/ranch-office-hub.html",
    ):
        if needle in index_text:
            ok(f"homepage keeps {needle}")
        else:
            fail(f"homepage missing {needle}")

    for needle in (
        "not a tax-deductible charity",
        "not a payment for website or app services",
        "https://venmo.com/u/Zachmoffett",
        "@Zachmoffett",
        "https://cash.app/$ZachMoffett",
        "$ZachMoffett",
        "https://paypal.me/zachmoffett",
        "@zachmoffett",
        "3BrYKKNQQe9MrnRTyje4fgp4QvmzuiqjYV",
        "Bitcoin network only",
        "Howdy World",
    ):
        if needle in support_text:
            ok(f"support keeps {needle}")
        else:
            fail(f"support missing {needle}")

    if "Fraunces" in read("assets/site.css") and "Figtree" in read("assets/site.css"):
        ok("self-hosted Fraunces and Figtree are referenced")
    else:
        fail("font families missing from site.css")

    if (ROOT / "assets/fonts/OFL.txt").exists():
        ok("font license file is present")
    else:
        fail("assets/fonts/OFL.txt missing")

    robots = read("robots.txt")
    if "Disallow: /" in robots:
        fail("robots.txt disallows the whole site")
    elif "Sitemap: https://howdy-world.com/sitemap.xml" in robots and "Allow: /" in robots:
        ok("robots.txt allows the site and points at the sitemap")
    else:
        fail("robots.txt is incomplete")

    if (ROOT / "_headers").exists():
        fail("staging _headers file must not be copied")
    else:
        ok("no staging _headers file")

    sitemap = read("sitemap.xml")
    sitemap_missing = [
        loc
        for loc in (
            "https://howdy-world.com/",
            "https://howdy-world.com/learn.html",
            "https://howdy-world.com/learn/00-intro.html",
            "https://howdy-world.com/learn/05-fetch.html",
            "https://howdy-world.com/support.html",
            "https://howdy-world.com/app/ranch-office-hub.html",
        )
        if loc not in sitemap
    ]
    if sitemap_missing:
        fail(f"sitemap missing {sitemap_missing}")
    else:
        ok("sitemap lists the homepage, lessons, support, and Ranch Office Hub")

    base = None
    for ref in ("main", "origin/main"):
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            base = ref
            break
    if base is None:
        fail("neither main nor origin/main is available for the preservation diff")
        preserved = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    else:
        preserved = subprocess.run(
            ["git", "diff", "--name-only", base, "--", "learn", "styles.css", "app", "images", "CNAME"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    if preserved.returncode == 0 and not preserved.stdout.strip():
        ok("lessons, lesson CSS, app pages, images, and CNAME are unchanged")
    else:
        fail(f"preserved paths changed:\n{preserved.stdout}{preserved.stderr}")

    lesson_footer = read("learn/00-intro.html")
    if "Start a project" in lesson_footer or "Web &amp; Apps" in lesson_footer:
        fail("lesson footer picked up commercial lead copy")
    else:
        ok("lesson footer remains the learning footer")

    for archive in ("app/lumapps.html", "app/ranch-office-hub.html", "images/cyberskull.jpg"):
        if (ROOT / archive).exists():
            ok(f"kept {archive}")
        else:
            fail(f"deleted {archive}")

    check_local_refs("index.html", index)
    check_local_refs("support.html", support)
    check_local_refs("404.html", missing)

    css = read("assets/site.css")
    if 'url("fonts/' in css and 'url("assets/fonts/' not in css:
        ok("font URLs resolve from /assets/site.css")
    else:
        fail("font URLs would 404 from the stylesheet location")

    if "prefers-reduced-motion" in css and "focus-visible" in css:
        ok("reduced motion and focus styles are in the stylesheet")
    else:
        fail("motion or focus CSS is missing")

    home_css = read("assets/home.css")
    if "Fraunces" in home_css and "Figtree" in home_css and 'url("fonts/' in home_css:
        ok("homepage fonts resolve from /assets/home.css")
    else:
        fail("homepage font URLs would 404")
    if "prefers-reduced-motion" in home_css and "focus-visible" in home_css and "#245c4a" in home_css:
        ok("homepage keeps the Howdy green, focus, and reduced motion")
    else:
        fail("homepage accent, focus, or motion CSS is missing")

    ids = index.ids
    needed = ["hero", "work", "apps", "contact", "quote"]
    if all(name in ids for name in needed) and ids.index("work") < ids.index("apps") < ids.index("quote"):
        ok("gallery comes before apps and the quote form")
    else:
        fail(f"section ids are {ids}")

    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
