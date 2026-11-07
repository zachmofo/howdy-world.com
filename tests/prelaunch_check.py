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
        "Request sent",
        "mailto:",
        "gmail.com",
        "/api/quote",
        "cf-turnstile",
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

    if index.forms == 0 and support.forms == 0:
        ok("no project or support form element")
    else:
        fail(f"form count index={index.forms} support={support.forms}")

    quote_url = "https://zachmoffett.com/#quote"
    quote_copy = "Continue to Zach’s project request form; choose Not sure for a web app."
    if quote_url in index_text and quote_url in support_text and quote_copy in index_text and quote_copy in support_text:
        ok("project actions link to the configured zachmoffett.com quote form")
    else:
        fail("configured quote link or instruction is missing")
    if "does not send messages" in index_text or "does not take project requests" in support_text:
        fail("dead-end contact copy remains")
    else:
        ok("dead-end contact copy is gone")

    order = [index_text.find(name) for name in ("stripewell", "bramblewick", "keelstone")]
    if index_text.count("sample-entry") == 3 and order[0] < order[1] < order[2] and -1 not in order:
        ok("three samples are grouped in Stripewell, Bramblewick, Keelstone order")
    else:
        fail(f"sample gallery order/count is wrong: {order}")

    if index_text.count("Fictional concept · not client work") == 3 and "not client projects" in index_text:
        ok("fictional labels are on the gallery")
    else:
        fail("fictional labels are missing")

    if "not claims of shipped apps" in index_text and "Ranch Office Hub" in index_text:
        ok("apps stay potential ideas and Ranch Office Hub keeps its URL")
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

    ids = index.ids
    needed = ["hero", "work", "services", "apps", "project"]
    if all(name in ids for name in needed) and ids.index("work") < ids.index("services"):
        ok("gallery comes before services")
    else:
        fail(f"section ids are {ids}")

    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
