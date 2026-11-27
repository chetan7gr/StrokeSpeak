"""Retired reference writer.

The previous generated stroke curves had no independently verified source and
included unsupported source/license labels. This file intentionally performs
no database writes. Use a source-pinned importer and obtain qualified review
before treating a reference as instructional or publishing it.
"""


def main() -> None:
    raise SystemExit(
        "This legacy reference writer is disabled: its generated geometry and "
        "source/license labels were not verified. Existing database paths were "
        "left untouched. See docs/REFERENCE_REVIEW_WORKSHEET.md."
    )


if __name__ == "__main__":
    main()
