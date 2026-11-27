"""Retired live-database verifier; no network calls or database writes.

This legacy audit generated synthetic traces from reference strokes and submitted them as learner attempts. It is disabled to protect learner history. Use genuine learner drawings for validation.
"""


def main() -> None:
    raise SystemExit("This legacy verifier is disabled. It would create synthetic learner evidence.")


if __name__ == "__main__":
    main()
