"""
StrokeSpeak — Stage 5A.2 Curriculum Sequence Reorganization Script
Organizes curriculum across all four scripts into clear, authentic pedagogical sequences:

1. Sanskrit (sa-devanagari):
   - Foundation Unit 1: स्वर (Svara / Vowels: अ, आ, इ, ई, उ, ऊ, ऋ, ए, ऐ, ओ, औ, अं)
   - Foundation Unit 2: व्यंजन (Vyanjana / Consonants: क-वर्ग Velar Group)
   - Beginner Unit 1: मात्राएँ (Mātrās / Vowel Signs)
   - Beginner Unit 2: सरल शब्द (Sarala Śabdāḥ / Simple Words)
   - Beginner Unit 3: सरल वाक्य (Sarala Vākyāni / Simple Sentences)

2. Tamil (ta):
   - Foundation Unit 1: உயிரெழுத்து (12 Uyir Vowels: அ through ஔ)
   - Foundation Unit 2: மெய்யெழுத்து (18 Mei Consonants: வல்லினம் / Hard Stops)
   - Foundation Unit 3: உயிர்மெய்யெழுத்து (216 Uyirmei Combinations: க-வரிசை)
   - Beginner Unit 1: சொற்கள் (Soṟkaḷ / Words: Essential Vocabulary)
   - Beginner Unit 2: வாக்கியங்கள் (Vākkiyaṅkaḷ / Sentences: Everyday Phrases)
   - Elementary Unit 1: காலங்கள் (Tense practice & verb forms)
   - Advanced Unit 1: உரையாடல் (Conversational dialogue & review)

3. Simplified Chinese (zh-hans):
   - Foundation Unit 1: 基础汉字 (Basic Foundational Characters: 一, 二, 三, 人, 大)
   - Foundation Unit 2: 常用独体字与部首 (Radicals & Basic Characters: 口, 日, 月, 山, 小)
   - Beginner Unit 1: 常用词汇 (Essential Vocabulary: 你好, 谢谢, 朋友)
   - Beginner Unit 2: 基础句型 (Basic Sentences: 你好吗？, 我是学生。)

4. Japanese Hiragana (ja-hiragana):
   - Preserved 100% intact with zero changes.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection


def reorganize_curriculum():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print("=" * 70)
    print("StrokeSpeak — Stage 5A.2 Curriculum Sequence Reorganization")
    print("=" * 70)

    # 1. Full pre-modification backup of learning_lessons
    cursor.execute("SELECT * FROM learning_lessons ORDER BY id")
    all_lessons_backup = cursor.fetchall()
    backup_file = os.path.abspath(f"backend/scripts/backup_lessons_pre_stage5a2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(all_lessons_backup, f, ensure_ascii=False, indent=2, default=str)
    print(f" [PASS] Full lessons backup created: {backup_file} ({len(all_lessons_backup)} rows)")

    # 2. Get language IDs
    cursor.execute("SELECT id, script_code FROM languages WHERE script_code IN ('sa-devanagari', 'ta', 'zh-hans')")
    lang_map = {r["script_code"]: r["id"] for r in cursor.fetchall()}
    sanskrit_id = lang_map["sa-devanagari"]
    tamil_id = lang_map["ta"]
    chinese_id = lang_map["zh-hans"]

    # ------------------------------------------------------------------------
    # SANSKRIT LESSONS REORGANIZATION
    # ------------------------------------------------------------------------
    print("\n--- Reorganizing Sanskrit Curriculum (sa-devanagari) ---")

    # Update existing Sanskrit vowel lessons in Foundation Unit 1 (orders 1 to 5)
    cursor.execute("""
        UPDATE learning_lessons SET
            unit_number = 1,
            lesson_order = 1,
            level = 'foundation',
            category = 'character',
            title = 'स्वर · अ (Short vowel a)',
            explanation = 'अ is the primary short vowel in Sanskrit. In Devanagari, its shirorekha (head bar) caps only the right vertical stem, leaving the left vowel curve open.'
        WHERE id = 339
    """)
    cursor.execute("""
        UPDATE learning_lessons SET
            unit_number = 1,
            lesson_order = 2,
            level = 'foundation',
            category = 'character',
            title = 'स्वर · आ (Long vowel ā)',
            explanation = 'आ is the long vowel formed by adding a vertical matra danda to अ. The shirorekha caps both vertical stems.'
        WHERE id = 340
    """)
    cursor.execute("""
        UPDATE learning_lessons SET
            unit_number = 1,
            lesson_order = 3,
            level = 'foundation',
            category = 'character',
            title = 'स्वर · इ (Short vowel i)',
            explanation = 'इ begins with a small vertical tick, curves in a serpentine S-shape, and finishes with a lower loop/knot and diagonal tail.'
        WHERE id = 341
    """)
    cursor.execute("""
        UPDATE learning_lessons SET
            unit_number = 1,
            lesson_order = 4,
            level = 'foundation',
            category = 'character',
            title = 'स्वर · ई (Long vowel ī)',
            explanation = 'ई features the same S-curve body and lower knot as इ, with an overarching reph hook curving rightward above the shirorekha.'
        WHERE id = 342
    """)
    cursor.execute("""
        UPDATE learning_lessons SET
            unit_number = 1,
            lesson_order = 5,
            level = 'foundation',
            category = 'character',
            title = 'स्वर · उ (Short vowel u)',
            explanation = 'उ consists of dual stacked curves capped by a full shirorekha.'
        WHERE id = 343
    """)

    # Check and insert remaining Sanskrit vowels (orders 6 to 12)
    sanskrit_vowels_to_add = [
        (sanskrit_id, 'character', 'foundation', 1, 6, 'स्वर · ऊ (Long vowel ū)', 'ऊ', 'Long vowel ū', 'ū', 'ऊ has the dual curves of उ with a middle curved tail descending from the waist to the right.'),
        (sanskrit_id, 'character', 'foundation', 1, 7, 'स्वर · ऋ (Vocalic r)', 'ऋ', 'Vocalic r vowel', 'ṛ', 'ऋ is a vocalic vowel in Sanskrit with a vertical stem, leftward hooks, and a lower right loop.'),
        (sanskrit_id, 'character', 'foundation', 1, 8, 'स्वर · ए (Vowel e)', 'ए', 'Vowel e', 'e', 'ए features a left descending diagonal limb and a right inward-turning arm capped by a shirorekha.'),
        (sanskrit_id, 'character', 'foundation', 1, 9, 'स्वर · ऐ (Diphthong ai)', 'ऐ', 'Diphthong ai', 'ai', 'ऐ has the base form of ए with a slanted matra ascending up and left from above the left stem.'),
        (sanskrit_id, 'character', 'foundation', 1, 10, 'स्वर · ओ (Vowel o)', 'ओ', 'Vowel o', 'o', 'ओ consists of the base body of आ with a top slanted matra anchored to the second vertical stem.'),
        (sanskrit_id, 'character', 'foundation', 1, 11, 'स्वर · औ (Diphthong au)', 'औ', 'Diphthong au', 'au', 'औ has the base body of आ with two slanted matras anchored to the second vertical stem.'),
        (sanskrit_id, 'character', 'foundation', 1, 12, 'स्वर · अं (Anusvāra)', 'अं', 'Nasal marker anusvara', 'aṃ', 'The anusvara (dot above shirorekha) represents pure nasal resonance in Sanskrit.')
    ]
    for row in sanskrit_vowels_to_add:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Sanskrit vowel lesson: {row[5]}")

    # Sanskrit Consonants (Foundation Unit 2: क-वर्ग Velar Group)
    sanskrit_consonants = [
        (sanskrit_id, 'character', 'foundation', 2, 1, 'व्यंजन · क (Unvoiced velar stop)', 'क', 'Consonant ka', 'ka', 'क begins with a central vertical stem, a left closed loop, and a right open hook.'),
        (sanskrit_id, 'character', 'foundation', 2, 2, 'व्यंजन · ख (Aspirated velar stop)', 'ख', 'Consonant kha', 'kha', 'ख has an initial curved loop turning down, connected to a vertical stem containing an inner loop.'),
        (sanskrit_id, 'character', 'foundation', 2, 3, 'व्यंजन · ग (Voiced velar stop)', 'ग', 'Consonant ga', 'ga', 'ग consists of a left vertical stroke ending in an inner loop, followed by a full vertical stem.'),
        (sanskrit_id, 'character', 'foundation', 2, 4, 'व्यंजन · घ (Aspirated voiced velar stop)', 'घ', 'Consonant gha', 'gha', 'घ consists of dual leftward curves touching the vertical stem.'),
        (sanskrit_id, 'character', 'foundation', 2, 5, 'व्यंजन · ङ (Velar nasal)', 'ङ', 'Consonant ṅa', 'ṅa', 'ङ has the serpentine S-curve shape of ड with a distinguishing nasal dot on the right.')
    ]
    for row in sanskrit_consonants:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Sanskrit consonant lesson: {row[5]}")

    # Sanskrit Matras (Beginner Unit 1)
    sanskrit_matras = [
        (sanskrit_id, 'character', 'beginner', 1, 1, 'मात्रा · आ-मात्रा (ा)', 'का', 'Consonant ka with long ā matra', 'kā', 'The ā-matra adds a vertical danda after the consonant, lengthening its sound to kā.'),
        (sanskrit_id, 'character', 'beginner', 1, 2, 'मात्रा · इ-मात्रा (ि)', 'कि', 'Consonant ka with short i matra', 'ki', 'The short i-matra arches from the left over the top shirorekha to touch the consonant stem.'),
        (sanskrit_id, 'character', 'beginner', 1, 3, 'मात्रा · ई-मात्रा (ी)', 'की', 'Consonant ka with long ī matra', 'kī', 'The long ī-matra arches from the right vertical line over the shirorekha.'),
        (sanskrit_id, 'character', 'beginner', 1, 4, 'मात्रा · उ-मात्रा (ु)', 'कु', 'Consonant ka with short u matra', 'ku', 'The short u-matra is a small curled hook attached to the bottom foot of the consonant.')
    ]
    for row in sanskrit_matras:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Sanskrit matra lesson: {row[5]}")

    # Update existing Sanskrit word lessons in Beginner Unit 2
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 1, title = 'शब्द · नमस्ते (Namaste)', translation_text = 'Salutations / Traditional greeting' WHERE id = 344
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 2, title = 'शब्द · जलम् (Water)', translation_text = 'Water' WHERE id = 345
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 3, title = 'शब्द · मित्रम् (Friend)', translation_text = 'Friend / Companion' WHERE id = 346
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 4, title = 'शब्द · पुस्तकम् (Book)', translation_text = 'Book / Study text' WHERE id = 347
    """)

    # Sanskrit Sentences (Beginner Unit 3)
    sanskrit_sentences = [
        (sanskrit_id, 'sentence', 'beginner', 3, 1, 'सरल वाक्य · अहं पठामि', 'अहं पठामि।', 'I read / I study.', 'aham paṭhāmi', 'Subject (अहम् = I) with present tense first-person verb (पठामि = I read).'),
        (sanskrit_id, 'sentence', 'beginner', 3, 2, 'सरल वाक्य · इदं जलम् अस्ति', 'इदं जलम् अस्ति।', 'This is water.', 'idam jalam asti', 'Demonstrative pronoun (इदम् = this) + noun (जलम् = water) + copula verb (अस्ति = is).')
    ]
    for row in sanskrit_sentences:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Sanskrit sentence lesson: {row[5]}")

    # ------------------------------------------------------------------------
    # TAMIL LESSONS REORGANIZATION
    # ------------------------------------------------------------------------
    print("\n--- Reorganizing Tamil Curriculum (ta) ---")

    # Clean up Unit 1 Vowels (IDs 223 to 234 -> orders 1 to 12)
    tamil_vowel_updates = [
        (223, 1, 'உயிரெழுத்து · அ (Short vowel a)', 'Starter vowel / Short a'),
        (224, 2, 'உயிரெழுத்து · ஆ (Long vowel aa)', 'Long vowel aa with bottom flourish loop'),
        (225, 3, 'உயிரெழுத்து · இ (Short vowel i)', 'Short vowel i with upper crown arch and lower S-curve flourish'),
        (226, 4, 'உயிரெழுத்து · ஈ (Long vowel ii)', 'Long vowel ii with two vertical pillars, center stem, and dual pulli dots'),
        (227, 5, 'உயிரெழுத்து · உ (Short vowel u)', 'Short vowel u with circular head, curved neck, and horizontal base'),
        (228, 6, 'உயிரெழுத்து · ஊ (Long vowel uu)', 'Long vowel uu with base உ and secondary superscript ள'),
        (229, 7, 'உயிரெழுத்து · எ (Short vowel e)', 'Short vowel e with bottom-left circular eye and vertical rise'),
        (230, 8, 'உயிரெழுத்து · ஏ (Long vowel ee)', 'Long vowel ee with base எ and downward-left diagonal slant tail'),
        (231, 9, 'உயிரெழுத்து · ஐ (Diphthong ai)', 'Diphthong ai with double-scallop upper wave and lower lobes'),
        (232, 10, 'உயிரெழுத்து · ஒ (Short vowel o)', 'Short vowel o with top eye, arched dome, inner fold, and curved tail'),
        (233, 11, 'உயிரெழுத்து · ஓ (Long vowel oo)', 'Long vowel oo with base ஒ and terminal curled loop flourish'),
        (234, 12, 'உயிரெழுத்து · ஔ (Diphthong au)', 'Diphthong au compound with base ஒ on left and auxiliary ள on right')
    ]
    for lid, order, title, expl in tamil_vowel_updates:
        cursor.execute("""
            UPDATE learning_lessons SET
                unit_number = 1,
                lesson_order = %s,
                level = 'foundation',
                category = 'character',
                title = %s,
                explanation = %s
            WHERE id = %s
        """, (order, title, expl, lid))

    # Mark legacy duplicate ID 55 as secondary introductory lesson
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 13, title = 'அறிமுகம் · தமிழ் உயிரெழுத்துக்கள் (Introduction to Vowels)' WHERE id = 55
    """)

    # Tamil Consonants (Foundation Unit 2: மெய்யெழுத்து - வல்லினம் Hard Stops)
    tamil_consonants = [
        (tamil_id, 'character', 'foundation', 2, 1, 'மெய்யெழுத்து · க் (Hard consonant k)', 'க்', 'Hard consonant k with pulli', 'k', 'க் consists of the consonant base க with a superscript dot (புள்ளி / pulli) denoting the pure consonant sound.'),
        (tamil_id, 'character', 'foundation', 2, 2, 'மெய்யெழுத்து · ச் (Hard consonant c)', 'ச்', 'Hard consonant c with pulli', 'c', 'ச் consists of base ச with a pulli dot, pronounced like soft ch.'),
        (tamil_id, 'character', 'foundation', 2, 3, 'மெய்யெழுத்து · ட் (Hard retroflex ṭ)', 'ட்', 'Hard retroflex ṭ with pulli', 'ṭ', 'ட் consists of the retroflex base ட with a pulli dot.'),
        (tamil_id, 'character', 'foundation', 2, 4, 'மெய்யெழுத்து · த் (Hard dental t)', 'த்', 'Hard dental t with pulli', 't', 'த் consists of the dental base த with a pulli dot.'),
        (tamil_id, 'character', 'foundation', 2, 5, 'மெய்யெழுத்து · ப் (Hard labial p)', 'ப்', 'Hard labial p with pulli', 'p', 'ப் consists of the labial base ப with a pulli dot.')
    ]
    for row in tamil_consonants:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Tamil consonant lesson: {row[5]}")

    # Tamil Combinations (Foundation Unit 3: உயிர்மெய்யெழுத்து - க-வரிசை)
    tamil_combinations = [
        (tamil_id, 'character', 'foundation', 3, 1, 'உயிர்மெய் · க (ka = க் + அ)', 'க', 'Consonant-vowel combination ka', 'ka', 'Formed by combining the pure consonant க் with short vowel அ.'),
        (tamil_id, 'character', 'foundation', 3, 2, 'உயிர்மெய் · கா (kaa = க் + ஆ)', 'கா', 'Consonant-vowel combination kaa', 'kaa', 'Formed by combining க் with long vowel ஆ, adding the auxiliary கால் (kaal).'),
        (tamil_id, 'character', 'foundation', 3, 3, 'உயிர்மெய் · கி (ki = க் + இ)', 'கி', 'Consonant-vowel combination ki', 'ki', 'Formed by combining க் with short vowel இ, adding an upper arched hook.'),
        (tamil_id, 'character', 'foundation', 3, 4, 'உயிர்மெய் · கீ (kee = க் + ஈ)', 'கீ', 'Consonant-vowel combination kee', 'kee', 'Formed by combining க் with long vowel ஈ, adding a looped upper hook.')
    ]
    for row in tamil_combinations:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Tamil combination lesson: {row[5]}")

    # Tamil Words (Beginner Unit 1)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 1, title = 'சொல் · வணக்கம் (Hello / Greetings)' WHERE id = 353
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 2, title = 'சொல் · நன்றி (Thank you)' WHERE id = 354
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 3, title = 'சொல் · புத்தகம் (Book)' WHERE id = 355
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 4, title = 'சொல் · தண்ணீர் (Water)' WHERE id = 356
    """)

    # Tamil Sentences (Beginner Unit 2)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 1, title = 'வாக்கியம் · நான் தண்ணீர் குடிக்கிறேன்' WHERE id = 302
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 2, lesson_order = 2, title = 'வாக்கியம் · தயவுசெய்து தண்ணீர் தாருங்கள்' WHERE id = 301
    """)

    # ------------------------------------------------------------------------
    # CHINESE LESSONS REORGANIZATION
    # ------------------------------------------------------------------------
    print("\n--- Reorganizing Simplified Chinese Curriculum (zh-hans) ---")

    # Update Foundation Unit 1: 基础汉字 (Basic Foundational Characters)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 1, title = '基础汉字 · 一 (Number One)', explanation = '一 consists of a single horizontal stroke (横 héng) written firmly from left to right.' WHERE id = 348
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 2, title = '基础汉字 · 二 (Number Two)', explanation = '二 consists of two horizontal strokes: shorter top stroke and longer base stroke.' WHERE id = 349
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 3, title = '基础汉字 · 三 (Number Three)', explanation = '三 consists of three horizontal strokes: top, middle (shortest), and bottom (longest).' WHERE id = 350
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 4, title = '基础汉字 · 人 (Person / Human)', explanation = '人 consists of a left-falling stroke (撇 piě) and a right-falling stroke (捺 nà).' WHERE id = 351
    """)
    cursor.execute("""
        UPDATE learning_lessons SET unit_number = 1, lesson_order = 5, title = '基础汉字 · 大 (Big / Great)', explanation = '大 consists of horizontal stroke (一), piercing left-falling stroke (撇), and right-falling stroke (捺).' WHERE id = 352
    """)

    # Foundation Unit 2: 常用独体字与部首 (Radicals & Basic Characters)
    chinese_unit2 = [
        (chinese_id, 'character', 'foundation', 2, 1, '部首与字 · 口 (Mouth / Opening)', '口', 'Mouth / Opening radical', 'kǒu', '口 is a fundamental three-stroke enclosed character and vital radical in Chinese writing.'),
        (chinese_id, 'character', 'foundation', 2, 2, '部首与字 · 日 (Sun / Day)', '日', 'Sun / Day radical', 'rì', '日 represents the sun and calendar days, formed by an outer enclosure and middle horizontal bar.'),
        (chinese_id, 'character', 'foundation', 2, 3, '部首与字 · 月 (Moon / Month)', '月', 'Moon / Month radical', 'yuè', '月 represents the moon and months, formed by four balanced strokes.'),
        (chinese_id, 'character', 'foundation', 2, 4, '部首与字 · 山 (Mountain)', '山', 'Mountain radical', 'shān', '山 is a pictographic character depicting mountain peaks, with a central tall vertical stroke.')
    ]
    for row in chinese_unit2:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Chinese radical/character lesson: {row[5]}")

    # Chinese Vocabulary (Beginner Unit 1)
    chinese_vocab = [
        (chinese_id, 'word', 'beginner', 1, 1, '常用词汇 · 你好 (Hello)', '你好', 'Hello / Greeting', 'nǐ hǎo', 'The most common Chinese greeting, combining 你 (you) and 好 (good).'),
        (chinese_id, 'word', 'beginner', 1, 2, '常用词汇 · 谢谢 (Thank you)', '谢谢', 'Thank you / Gratitude', 'xièxie', 'Standard expression of gratitude, doubling the character 谢.'),
        (chinese_id, 'word', 'beginner', 1, 3, '常用词汇 · 朋友 (Friend)', '朋友', 'Friend / Companion', 'péngyou', 'Common compound noun combining 朋 and 友.')
    ]
    for row in chinese_vocab:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Chinese vocabulary lesson: {row[5]}")

    # Chinese Sentences (Beginner Unit 2)
    chinese_sentences = [
        (chinese_id, 'sentence', 'beginner', 2, 1, '基础句型 · 你好吗？ (How are you?)', '你好吗？', 'How are you?', 'nǐ hǎo ma?', 'Question form formed by greeting 你好 with interrogative particle 吗 (ma).'),
        (chinese_id, 'sentence', 'beginner', 2, 2, '基础句型 · 我是学生。 (I am a student.)', '我是学生。', 'I am a student.', 'wǒ shì xuésheng.', 'Subject-verb-object declarative structure: 我 (I) + 是 (am) + 学生 (student).')
    ]
    for row in chinese_sentences:
        cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND content_text = %s", (row[0], row[6]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO learning_lessons (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
            print(f"  + Added Chinese sentence lesson: {row[5]}")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n [PASS] Curriculum reorganization completed successfully across Sanskrit, Tamil, and Chinese!")


if __name__ == "__main__":
    reorganize_curriculum()
