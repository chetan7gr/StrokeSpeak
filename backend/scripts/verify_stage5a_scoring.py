"""Retired live-database verifier; no network calls or database writes.

This legacy scoring verifier posted synthetic traces as practice attempts and then deleted the rows. It is disabled to protect learner history; use genuine learner drawings for validation.
"""


def main() -> None:
    raise SystemExit("This legacy verifier is disabled. It would create synthetic learner evidence.")


if __name__ == "__main__":
    main()
