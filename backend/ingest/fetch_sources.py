"""Download the three raw sources into data/raw/.

    python -m ingest.fetch_sources

Stops with the exact URL + target path on any failure so the file can be placed manually.
"""
import sys
import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

OWASP_PAGES = [
    "A01_2021-Broken_Access_Control",
    "A02_2021-Cryptographic_Failures",
    "A03_2021-Injection",
    "A04_2021-Insecure_Design",
    "A05_2021-Security_Misconfiguration",
    "A06_2021-Vulnerable_and_Outdated_Components",
    "A07_2021-Identification_and_Authentication_Failures",
    "A08_2021-Software_and_Data_Integrity_Failures",
    "A09_2021-Security_Logging_and_Monitoring_Failures",
    "A10_2021-Server-Side_Request_Forgery_(SSRF)",
]

SOURCES: list[tuple[str, Path]] = [
    (
        "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
        RAW_DIR / "mitre" / "enterprise-attack.json",
    ),
    (
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        RAW_DIR / "cisa_kev" / "known_exploited_vulnerabilities.json",
    ),
] + [
    (f"https://raw.githubusercontent.com/OWASP/Top10/master/2021/docs/en/{page}.md", RAW_DIR / "owasp" / f"{page}.md")
    for page in OWASP_PAGES
]


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "cybersec-rag-copilot/0.1"})
    with urllib.request.urlopen(req, timeout=120) as resp, target.open("wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)


def main() -> None:
    for url, target in SOURCES:
        if target.is_file() and target.stat().st_size > 0:
            print(f"skip   {target.relative_to(RAW_DIR)} (already downloaded)")
            continue
        print(f"fetch  {url}")
        try:
            download(url, target)
        except Exception as exc:  # noqa: BLE001 - we want to report every failure the same way
            print(f"\nFAILED: {exc}\n  URL:  {url}\n  Save it manually to:\n  {target}\n", file=sys.stderr)
            sys.exit(1)
        print(f"  -> {target.relative_to(RAW_DIR)}  {target.stat().st_size / 1024:.0f} KB")
    print("All sources present in data/raw/.")


if __name__ == "__main__":
    main()
