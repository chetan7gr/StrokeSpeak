"""
StrokeSpeak — Stage 5B-B1.1 Contact Sheet Generator
Generates comprehensive visual contact sheets for:
1. Sanskrit Devanagari (10 vowels)
2. Tamil (12 vowels)
3. Simplified Chinese (9 foundational characters)

Each row displays a character class with:
- Target Character Unicode / Label
- Sample 0 (Train Split)
- Sample 7 (Train Split)
- Sample 14 (Validation Split)
- Sample 18 (Held-out Test Split)
"""

import os
import sys
import json
import cv2
import numpy as np

DATA_DIR = os.path.abspath("backend/data")
ARTIFACT_DIR = os.path.abspath("C:/Users/CHETAN/.gemini/antigravity/brain/ef6c5a04-a48a-4702-a9c0-44e5461eece1")

CONTACT_SHEET_CONFIGS = [
    {
        "name": "Sanskrit Devanagari (10 Vowels)",
        "dir_name": "sanskrit_dataset",
        "output_filename": "sanskrit_dataset_contact_sheet.png",
        "classes": [
            ("अ", "vowel_A"), ("आ", "vowel_AA"), ("इ", "vowel_I"), ("ई", "vowel_II"), ("उ", "vowel_U"),
            ("ऊ", "vowel_UU"), ("ए", "vowel_E"), ("ऐ", "vowel_AI"), ("ओ", "vowel_O"), ("औ", "vowel_AU")
        ]
    },
    {
        "name": "Tamil (12 Vowels)",
        "dir_name": "tamil_dataset",
        "output_filename": "tamil_dataset_contact_sheet.png",
        "classes": [
            ("அ", "vowel_A"), ("ஆ", "vowel_AA"), ("இ", "vowel_I"), ("ஈ", "vowel_II"), ("உ", "vowel_U"),
            ("ஊ", "vowel_UU"), ("எ", "vowel_E"), ("ஏ", "vowel_EE"), ("ஐ", "vowel_AI"), ("ஒ", "vowel_O"),
            ("ஓ", "vowel_OO"), ("ஔ", "vowel_AU")
        ]
    },
    {
        "name": "Simplified Chinese (9 Characters)",
        "dir_name": "chinese_dataset",
        "output_filename": "chinese_dataset_contact_sheet.png",
        "classes": [
            ("一", "char_YI"), ("二", "char_ER"), ("三", "char_SAN"), ("人", "char_REN"), ("大", "char_DA"),
            ("口", "char_KOU"), ("日", "char_RI"), ("月", "char_YUE"), ("山", "char_SHAN")
        ]
    }
]

def make_contact_sheet(cfg):
    dir_path = os.path.join(DATA_DIR, cfg["dir_name"])
    classes = cfg["classes"]
    
    num_rows = len(classes)
    cols = 4  # Sample 0 (Train), Sample 7 (Train), Sample 14 (Val), Sample 18 (Test)
    col_indices = [0, 7, 14, 18]
    col_headers = ["Train (Sample 0)", "Train (Sample 7)", "Val (Sample 14)", "Held-out Test (Sample 18)"]

    cell_size = 128
    label_width = 160
    header_height = 40
    padding = 8

    sheet_w = label_width + cols * (cell_size + padding) + padding
    sheet_h = header_height + num_rows * (cell_size + padding) + padding

    # Light slate background
    sheet = np.ones((sheet_h, sheet_w, 3), dtype=np.uint8) * 245

    # Draw header text
    for c_idx, title in enumerate(col_headers):
        x = label_width + c_idx * (cell_size + padding) + 10
        y = 26
        cv2.putText(sheet, title, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 60), 1, cv2.LINE_AA)

    for r_idx, (glyph, prefix) in enumerate(classes):
        row_y = header_height + r_idx * (cell_size + padding)

        # Label cell
        label_text = f"{glyph} ({prefix})"
        cv2.putText(sheet, label_text, (10, row_y + cell_size // 2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (20, 20, 20), 1, cv2.LINE_AA)

        # 4 samples
        c_dir = os.path.join(dir_path, prefix)
        for c_idx, s_idx in enumerate(col_indices):
            fname = f"{prefix}_{s_idx}.jpg"
            fpath = os.path.join(c_dir, fname)
            x = label_width + c_idx * (cell_size + padding)
            y = row_y

            if os.path.exists(fpath):
                img = cv2.imread(fpath)
                if img is not None:
                    # Draw border around sample
                    border_color = (180, 220, 180) if s_idx < 14 else ((180, 200, 240) if s_idx < 17 else (200, 180, 240))
                    cv2.rectangle(sheet, (x - 1, y - 1), (x + cell_size, y + cell_size), border_color, 1)
                    sheet[y:y+cell_size, x:x+cell_size] = img
            else:
                cv2.rectangle(sheet, (x, y), (x + cell_size, y + cell_size), (200, 200, 200), -1)

    out_path = os.path.join(ARTIFACT_DIR, cfg["output_filename"])
    cv2.imwrite(out_path, sheet)
    print(f"Generated contact sheet: {out_path} ({os.path.getsize(out_path)} bytes)")
    return out_path

def main():
    print("=" * 75)
    print("GENERATING VISUAL CONTACT SHEETS FOR STAGE 5B-B1.1")
    print("=" * 75)
    for cfg in CONTACT_SHEET_CONFIGS:
        make_contact_sheet(cfg)

if __name__ == "__main__":
    main()
