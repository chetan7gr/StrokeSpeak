
from app.db.database import get_db_connection

def create_tables():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                script_code VARCHAR(20) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                language_id INT NOT NULL,
                character_text VARCHAR(50) NOT NULL,
                meaning VARCHAR(255),
                pronunciation_text VARCHAR(255),
                reference_strokes JSON NULL,
                FOREIGN KEY (language_id)
                    REFERENCES languages(id),
                UNIQUE (language_id, character_text)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_lessons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                language_id INT NOT NULL,
                category ENUM('character', 'word', 'sentence', 'grammar') NOT NULL,
                level ENUM('foundation', 'beginner', 'elementary', 'intermediate', 'advanced')
                    NOT NULL DEFAULT 'foundation',
                unit_number INT NOT NULL DEFAULT 1,
                lesson_order INT NOT NULL DEFAULT 1,
                tutorial_video_url VARCHAR(500) NULL,
                tutorial_video_status ENUM('not_started','processing','ready','failed') NOT NULL DEFAULT 'not_started',
                title VARCHAR(120) NOT NULL,
                content_text TEXT NOT NULL,
                translation_text VARCHAR(255),
                pronunciation_text VARCHAR(255),
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (language_id) REFERENCES languages(id),
                UNIQUE (language_id, title)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                lesson_id INT NOT NULL,
                status ENUM('not_started','in_progress','completed') NOT NULL DEFAULT 'in_progress',
                score DECIMAL(5,2) NULL,
                completed_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_lesson_progress_user_lesson (user_id, lesson_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (lesson_id) REFERENCES learning_lessons(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS practice_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                character_id INT NOT NULL,
                handwriting_score DECIMAL(5,2),
                stroke_order_score DECIMAL(5,2),
                pronunciation_score DECIMAL(5,2),
                feedback TEXT,
                stroke_data JSON NULL,
                audio_data MEDIUMBLOB NULL,
                audio_mime_type VARCHAR(100) NULL,
                pronunciation_status ENUM('not_submitted','pending_assessment','completed','failed') NOT NULL DEFAULT 'not_submitted',
                transcribed_text TEXT NULL,
                pronunciation_feedback TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (character_id) REFERENCES characters(id)
            )
        """)

        # Migrate older databases so every column used by the API exists.
        # CREATE TABLE IF NOT EXISTS does not add columns to existing tables.
        for table_name, column_name, column_sql in [
            ("characters", "reference_strokes", "JSON NULL"),
            ("practice_attempts", "stroke_data", "JSON NULL"),
            ("practice_attempts", "audio_data", "MEDIUMBLOB NULL"),
            ("practice_attempts", "audio_mime_type", "VARCHAR(100) NULL"),
            ("practice_attempts", "pronunciation_status", "ENUM('not_submitted','pending_assessment','completed','failed') NOT NULL DEFAULT 'not_submitted'"),
            ("practice_attempts", "transcribed_text", "TEXT NULL"),
            ("practice_attempts", "pronunciation_feedback", "TEXT NULL"),
            ("learning_lessons", "tutorial_video_url", "VARCHAR(500) NULL"),
            ("learning_lessons", "tutorial_video_status", "ENUM('not_started','processing','ready','failed') NOT NULL DEFAULT 'not_started'"),
        ]:
            cursor.execute("SHOW COLUMNS FROM " + table_name + " LIKE %s", (column_name,))
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE " + table_name + " ADD COLUMN " + column_name + " " + column_sql)
        # Allow character and sound lessons in an existing course table.
        cursor.execute("SHOW COLUMNS FROM learning_lessons LIKE 'category'")
        category_column = cursor.fetchone()
        if category_column and 'character' not in str(category_column[1]):
            cursor.execute("ALTER TABLE learning_lessons MODIFY COLUMN category ENUM('character','word','sentence','grammar') NOT NULL")

        # Upgrade existing lesson tables before inserting rows that use these columns.
        for column_name, column_sql in [
            ("level", "ENUM('foundation','beginner','elementary','intermediate','advanced') NOT NULL DEFAULT 'foundation'"),
            ("unit_number", "INT NOT NULL DEFAULT 1"),
            ("lesson_order", "INT NOT NULL DEFAULT 1"),
        ]:
            cursor.execute("SHOW COLUMNS FROM learning_lessons LIKE %s", (column_name,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "ALTER TABLE learning_lessons ADD COLUMN " + column_name + " " + column_sql
                )
        cursor.executemany(
            "INSERT IGNORE INTO languages (name, script_code) VALUES (%s, %s)",
            [("Korean", "ko"), ("Telugu", "te"), ("Tamil", "ta"), ("Malayalam", "ml"), ("Kannada", "kn")],
        )
        cursor.execute(
            "UPDATE languages SET name = %s WHERE script_code = %s",
            ("Hindi", "Deva"),
        )

        # Starter Hindi vowel and sound lessons begin the learning path.
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ('Deva',))
        devanagari_language = cursor.fetchone()
        if devanagari_language:
            devanagari_id = devanagari_language[0]
            vowel_lessons = [
                ('अ', 'a', 'Short a, as in अनार (pomegranate).'),
                ('आ', 'aa', 'Long aa, as in आम (mango).'),
                ('इ', 'i', 'Short i, as in इमली (tamarind).'),
                ('ई', 'ee', 'Long ee, as in ईख (sugarcane).'),
                ('उ', 'u', 'Short u, as in उल्लू (owl).'),
                ('ऊ', 'oo', 'Long oo, as in ऊन (wool).'),
                ('ए', 'e', 'Long e sound, as in एक (one).'),
                ('ऐ', 'ai', 'The ai vowel sound, as in ऐनक (glasses).'),
                ('ओ', 'o', 'Long o sound, as in ओस (dew).'),
                ('औ', 'au', 'The au vowel sound, as in और (and).'),
                ('ऋ', 'ri', 'A traditional Devanagari vowel, now uncommon in everyday Hindi words.'),
            ]
            for lesson_order, (letter, sound, explanation) in enumerate(vowel_lessons, start=1):
                cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (devanagari_id, letter))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (devanagari_id, letter, 'Hindi vowel', sound))
                else:
                    cursor.execute("UPDATE characters SET meaning = %s, pronunciation_text = %s WHERE language_id = %s AND character_text = %s", ('Hindi vowel', sound, devanagari_id, letter))
                title = 'Vowel ' + letter + ' and its sound'
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (devanagari_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 1, %s)", (devanagari_id, title, letter, 'Hindi vowel', sound, explanation, lesson_order))

        # Add one first-letter and greeting starter for each requested language.
        south_indian_starters = [
            ("te", "అ", "a", "Telugu greeting", "నమస్కారం", "namaskaram"),
            ("ta", "அ", "a", "Tamil greeting", "வணக்கம்", "vanakkam"),
            ("ml", "അ", "a", "Malayalam greeting", "നമസ്കാരം", "namaskaram"),
            ("kn", "ಅ", "a", "Kannada greeting", "ನಮಸ್ಕಾರ", "namaskara"),
        ]
        for script_code, letter, sound, greeting_title, greeting, greeting_sound in south_indian_starters:
            cursor.execute("SELECT id FROM languages WHERE script_code = %s", (script_code,))
            language_row = cursor.fetchone()
            if not language_row:
                continue
            language_id = language_row[0]
            cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (language_id, letter))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (language_id, letter, 'Starter vowel', sound))
            for category, title, content, translation, pronunciation, explanation, unit in [
                ('character', 'First vowel ' + letter, letter, 'First independent vowel', sound, 'Starter letter for this language. More script-specific lessons will follow.', 1),
                ('word', greeting_title, greeting, 'Hello / greeting', greeting_sound, 'A common polite greeting.', 2),
            ]:
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (language_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, %s, %s, %s, %s, %s, %s, 'foundation', %s, 1)", (language_id, category, title, content, translation, pronunciation, explanation, unit))

        # Add complete starter-vowel rows for the requested South Indian scripts.
        south_script_vowels = {
            "te": [("అ","a"),("ఆ","aa"),("ఇ","i"),("ఈ","ii"),("ఉ","u"),("ఊ","uu"),("ఋ","ru"),("ఎ","e"),("ఏ","ee"),("ఐ","ai"),("ఒ","o"),("ఓ","oo"),("ఔ","au")],
            "ta": [("அ","a"),("ஆ","aa"),("இ","i"),("ஈ","ii"),("உ","u"),("ஊ","uu"),("எ","e"),("ஏ","ee"),("ஐ","ai"),("ஒ","o"),("ஓ","oo"),("ஔ","au")],
            "ml": [("അ","a"),("ആ","aa"),("ഇ","i"),("ഈ","ii"),("ഉ","u"),("ഊ","uu"),("ഋ","ru"),("എ","e"),("ഏ","ee"),("ഐ","ai"),("ഒ","o"),("ഓ","oo"),("ഔ","au")],
            "kn": [("ಅ","a"),("ಆ","aa"),("ಇ","i"),("ಈ","ii"),("ಉ","u"),("ಊ","uu"),("ಋ","ru"),("ಎ","e"),("ಏ","ee"),("ಐ","ai"),("ಒ","o"),("ಓ","oo"),("ಔ","au")],
        }
        for script_code, vowel_rows in south_script_vowels.items():
            cursor.execute("SELECT id FROM languages WHERE script_code = %s", (script_code,))
            language_row = cursor.fetchone()
            if not language_row:
                continue
            language_id = language_row[0]
            for lesson_order, (letter, sound) in enumerate(vowel_rows, start=1):
                cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (language_id, letter))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (language_id, letter, "Independent vowel", sound))
                title = "Vowel " + letter + " and its sound"
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (language_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("""INSERT INTO learning_lessons
                        (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order)
                        VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 1, %s)""",
                        (language_id, title, letter, "Independent vowel", sound, "Listen to the vowel sound, then practise writing the letter.", lesson_order))

        # Teach Hangul jamo before learners combine them into syllable blocks.
        hangul_jamo = [("ㄱ","g/k"),("ㄴ","n"),("ㄷ","d/t"),("ㄹ","r/l"),("ㅁ","m"),("ㅂ","b/p"),("ㅅ","s"),("ㅇ","ng"),("ㅈ","j"),("ㅊ","ch"),("ㅋ","k"),("ㅌ","t"),("ㅍ","p"),("ㅎ","h"),("ㅏ","a"),("ㅑ","ya"),("ㅓ","eo"),("ㅕ","yeo"),("ㅗ","o"),("ㅛ","yo"),("ㅜ","u"),("ㅠ","yu"),("ㅡ","eu"),("ㅣ","i")]
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ("ko",))
        korean_row = cursor.fetchone()
        if korean_row:
            korean_id = korean_row[0]
            for lesson_order, (letter, sound) in enumerate(hangul_jamo, start=1):
                cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (korean_id, letter))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (korean_id, letter, "Hangul jamo", sound))
                title = "Hangul sound " + letter
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (korean_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("""INSERT INTO learning_lessons
                        (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order)
                        VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 1, %s)""",
                        (korean_id, title, letter, "Hangul jamo", sound, "Learn this consonant or vowel before combining jamo into a Korean syllable block.", lesson_order))

        # Seven-stage starter path for Japanese, Korean, Telugu, Tamil, Malayalam, and Kannada.
        additional_script_lessons = [
            ("ja-hiragana","character","Sound contrast: か and が","か / が","ka / ga","ka / ga","が adds voicing to か. Listen for the difference.","foundation"),
            ("ja-hiragana","word","Phrase practice: coffee please","コーヒーをください。","Coffee, please.","koohii o kudasai","ください is a polite way to request something.","foundation"),
            ("ja-hiragana","sentence","Sentence practice: I read a book","わたしは ほんを よみます。","I read a book.","watashi wa hon o yomimasu","The particle を marks the object in this polite sentence.","beginner"),
            ("ja-hiragana","grammar","Tense practice: read and read-past","よみます → よみました","read / will read → read (past)","yomimasu → yomimashita","ました marks the polite past form.","elementary"),
            ("ja-hiragana","grammar","Dialogue: greeting and request","こんにちは。みずをください。","Hello. Water, please.","konnichiwa. mizu o kudasai","Practise the greeting and the polite request together.","advanced"),
            ("ko","character","Sound contrast: 가 and 나","가 / 나","ga / na","ga / na","Compare the initial consonants ㄱ and ㄴ.","foundation"),
            ("ko","word","Phrase practice: please give water","물 주세요.","Water, please.","mul juseyo","주세요 makes this a polite request.","foundation"),
            ("ko","sentence","Sentence practice: I read a book","저는 책을 읽어요.","I read a book.","jeoneun chaegeul ilgeoyo","을 marks the object in this polite sentence.","beginner"),
            ("ko","grammar","Tense practice: drink","마셔요 → 마셨어요 → 마실 거예요","drink → drank → will drink","masyeoyo → masyeosseoyo → masil geoyeyo","Compare the present, past, and future polite forms.","elementary"),
            ("ko","grammar","Dialogue: greeting and request","안녕하세요. 물 주세요.","Hello. Water, please.","annyeonghaseyo. mul juseyo","Use a polite greeting followed by a polite request.","advanced"),
            ("te","character","Sound contrast: అ and ఆ","అ / ఆ","short a / long aa","a / aa","Compare the short and long vowel sounds.","foundation"),
            ("te","word","Phrase practice: please give water","దయచేసి నీరు ఇవ్వండి.","Please give water.","dayachesi neeru ivvandi","A polite request using దయచేసి (please).","foundation"),
            ("te","sentence","Sentence practice: I drink water","నేను నీరు తాగుతాను.","I drink water.","nenu neeru tagutanu","నేను means I; నీరు means water.","beginner"),
            ("te","grammar","Tense practice: drink","తాగుతున్నాను → తాగాను → తాగుతాను","am drinking → drank → drink / will drink","tagutunnanu → taganu → tagutanu","Compare common present-progressive, past, and habitual/future forms.","elementary"),
            ("te","grammar","Dialogue: greeting and request","నమస్కారం. దయచేసి నీరు ఇవ్వండి.","Hello. Please give water.","namaskaram. dayachesi neeru ivvandi","Practise a greeting and polite request.","advanced"),
            ("ta","character","Sound contrast: அ and ஆ","அ / ஆ","short a / long aa","a / aa","Compare the short and long vowel sounds.","foundation"),
            ("ta","word","Phrase practice: please give water","தயவுசெய்து தண்ணீர் தாருங்கள்.","Please give water.","thayavuseythu thanneer thaarungal","A polite request for water.","foundation"),
            ("ta","sentence","Sentence practice: I drink water","நான் தண்ணீர் குடிக்கிறேன்.","I drink water.","naan thanneer kudikkiren","நான் means I; தண்ணீர் means water.","beginner"),
            ("ta","grammar","Tense practice: drink","குடிக்கிறேன் → குடித்தேன் → குடிப்பேன்","drink (present) → drank → will drink","kudikkiren → kudithen → kudippen","Compare present, past, and future forms.","elementary"),
            ("ta","grammar","Dialogue: greeting and request","வணக்கம். தயவுசெய்து தண்ணீர் தாருங்கள்.","Hello. Please give water.","vanakkam. thayavuseythu thanneer thaarungal","Practise a greeting and polite request.","advanced"),
            ("ml","character","Sound contrast: അ and ആ","അ / ആ","short a / long aa","a / aa","Compare the short and long vowel sounds.","foundation"),
            ("ml","word","Phrase practice: please give water","ദയവായി വെള്ളം തരൂ.","Please give water.","dayavaayi vellam tharoo","A polite request for water.","foundation"),
            ("ml","sentence","Sentence practice: I drink water","ഞാൻ വെള്ളം കുടിക്കുന്നു.","I drink water.","njan vellam kudikkunnu","ഞാൻ means I; വെള്ളം means water.","beginner"),
            ("ml","grammar","Tense practice: drink","കുടിക്കുന്നു → കുടിച്ചു → കുടിക്കും","drink (present) → drank → will drink","kudikkunnu → kudichu → kudikkum","Compare present, past, and future forms.","elementary"),
            ("ml","grammar","Dialogue: greeting and request","നമസ്കാരം. ദയവായി വെള്ളം തരൂ.","Hello. Please give water.","namaskaram. dayavaayi vellam tharoo","Practise a greeting and polite request.","advanced"),
            ("kn","character","Sound contrast: ಅ and ಆ","ಅ / ಆ","short a / long aa","a / aa","Compare the short and long vowel sounds.","foundation"),
            ("kn","word","Phrase practice: please give water","ದಯವಿಟ್ಟು ನೀರು ಕೊಡಿ.","Please give water.","dayavittu neeru kodi","A polite request for water.","foundation"),
            ("kn","sentence","Sentence practice: I drink water","ನಾನು ನೀರು ಕುಡಿಯುತ್ತೇನೆ.","I drink water.","naanu neeru kudiyuttene","ನಾನು means I; ನೀರು means water.","beginner"),
            ("kn","grammar","Tense practice: drink","ಕುಡಿಯುತ್ತೇನೆ → ಕುಡಿದೆ → ಕುಡಿಯುವೆ","drink (present) → drank → will drink","kudiyuttene → kudide → kudiyuve","Compare present, past, and future forms.","elementary"),
            ("kn","grammar","Dialogue: greeting and request","ನಮಸ್ಕಾರ. ದಯವಿಟ್ಟು ನೀರು ಕೊಡಿ.","Hello. Please give water.","namaskara. dayavittu neeru kodi","Practise a greeting and polite request.","advanced"),
        ]
        for script_code, category, title, content, translation, pronunciation, explanation, level in additional_script_lessons:
            cursor.execute("SELECT id FROM languages WHERE script_code = %s", (script_code,))
            language_row = cursor.fetchone()
            if not language_row:
                continue
            language_id = language_row[0]
            cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (language_id, title))
            if cursor.fetchone() is None:
                cursor.execute("""INSERT INTO learning_lessons
                    (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 1)""",
                    (language_id, category, title, content, translation, pronunciation, explanation, level))
        # A small starter library with words, sentences, and grammar examples.
        starter_lessons = {
            "Deva": [
                ("word", "Water", "पानी", "Water", "paani", "A common Hindi word for water."),
                ("word", "Hello", "नमस्ते", "Hello / greetings", "namaste", "A polite Hindi greeting."),
                ("sentence", "I drink water", "मैं पानी पीता हूँ।", "I drink water (masculine speaker)", "main paani peeta hoon", "For a feminine speaker, say: मैं पानी पीती हूँ।"),
                ("grammar", "Hindi habitual present", "मैं पढ़ता हूँ। / मैं पढ़ती हूँ।", "I read / I study.", "main padhta hoon / main padhti hoon", "The verb ending changes with the speaker's gender in this example."),
            ],
            "ja-hiragana": [
                ("word", "Water", "みず", "Water", "mizu", "A basic Japanese word written here in Hiragana."),
                ("word", "Hello", "こんにちは", "Hello", "konnichiwa", "A common daytime greeting."),
                ("sentence", "I drink water", "わたしは みずを のみます。", "I drink water.", "watashi wa mizu o nomimasu", "A beginner polite sentence."),
                ("grammar", "Polite non-past and past", "のみます → のみました", "drink / will drink → drank", "nomimasu → nomimashita", "In polite Japanese, ます is non-past and ました is past."),
            ],
            "ko": [
                ("word", "Water", "물", "Water", "mul", "The basic Korean word for water."),
                ("word", "Hello", "안녕하세요", "Hello", "annyeonghaseyo", "A polite Korean greeting."),
                ("sentence", "I drink water", "저는 물을 마셔요.", "I drink water.", "jeoneun mureul masyeoyo", "A common polite conversational sentence."),
                ("grammar", "Present, past, and future", "마셔요 → 마셨어요 → 마실 거예요", "drink → drank → will drink", "masyeoyo → masyeosseoyo → masil geoyeyo", "A beginner comparison of three polite verb forms."),
            ],
        }

        for script_code, lessons in starter_lessons.items():
            cursor.execute("SELECT id FROM languages WHERE script_code = %s", (script_code,))
            language_row = cursor.fetchone()
            if language_row:
                for lesson_order, (category, title, content, translation, pronunciation, explanation) in enumerate(lessons, start=1):
                    cursor.execute(
                        "SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s",
                        (language_row[0], title),
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """
                            INSERT INTO learning_lessons
                                (language_id, category, title, content_text, translation_text,
                                 pronunciation_text, explanation, level, unit_number, lesson_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                language_row[0], category, title, content, translation,
                                pronunciation, explanation,
                                "foundation" if category == "word" else "beginner" if category == "sentence" else "elementary",
                                1 if category == "word" else 2 if category == "sentence" else 3,
                                lesson_order,
                            ),
                        )
        # Keep both Japanese kana systems inside one Japanese tutor.
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ("ja-hiragana",))
        japanese_language = cursor.fetchone()
        if japanese_language:
            japanese_id = japanese_language[0]
            cursor.execute("UPDATE languages SET name = %s WHERE id = %s", ("Japanese", japanese_id))
            kana_sets = {
                "Hiragana": [
                    ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
                    ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
                    ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
                    ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
                    ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
                    ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
                    ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
                    ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
                    ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
                    ("わ", "wa"), ("を", "o"), ("ん", "n"),
                ],
                "Katakana": [
                    ("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o"),
                    ("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko"),
                    ("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so"),
                    ("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to"),
                    ("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no"),
                    ("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho"),
                    ("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo"),
                    ("ヤ", "ya"), ("ユ", "yu"), ("ヨ", "yo"),
                    ("ラ", "ra"), ("リ", "ri"), ("ル", "ru"), ("レ", "re"), ("ロ", "ro"),
                    ("ワ", "wa"), ("ヲ", "o"), ("ン", "n"),
                ],
            }
            for kana_type, kana_rows in kana_sets.items():
                for lesson_order, (letter, sound) in enumerate(kana_rows, start=1):
                    cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (japanese_id, letter))
                    if cursor.fetchone() is None:
                        cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (japanese_id, letter, "Japanese " + kana_type + " character", sound))
                    else:
                        cursor.execute("UPDATE characters SET meaning = %s, pronunciation_text = %s WHERE language_id = %s AND character_text = %s", ("Japanese " + kana_type + " character", sound, japanese_id, letter))
                    title = kana_type + " " + letter + " and its sound"
                    cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (japanese_id, title))
                    if cursor.fetchone() is None:
                        cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 1, %s)", (japanese_id, title, letter, kana_type + " character", sound, "Learn the sound, then practise writing this " + kana_type + " character.", lesson_order))

            katakana_words = [
                ("Katakana word: coffee", "コーヒー", "coffee", "koohii"),
                ("Katakana word: camera", "カメラ", "camera", "kamera"),
                ("Katakana word: hotel", "ホテル", "hotel", "hoteru"),
            ]
            for lesson_order, (title, content, translation, pronunciation) in enumerate(katakana_words, start=1):
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (japanese_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, 'word', %s, %s, %s, %s, %s, 'foundation', 2, %s)", (japanese_id, title, content, translation, pronunciation, "Katakana is commonly used for loanwords and borrowed terms.", lesson_order))

        # Complete the first seven-stage Hindi course path. Inserts are safe to rerun.
        if devanagari_language:
            devanagari_id = devanagari_language[0]
            consonants = [
                ('क', 'ka'), ('ख', 'kha'), ('ग', 'ga'), ('घ', 'gha'), ('ङ', 'nga'),
                ('च', 'cha'), ('छ', 'chha'), ('ज', 'ja'), ('झ', 'jha'), ('ञ', 'nya'),
                ('ट', 'ta'), ('ठ', 'tha'), ('ड', 'da'), ('ढ', 'dha'), ('ण', 'na'),
                ('त', 'ta'), ('थ', 'tha'), ('द', 'da'), ('ध', 'dha'), ('न', 'na'),
                ('प', 'pa'), ('फ', 'pha'), ('ब', 'ba'), ('भ', 'bha'), ('म', 'ma'),
                ('य', 'ya'), ('र', 'ra'), ('ल', 'la'), ('व', 'va'),
                ('श', 'sha'), ('ष', 'sha'), ('स', 'sa'), ('ह', 'ha'),
            ]
            for letter, sound in consonants:
                cursor.execute("SELECT id FROM characters WHERE language_id = %s AND character_text = %s", (devanagari_id, letter))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) VALUES (%s, %s, %s, %s)", (devanagari_id, letter, 'Hindi consonant', sound))
                title = 'Consonant ' + letter + ' and its sound'
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (devanagari_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 4, %s)", (devanagari_id, title, letter, 'Hindi consonant', sound, 'Say the consonant with its natural short a sound, then practise drawing it.', len(consonants)))

            next_lessons = [
                # Stage 3: recognise familiar words containing vowel sounds.
                (3, 'word', 'Vowel word: अनार', 'अनार', 'Pomegranate', 'anaar', 'Notice the opening अ sound. This is whole-word recognition; more consonants are introduced in the next stage.', 'foundation'),
                (3, 'word', 'Vowel word: आम', 'आम', 'Mango', 'aam', 'The first sound is the long आ vowel.', 'foundation'),
                (3, 'word', 'Vowel word: इमली', 'इमली', 'Tamarind', 'imli', 'Listen for the short इ sound at the beginning.', 'foundation'),
                (3, 'word', 'Vowel word: ईख', 'ईख', 'Sugarcane', 'eekh', 'The first sound is the long ई vowel.', 'foundation'),
                (3, 'word', 'Vowel word: उल्लू', 'उल्लू', 'Owl', 'ullu', 'The first sound is the short उ vowel.', 'foundation'),
                (3, 'word', 'Vowel word: ऊन', 'ऊन', 'Wool', 'oon', 'The first sound is the long ऊ vowel.', 'foundation'),
                # Stage 4: combine consonants with dependent vowel signs (matras).
                (4, 'word', 'Vowel sign: ा (aa)', 'क + ा = का', 'The consonant ka becomes kaa.', 'kaa', 'ा follows a consonant and lengthens the inherent a sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ि (i)', 'क + ि = कि', 'The consonant ka becomes ki.', 'ki', 'ि is written before the consonant visually, but pronounced after it.', 'foundation'),
                (4, 'word', 'Vowel sign: ी (ii)', 'क + ी = की', 'The consonant ka becomes kee.', 'kii', 'ी follows the consonant and makes a long ee sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ु (u)', 'क + ु = कु', 'The consonant ka becomes ku.', 'ku', 'ु is written below a consonant and makes a short u sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ू (uu)', 'क + ू = कू', 'The consonant ka becomes koo.', 'kuu', 'ू is written below a consonant and makes a long oo sound.', 'foundation'),
                (4, 'word', 'Vowel sign: े (e)', 'क + े = के', 'The consonant ka becomes ke.', 'ke', 'े follows the consonant and makes an e sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ै (ai)', 'क + ै = कै', 'The consonant ka becomes kai.', 'kai', 'ै follows the consonant and makes an ai sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ो (o)', 'क + ो = को', 'The consonant ka becomes ko.', 'ko', 'ो follows the consonant and makes an o sound.', 'foundation'),
                (4, 'word', 'Vowel sign: ौ (au)', 'क + ौ = कौ', 'The consonant ka becomes kau.', 'kau', 'ौ follows the consonant and makes an au sound.', 'foundation'),
                # Stage 5: join known consonants and learn the long-aa vowel sign.
                (5, 'word', 'Build a word: कम', 'क + म = कम', 'kam (less)', 'kam', 'Each consonant carries a natural short a sound when no vowel sign is written.', 'foundation'),
                (5, 'word', 'Build a word: मन', 'म + न = मन', 'man (mind)', 'man', 'Read from left to right and say each sound smoothly.', 'foundation'),
                (5, 'word', 'Build a word: काम', 'क + ा + म = काम', 'kaam (work)', 'kaam', 'The mark ा after क changes ka to kaa. This is the long-aa vowel sign.', 'foundation'),
                (5, 'word', 'Build a word: नाम', 'न + ा + म = नाम', 'naam (name)', 'naam', 'Use the same ा sign to make naa, then add म.', 'foundation'),
                (5, 'word', 'Build a word: काम', 'काम', 'Work', 'kaam', 'Read क with the ा sign as kaa, then add म.', 'foundation'),
                (5, 'word', 'Build a word: किताब', 'किताब', 'Book', 'kitaab', 'Notice ि before त and ा after ब in the written word.', 'foundation'),
                (5, 'word', 'Build a word: पानी', 'पानी', 'Water', 'paani', 'Read पा with ा, then नी with ी.', 'foundation'),
                (5, 'word', 'Build a word: कमल', 'कमल', 'Lotus', 'kamal', 'Read each consonant with its natural vowel.', 'foundation'),
                # Stage 6: simple readable sentences with taught letters and sounds.
                (6, 'sentence', 'Sentence: यह नल है।', 'यह नल है।', 'This is a tap.', 'yah nal hai', 'Read each word in order: यह (this), नल (tap), है (is).', 'beginner'),
                (6, 'sentence', 'Sentence: राम आता है।', 'राम आता है।', 'Ram comes.', 'raam aataa hai', 'आ is written with the ा sign after a consonant: रा and ता.', 'beginner'),
                (6, 'sentence', 'Sentence: राम का नाम।', 'राम का नाम।', 'Ram’s name.', 'raam kaa naam', 'का and ना use the long-aa vowel sign. This is a short reading phrase.', 'beginner'),
                (6, 'sentence', 'Sentence: सीता आम खाती है।', 'सीता आम खाती है।', 'Sita eats a mango.', 'seeta aam khaati hai', 'Read the subject, object, then the verb at the end.', 'beginner'),
                (6, 'sentence', 'Sentence: यह किताब नई है।', 'यह किताब नई है।', 'This book is new.', 'yah kitaab nayee hai', 'नई uses the long ee vowel sign in the final syllable.', 'beginner'),
                (6, 'sentence', 'Sentence: बच्चे पानी पीते हैं।', 'बच्चे पानी पीते हैं।', 'The children drink water.', 'bachche paani peete hain', 'Notice the plural verb पीते हैं with बच्चे.', 'beginner'),
                # Stage 7: introduce useful grammar after the reading examples.
                (7, 'grammar', 'Hindi sentence order', 'कर्ता + कर्म + क्रिया', 'subject + object + verb', 'karta + karma + kriya', 'Hindi commonly places the verb at the end. Example: राम आम खाता है। (Ram eats a mango.)', 'elementary'),
                (7, 'grammar', 'Using है and हैं', 'यह नल है। / वे लोग हैं।', 'This is a tap. / They are people.', 'hai / hain', 'है is commonly used with one subject; हैं is used with plural or respectful subjects.', 'elementary'),
                (7, 'grammar', 'Present habitual: masculine and feminine', 'राम पढ़ता है। / सीता पढ़ती है।', 'Ram studies. / Sita studies.', 'padhta hai / padhti hai', 'In these examples, the verb ending agrees with the subject’s gender.', 'elementary'),
                (7, 'grammar', 'Simple past tense', 'राम आया।', 'Ram came.', 'raam aayaa', 'आया describes a completed past action in this example.', 'elementary'),
                (7, 'grammar', 'Simple future tense', 'राम आएगा।', 'Ram will come.', 'raam aayegaa', 'एगा marks a masculine singular future form in this example.', 'elementary'),
                (7, 'grammar', 'Pronouns: मैं and तुम', 'मैं पढ़ता हूँ। / तुम पढ़ते हो।', 'I study. / You study.', 'main padhta hoon / tum padhte ho', 'मैं means I; तुम is an informal or familiar you.', 'elementary'),
                (7, 'grammar', 'Plural nouns and agreement', 'लड़का → लड़के', 'boy → boys', 'ladka → ladke', 'Many masculine nouns ending in ा change to े in the plural; forms vary by sentence role.', 'elementary'),
                (7, 'grammar', 'Postposition में', 'किताब मेज़ पर है।', 'The book is on the table.', 'kitaab mez par hai', 'Hindi uses postpositions after the noun they relate to.', 'elementary'),
            ]
            for step, category, title, content, translation, pronunciation, explanation, level in next_lessons:
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (devanagari_id, title))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO learning_lessons (language_id, category, title, content_text, translation_text, pronunciation_text, explanation, level, unit_number, lesson_order) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (devanagari_id, category, title, content, translation, pronunciation, explanation, level, step, 1))

        # Intermediate and advanced Hindi sentence/grammar lessons complete the level path.
        if devanagari_language:
            devanagari_id = devanagari_language[0]
            higher_level_lessons = [
                ('sentence', 'Intermediate: progressive aspect', 'सीता खाना बना रही है।', 'Sita is cooking food.', 'seeta khaana banaa rahi hai', 'रही है marks a feminine singular ongoing action in this example.', 'intermediate'),
                ('sentence', 'Intermediate: habitual past', 'वह रोज़ पढ़ता था।', 'He used to study every day.', 'vah roz padhta tha', 'था combines with a verb to describe a masculine singular habitual past action here.', 'intermediate'),
                ('sentence', 'Intermediate: future plural', 'हम कल आएँगे।', 'We will come tomorrow.', 'ham kal aayenge', 'आएँगे is a polite or plural future verb form.', 'intermediate'),
                ('grammar', 'Intermediate: postpositional phrases', 'बच्चों के लिए किताबें', 'Books for children.', 'bachchon ke liye kitaaben', 'के लिए follows the noun phrase and means for.', 'intermediate'),
                ('sentence', 'Intermediate: compound verb', 'उसने काम कर लिया।', 'He completed the work.', 'usne kaam kar liya', 'कर लिया combines the main verb with लेना to show a completed action.', 'intermediate'),
                ('sentence', 'Advanced: perfect agreement', 'सीता ने किताब पढ़ी है।', 'Sita has read a book.', 'seeta ne kitaab padhee hai', 'In this perfective example, पढ़ी agrees with the feminine object किताब.', 'advanced'),
                ('sentence', 'Advanced: conditional sentence', 'अगर समय मिला, तो हम चलेंगे।', 'If we get time, then we will go.', 'agar samay mila to ham chalenge', 'अगर introduces a condition and तो introduces its result.', 'advanced'),
                ('sentence', 'Advanced: passive voice', 'पत्र शिक्षक द्वारा लिखा गया।', 'The letter was written by the teacher.', 'patra shikshak dvaara likha gaya', 'गया forms a passive construction in this example.', 'advanced'),
                ('sentence', 'Advanced: relative clause', 'जो विद्यार्थी अभ्यास करते हैं, वे सीखते हैं।', 'Students who practise learn.', 'jo vidyaarthi abhyaas karte hain ve seekhte hain', 'जो introduces the relative clause; वे refers back to those students.', 'advanced'),
                ('sentence', 'Advanced: reported speech', 'उसने कहा कि वह कल आएगा।', 'He said that he would come tomorrow.', 'usne kaha ki vah kal aayega', 'कि introduces the reported statement.', 'advanced'),
            ]
            for category, title, content, translation, pronunciation, explanation, level in higher_level_lessons:
                cursor.execute("SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s", (devanagari_id, title))
                if cursor.fetchone() is None:
                    cursor.execute(
                        """INSERT INTO learning_lessons
                            (language_id, category, title, content_text, translation_text,
                             pronunciation_text, explanation, level, unit_number, lesson_order)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 7, 1)""",
                        (devanagari_id, category, title, content, translation, pronunciation, explanation, level),
                    )
        # Add course-order columns for existing StrokeSpeak databases.
        for column_name, column_sql in [
            ("level", "ENUM('foundation','beginner','elementary','intermediate','advanced') NOT NULL DEFAULT 'foundation'"),
            ("unit_number", "INT NOT NULL DEFAULT 1"),
            ("lesson_order", "INT NOT NULL DEFAULT 1"),
        ]:
            cursor.execute("SHOW COLUMNS FROM learning_lessons LIKE %s", (column_name,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "ALTER TABLE learning_lessons ADD COLUMN " + column_name + " " + column_sql
                )

        # Organize the Hindi course into the seven agreed stages.
        cursor.execute("""
            UPDATE learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            SET
                ll.level = CASE
                    WHEN l.script_code = 'Deva' AND ll.title LIKE 'Intermediate:%' THEN 'intermediate'
                    WHEN l.script_code = 'Deva' AND ll.title LIKE 'Advanced:%' THEN 'advanced'
                    WHEN l.script_code = 'Deva' AND ll.category IN ('character', 'word') THEN 'foundation'
                    WHEN l.script_code = 'Deva' AND ll.category = 'sentence' THEN 'beginner'
                    WHEN l.script_code = 'Deva' THEN 'elementary'
                    WHEN ll.title LIKE 'Dialogue:%' THEN 'advanced'
                    WHEN ll.category IN ('character', 'word') THEN 'foundation'
                    WHEN ll.category = 'sentence' THEN 'beginner'
                    ELSE 'elementary'
                END,
                ll.unit_number = CASE
                    WHEN l.script_code = 'Deva' AND ll.category = 'character' AND ll.title LIKE 'Vowel %' THEN 1
                    WHEN l.script_code = 'Deva' AND ll.category = 'character' THEN 4
                    WHEN l.script_code = 'Deva' AND ll.category = 'word' AND ll.title LIKE 'Vowel sign:%' THEN 4
                    WHEN l.script_code = 'Deva' AND ll.category = 'word' AND ll.title LIKE 'Build a word:%' THEN 5
                    WHEN l.script_code = 'Deva' AND ll.category = 'word' THEN 3
                    WHEN l.script_code = 'Deva' AND ll.category = 'sentence' THEN 6
                    WHEN l.script_code = 'Deva' AND ll.category = 'grammar' THEN 7
                    WHEN ll.title LIKE 'Sound contrast:%' THEN 2
                    WHEN ll.title LIKE 'Phrase practice:%' THEN 4
                    WHEN ll.title LIKE 'Sentence practice:%' THEN 5
                    WHEN ll.title LIKE 'Tense practice:%' THEN 6
                    WHEN ll.title LIKE 'Dialogue:%' THEN 7
                    WHEN ll.category = 'character' THEN 1
                    WHEN ll.category = 'word' THEN 3
                    WHEN ll.category = 'sentence' THEN 5
                    ELSE 6
                END,
                ll.lesson_order = CASE
                    WHEN l.script_code = 'Deva' AND ll.category = 'character' AND ll.title LIKE 'Vowel %' THEN
                        CASE ll.content_text
                            WHEN 'अ' THEN 1 WHEN 'आ' THEN 2 WHEN 'इ' THEN 3 WHEN 'ई' THEN 4
                            WHEN 'उ' THEN 5 WHEN 'ऊ' THEN 6 WHEN 'ऋ' THEN 7 WHEN 'ए' THEN 8
                            WHEN 'ऐ' THEN 9 WHEN 'ओ' THEN 10 WHEN 'औ' THEN 11 ELSE 99 END
                    WHEN l.script_code = 'Deva' AND ll.category = 'character' AND ll.title LIKE 'Consonant %' THEN
                        CASE ll.content_text
                            WHEN 'क' THEN 1 WHEN 'ख' THEN 2 WHEN 'ग' THEN 3 WHEN 'घ' THEN 4 WHEN 'ङ' THEN 5
                            WHEN 'च' THEN 6 WHEN 'छ' THEN 7 WHEN 'ज' THEN 8 WHEN 'झ' THEN 9 WHEN 'ञ' THEN 10
                            WHEN 'ट' THEN 11 WHEN 'ठ' THEN 12 WHEN 'ड' THEN 13 WHEN 'ढ' THEN 14 WHEN 'ण' THEN 15
                            WHEN 'त' THEN 16 WHEN 'थ' THEN 17 WHEN 'द' THEN 18 WHEN 'ध' THEN 19 WHEN 'न' THEN 20
                            WHEN 'प' THEN 21 WHEN 'फ' THEN 22 WHEN 'ब' THEN 23 WHEN 'भ' THEN 24 WHEN 'म' THEN 25
                            WHEN 'य' THEN 26 WHEN 'र' THEN 27 WHEN 'ल' THEN 28 WHEN 'व' THEN 29
                            WHEN 'श' THEN 30 WHEN 'ष' THEN 31 WHEN 'स' THEN 32 WHEN 'ह' THEN 33 ELSE 99 END
                    WHEN l.script_code = 'Deva' AND ll.title LIKE 'Vowel sign:%' THEN
                        CASE ll.title
                            WHEN 'Vowel sign: ा (aa)' THEN 34 WHEN 'Vowel sign: ि (i)' THEN 35
                            WHEN 'Vowel sign: ी (ii)' THEN 36 WHEN 'Vowel sign: ु (u)' THEN 37
                            WHEN 'Vowel sign: ू (uu)' THEN 38 WHEN 'Vowel sign: े (e)' THEN 39
                            WHEN 'Vowel sign: ै (ai)' THEN 40 WHEN 'Vowel sign: ो (o)' THEN 41
                            WHEN 'Vowel sign: ौ (au)' THEN 42 ELSE 99 END
                    WHEN l.script_code = 'Deva' AND ll.title LIKE 'Vowel word:%' THEN
                        CASE ll.title
                            WHEN 'Vowel word: अनार' THEN 1 WHEN 'Vowel word: आम' THEN 2
                            WHEN 'Vowel word: इमली' THEN 3 WHEN 'Vowel word: ईख' THEN 4
                            WHEN 'Vowel word: उल्लू' THEN 5 WHEN 'Vowel word: ऊन' THEN 6 ELSE 99 END
                    WHEN l.script_code = 'Deva' AND ll.title LIKE 'Build a word:%' THEN
                        CASE ll.title
                            WHEN 'Build a word: कम' THEN 1 WHEN 'Build a word: मन' THEN 2
                            WHEN 'Build a word: काम' THEN 3 WHEN 'Build a word: नाम' THEN 4
                            WHEN 'Build a word: किताब' THEN 5 WHEN 'Build a word: पानी' THEN 6
                            WHEN 'Build a word: कमल' THEN 7 ELSE 99 END
                    ELSE ll.id
                END
        """)
        connection.commit()
        print("StrokeSpeak tables and starter language lessons are ready!")

    except Exception as error:
        connection.rollback()
        print("Error creating tables:", error)

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    create_tables()












