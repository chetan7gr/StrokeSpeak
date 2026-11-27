"""Retired live-database verifier; no network calls or database writes.

This legacy API verification script posted a synthetic practice attempt and deleted it afterward. It is disabled because checks must not write fabricated learner evidence to the live database.
"""


def main() -> None:
    raise SystemExit("This legacy verifier is disabled. It would create synthetic learner evidence.")


if __name__ == "__main__":
    main()
