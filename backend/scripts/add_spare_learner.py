"""Deprecated legacy helper: placeholder demo users cannot authenticate.

Use the normal StrokeSpeak account registration endpoint instead. This file
is retained only as a historical pointer and performs no database writes.
"""


def main() -> None:
    print("Spare demo-user seeding is disabled.")
    print("Start StrokeSpeak and register a real learner account in the app.")


if __name__ == "__main__":
    main()
