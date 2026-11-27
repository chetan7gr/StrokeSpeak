# Katakana CNN data intake

No Katakana images are included here. The CNN remains `UNTRAINED` until a lawful, verified dataset is installed and evaluated. Do not create synthetic examples or promote learner practice drawings into training data without explicit consent.

## Candidate source

AIST's ETL Character Database includes ETL6, a handwritten dataset of 46 Katakana classes. The official page reports 1,383 writers and 157,662 samples. Read and accept AIST's current Terms of Use yourself before downloading. AIST retains copyright; use is free under its terms, but redistribution of the dataset is restricted to AIST's site. Do not put ETL6 source archives or extracted images into a public project ZIP.

- Dataset overview: https://etlcdb.db.aist.go.jp/the-etl-character-database/
- Official download and Terms of Use: https://etlcdb.db.aist.go.jp/download2/
- Required citation: Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984.

## Local intake format

After downloading via AIST and unpacking ETL6 with its official unpacker, place images under this folder and create `annotations.csv` with the exact columns `filename,character,writer_id`. Paths in `filename` must be relative to this folder. Preserve each source writer identifier; writer-disjoint train/validation/test splits are required to prevent leakage. Map only the standard 46 Katakana below. Do not infer labels or writer IDs from file order.

Create `dataset_manifest.json` with: `script_code` (`ja-katakana`), `dataset_name` (`ETL6`), `source_url`, `license_name`, `terms_of_use_accepted` (true only after you accept AIST's terms), `terms_accepted_date`, `citation`, and `source_archive_sha256`. Keep the archive checksum for provenance; never copy the archive into the submission package.

Run the read-only preflight from the project root:

```powershell
& .\backend\.venv\Scripts\python.exe .\backend\scripts\preflight_katakana_dataset.py
```

The preflight checks manifest provenance, all 46 classes, image readability, duplicate files, minimum sample counts, and writer diversity. It creates no files and does not train or register a model. Training and real learner validation remain separate steps.

Classes: ア イ ウ エ オ カ キ ク ケ コ サ シ ス セ ソ タ チ ツ テ ト ナ ニ ヌ ネ ノ ハ ヒ フ ヘ ホ マ ミ ム メ モ ヤ ユ ヨ ラ リ ル レ ロ ワ ヲ ン
The Katakana training script is backend/scripts/train_katakana_cnn.py. It first runs the read-only preflight, partitions writers into disjoint train/validation/test groups, augments training images only, and writes a local model draft under this directory's artifacts/ folder. It does not modify MySQL, the model registry, or public status. Review the held-out metrics and rights before promoting or redistributing any artifact.
