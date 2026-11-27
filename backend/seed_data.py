from app.db.database import get_db_connection


def seed_starter_lesson():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Add the language once. If it already exists, leave it as it is.
        cursor.execute(
            """
            INSERT IGNORE INTO languages (name, script_code)
            VALUES (%s, %s)
            """,
            ("Hindi", "Deva"),
        )

        # Look up its ID so the character can refer to it.
        cursor.execute(
            "SELECT id FROM languages WHERE script_code = %s",
            ("Deva",),
        )
        language_id = cursor.fetchone()[0]

        # Add the starter character, or update its lesson text if it exists.
        cursor.execute(
            """
            INSERT INTO characters
                (language_id, character_text, meaning, pronunciation_text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                meaning = %s,
                pronunciation_text = %s
            """,
            (
                language_id,
                "अ",
                "Starter Hindi character",
                "a",
                "Starter Hindi character",
                "a",
            ),
        )

        connection.commit()
        print("Starter Hindi character added successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    seed_starter_lesson()