# Import FastAPI to build the backend API.
# HTTPException returns errors such as 404, 409, and 500.
# Query adds and validates query-string parameters.
from fastapi import Depends, FastAPI, HTTPException, Query

# BaseModel and Field validate incoming JSON request data.
from pydantic import BaseModel, Field, field_validator

# Error handles general MySQL errors.
# IntegrityError handles constraint errors, such as duplicates.
from mysql.connector import Error, IntegrityError

# Import our function for connecting to the MySQL database.
from app.db.database import get_db_connection
from app.reference_paths import reference_path_fingerprint
from app.security import create_access_token, get_current_admin_user_id, get_current_user_id, get_optional_user_id, has_demo_quiz_access, is_admin_user_id, is_developer_user_id, require_user_scope
from app.quiz_api import router as section_quiz_router, _lesson_is_unlocked
from app.ml.registry import model_registry
from fastapi.responses import FileResponse, Response
from pathlib import Path
from datetime import datetime, timezone
from gtts import gTTS
import io

import base64
import hashlib
import hmac
import json
import re
import secrets
import tempfile
import threading
import os
import mimetypes
import urllib.error
import urllib.request
import uuid
import unicodedata
from typing import Literal

# --------------------------------------------------
# 1. CREATE THE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="StrokeSpeak API",
    description="Multilingual handwriting and pronunciation learning platform",
    version="0.1.0",
)


app.include_router(section_quiz_router)

# Public scope: Sanskrit (Devanagari), Japanese (Hiragana and Katakana), Tamil,
# and Simplified Chinese. These four language groups use five script records.
# Other legacy database rows remain stored but are hidden from public API reads and writes.
SUPPORTED_SCRIPT_CODES = ("ja-hiragana", "ja-katakana", "sa-devanagari", "ta", "zh-hans")
HIDDEN_TEST_CHARACTER_IDS = {169}
_SCRIPT_PLACEHOLDERS = ", ".join(["%s"] * len(SUPPORTED_SCRIPT_CODES))


def _supported_script_clause(alias: str) -> str:
    return f"{alias}.script_code IN ({_SCRIPT_PLACEHOLDERS})"


# --------------------------------------------------
# 2. VALIDATE LANGUAGE INPUT
# --------------------------------------------------

class LanguageCreate(BaseModel):
    # Name of the language or writing system.
    name: str = Field(min_length=1, max_length=100)

    # Unique code identifying the writing system.
    # Example: ja-hiragana
    script_code: str = Field(min_length=1, max_length=20)

    # Remove extra spaces and reject blank strings.
    @field_validator("name", "script_code")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("script_code")
    @classmethod
    def validate_supported_script(cls, value: str) -> str:
        if value not in SUPPORTED_SCRIPT_CODES:
            raise ValueError("Only Sanskrit, Japanese, Tamil, and Simplified Chinese are supported.")
        return value


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address.")
        return value


class UserProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters.")
        return value


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address.")
        return value


# --------------------------------------------------
class StrokePoint(BaseModel):
    x: float
    y: float
    time: int


class PracticeAttemptCreate(BaseModel):
    user_id: int = Field(gt=0)
    character_id: int = Field(gt=0)
    stroke_data: list[list[StrokePoint]] = Field(min_length=1)
    canvas_image_base64: str | None = None

class HandwritingRecognizeRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=5_000_000)
    script_code: str = Field(default="ja-hiragana", max_length=20)
    expected_character: str | None = None

class CharacterRecognizeRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=5_000_000)

class PronunciationAudioUpload(BaseModel):
    audio_base64: str = Field(min_length=1, max_length=4_000_000)
    mime_type: str = Field(min_length=1, max_length=100)

    @field_validator("mime_type")
    @classmethod
    def validate_audio_mime_type(cls, value: str) -> str:
        value = value.strip().lower()
        if not value.startswith("audio/"):
            raise ValueError("The uploaded recording must use an audio MIME type.")
        return value

class PronunciationAssessmentCreate(BaseModel):
    transcribed_text: str = Field(min_length=1, max_length=1000)

    @field_validator("transcribed_text")
    @classmethod
    def validate_transcribed_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Transcribed speech cannot be blank.")
        return value

class LessonProgressUpdate(BaseModel):
    user_id: int = Field(gt=0)
    status: Literal["not_started", "in_progress", "completed"]
    score: float | None = Field(default=None, ge=0, le=100)


class TutorialVideoUpdate(BaseModel):
    video_url: str | None = Field(default=None, max_length=500)
    status: Literal["not_started", "processing", "ready", "failed"]

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                return None
        return value

class ReferenceStrokesUpdate(BaseModel):
    stroke_data: list[list[StrokePoint]] = Field(min_length=1)


class StrokePreviewEvaluate(BaseModel):
    character_id: int = Field(gt=0)
    learner_strokes: list[list[StrokePoint]] = Field(min_length=1, max_length=60)
    reference_strokes: list[list[StrokePoint]] = Field(min_length=1, max_length=60)

    @field_validator("learner_strokes", "reference_strokes")
    @classmethod
    def validate_preview_strokes(cls, strokes):
        if any(len(stroke) < 2 for stroke in strokes):
            raise ValueError("Each preview stroke must contain at least two points.")
        if sum(len(stroke) for stroke in strokes) > 6000:
            raise ValueError("A preview may contain at most 6000 points.")
        return strokes


class ReferenceReviewCreate(BaseModel):
    reviewer_name: str = Field(min_length=2, max_length=120)
    reviewer_qualification: str = Field(min_length=5, max_length=300)
    reference_standard: str = Field(min_length=5, max_length=500)
    writing_convention: str = Field(min_length=3, max_length=200)
    decision: Literal["approve", "revise", "hold"]
    notes: str | None = Field(default=None, max_length=2000)
    attests_exact_reference: bool = False

    @field_validator("reviewer_name", "reviewer_qualification", "reference_standard", "writing_convention")
    @classmethod
    def validate_review_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This review field cannot be blank.")
        return value

    @field_validator("notes")
    @classmethod
    def normalize_review_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 310_000
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${password_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        _, iterations_str, salt_hex, hash_hex = parts
        try:
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)
        except (ValueError, TypeError):
            return False
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_hash, expected_hash)

    return False

# 3. HOME ROUTE
# --------------------------------------------------
# GET / returns a simple message confirming that
# the StrokeSpeak backend is running.

@app.get("/")
def home():
    return {
        "project": "StrokeSpeak",
        "message": "Backend is running!"
    }


# --------------------------------------------------
# 4. HEALTH-CHECK ROUTE
# --------------------------------------------------
# GET /api/v1/health checks both the API and its MySQL connection.

@app.get("/api/v1/health")
def health_check():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return {
            "status": "healthy",
            "service": "StrokeSpeak API",
            "database": "connected",
        }
    except Error:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "service": "StrokeSpeak API",
                "database": "disconnected",
            },
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# --------------------------------------------------
@app.post("/api/v1/auth/register", status_code=201)
def register_user(user: UserRegister):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (user.name, user.email, hash_password(user.password)),
        )

        connection.commit()
        new_user_id = cursor.lastrowid

        return {
            "message": "Account created successfully.",
            "user": {
                "id": new_user_id,
                "name": user.name,
                "email": user.email,
                "role": "admin" if is_admin_user_id(new_user_id) else "learner",
                "developer_mode": is_developer_user_id(new_user_id),
                "demo_quiz_access": has_demo_quiz_access(new_user_id),
            },
            "token": create_access_token(new_user_id),
        }

    except IntegrityError:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create the account.",
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
@app.post("/api/v1/auth/login")
def login_user(credentials: UserLogin):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = %s
            LIMIT 1
            """,
            (credentials.email,),
        )
        user = cursor.fetchone()
        if not user or not verify_password(credentials.password, user.get("password_hash") or ""):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        token = create_access_token(int(user["id"]))
        return {
            "message": "Login successful.",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": "admin" if is_admin_user_id(int(user["id"])) else "learner",
                "developer_mode": is_developer_user_id(int(user["id"])),
                "demo_quiz_access": has_demo_quiz_access(int(user["id"])),
            },
            "token": token,
        }
    except HTTPException:
        raise
    except Error:
        raise HTTPException(
            status_code=500,
            detail="Authentication failed due to a database error.",
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/v1/auth/me")
def get_current_user(user_id: int = Depends(get_current_user_id)):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return {
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": "admin" if is_admin_user_id(user_id) else "learner",
                "developer_mode": is_developer_user_id(user_id),
                "demo_quiz_access": has_demo_quiz_access(user_id),
                "created_at": str(user["created_at"]) if user.get("created_at") else None,
            }
        }
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Database error retrieving user.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/v1/auth/profile")
def update_current_user_profile(
    profile: UserProfileUpdate,
    user_id: int = Depends(get_current_user_id),
):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "UPDATE users SET name = %s WHERE id = %s",
            (profile.name, user_id),
        )
        connection.commit()
        cursor.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return {
            "message": "Profile updated successfully.",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": "admin" if is_admin_user_id(user_id) else "learner",
                "developer_mode": is_developer_user_id(user_id),
                "demo_quiz_access": has_demo_quiz_access(user_id),
                "created_at": str(user["created_at"]) if user.get("created_at") else None,
            },
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Database error updating profile.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def _valid_strokes(strokes):
    result = []
    for stroke in strokes or []:
        points = [point.model_dump() if hasattr(point, "model_dump") else point for point in stroke]
        if points:
            result.append(points)
    return result


def _normalized_points(strokes):
    points = [point for stroke in strokes for point in stroke]
    if not points:
        return [], []
    min_x, max_x = min(float(p["x"]) for p in points), max(float(p["x"]) for p in points)
    min_y, max_y = min(float(p["y"]) for p in points), max(float(p["y"]) for p in points)
    dx = max_x - min_x
    dy = max_y - min_y
    scale = max(dx, dy, 1e-6)
    offset_x = (1.0 - dx / scale) / 2.0
    offset_y = (1.0 - dy / scale) / 2.0
    normalized = [[
        (
            (float(p["x"]) - min_x) / scale + offset_x,
            (float(p["y"]) - min_y) / scale + offset_y,
        )
        for p in stroke
    ] for stroke in strokes]
    return normalized, [point for stroke in normalized for point in stroke]


def _point_distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _resample_stroke(stroke, count=32):
    if len(stroke) == 1:
        return [stroke[0]] * count
    lengths = [0.0]
    for i in range(1, len(stroke)):
        lengths.append(lengths[-1] + _point_distance(stroke[i - 1], stroke[i]))
    total = lengths[-1]
    if total == 0:
        return [stroke[0]] * count
    sampled, segment = [], 1
    for step in range(count):
        target = total * step / (count - 1)
        while segment < len(lengths) - 1 and lengths[segment] < target:
            segment += 1
        left, right = lengths[segment - 1], lengths[segment]
        ratio = 0.0 if right == left else (target - left) / (right - left)
        a, b = stroke[segment - 1], stroke[segment]
        sampled.append((a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio))
    return sampled


def _stroke_has_movement(stroke, epsilon=1e-6):
    """Return false for a single-point or stationary stroke."""
    if len(stroke) < 2:
        return False
    first = stroke[0]
    previous = (float(first["x"]), float(first["y"]))
    for point in stroke[1:]:
        current = (float(point["x"]), float(point["y"]))
        if _point_distance(previous, current) > epsilon:
            return True
        previous = current
    return False


def _remove_unmatched_stationary_strokes(learner_strokes, reference_strokes):
    """Ignore extra taps only when the reference has no matching stationary stroke."""
    reference_capacity = sum(not _stroke_has_movement(stroke) for stroke in reference_strokes)
    result = []
    kept_stationary = 0
    ignored = 0
    for stroke in learner_strokes:
        if _stroke_has_movement(stroke):
            result.append(stroke)
        elif kept_stationary < reference_capacity:
            result.append(stroke)
            kept_stationary += 1
        else:
            ignored += 1
    return result, ignored


def _mean_direction_similarity(learner, reference):
    """Compare corresponding arc-length-resampled tangents, ignoring zero-length segments."""
    similarities = []
    for index in range(min(len(learner), len(reference)) - 1):
        learner_dx = learner[index + 1][0] - learner[index][0]
        learner_dy = learner[index + 1][1] - learner[index][1]
        reference_dx = reference[index + 1][0] - reference[index][0]
        reference_dy = reference[index + 1][1] - reference[index][1]
        learner_length = (learner_dx ** 2 + learner_dy ** 2) ** 0.5
        reference_length = (reference_dx ** 2 + reference_dy ** 2) ** 0.5
        if learner_length <= 1e-6 or reference_length <= 1e-6:
            continue
        cosine = (learner_dx * reference_dx + learner_dy * reference_dy) / (learner_length * reference_length)
        similarities.append(max(-1.0, min(1.0, cosine)))
    return sum(similarities) / len(similarities) if similarities else None


def _prototype_scores(learner_strokes, reference_strokes):
    # Minimum-size guard based on canvas size (about 10% of canvas height: 32px, or 0.10 if normalized <= 1.0)
    all_learner_pts = [point for stroke in learner_strokes for point in stroke]
    if not all_learner_pts:
        return None, None, False
    raw_dx = max(float(p["x"]) for p in all_learner_pts) - min(float(p["x"]) for p in all_learner_pts)
    raw_dy = max(float(p["y"]) for p in all_learner_pts) - min(float(p["y"]) for p in all_learner_pts)
    is_norm = max(float(p["y"]) for p in all_learner_pts) <= 1.0 and max(float(p["x"]) for p in all_learner_pts) <= 1.0
    min_size = 0.10 if is_norm else 32.0
    is_too_small = max(raw_dx, raw_dy) < min_size

    learner, learner_points = _normalized_points(learner_strokes)
    reference, reference_points = _normalized_points(reference_strokes)
    if not learner_points or not reference_points:
        return None, None, False

    def mean_nearest(source, target):
        return sum(min(_point_distance(p, q) for q in target) for p in source) / len(source)

    shape_distance = (mean_nearest(learner_points, reference_points) + mean_nearest(reference_points, learner_points)) / 2
    count_penalty = abs(len(learner) - len(reference)) / max(len(learner), len(reference), 1)

    raw_shape = 100.0 * (1.0 - shape_distance / 0.5)
    shape = round(max(0.0, min(100.0, raw_shape * (1.0 - count_penalty))), 2)

    if is_too_small:
        shape = min(shape, 10.0)

    matched = min(len(learner), len(reference))
    if not matched:
        return shape, 0.0, is_too_small

    stroke_scores = []
    for i in range(matched):
        a, b = _resample_stroke(learner[i]), _resample_stroke(reference[i])
        stroke_dist = sum(_point_distance(p, q) for p, q in zip(a, b)) / len(a)
        stroke_order = max(0.0, 100.0 * (1.0 - stroke_dist / 0.75))

        direction_similarity = _mean_direction_similarity(a, b)
        if direction_similarity is not None:
            # A gradual factor keeps small direction deviations from triggering a hard score drop.
            direction_factor = max(0.0, min(1.0, (1.0 + direction_similarity) / 2.0))
            stroke_order *= direction_factor

        stroke_scores.append(stroke_order)

    avg_order = sum(stroke_scores) / len(stroke_scores)
    order = max(0.0, min(100.0, avg_order * (1.0 - count_penalty)))
    return shape, round(order, 2), is_too_small


def _classify_stroke_reference(reference_strokes, reference_strokes_svg) -> dict:
    """Classify reference verification tier using actual source evidence and SHA-256 fingerprints.

    Tiers:
    - instructor_certified: approved instructor review matching current SHA-256 fingerprint (enforces stroke order).
    - source_supported: verifiable source evidence (source, source_file, source_url/file_url/asset_url,
      cryptographic hash or source_revision, non-draft license, and valid fingerprint) (enforces stroke order).
    - unverified: draft/unattributed or missing verifiable evidence (stroke-order completion cannot be certified).
    """
    if isinstance(reference_strokes_svg, str):
        try:
            reference_strokes_svg = json.loads(reference_strokes_svg)
        except (ValueError, TypeError):
            reference_strokes_svg = None
    if not isinstance(reference_strokes_svg, dict) or not reference_strokes:
        return {"tier": "unverified", "enforce_stroke_order": False, "instructor_certified": False, "source_supported": False}

    try:
        current_fp = reference_path_fingerprint(reference_strokes, reference_strokes_svg)
    except (ValueError, TypeError, KeyError):
        return {"tier": "unverified", "enforce_stroke_order": False, "instructor_certified": False, "source_supported": False}
    if not current_fp:
        return {"tier": "unverified", "enforce_stroke_order": False, "instructor_certified": False, "source_supported": False}

    svg_strokes = reference_strokes_svg.get("strokes")
    if not isinstance(svg_strokes, list) or len(svg_strokes) != len(reference_strokes):
        return {"tier": "unverified", "enforce_stroke_order": False, "instructor_certified": False, "source_supported": False}

    if (
        reference_strokes_svg.get("instructional_review_status") == "approved"
        and reference_strokes_svg.get("reviewed_reference_sha256") == current_fp
    ):
        return {"tier": "instructor_certified", "enforce_stroke_order": True, "instructor_certified": True, "source_supported": True}

    prov_status = str(reference_strokes_svg.get("provenance_status") or "").strip().lower()
    review_status = str(reference_strokes_svg.get("instructional_review_status") or "").strip().lower()
    license_text = str(reference_strokes_svg.get("license") or "").strip()
    source_name = str(reference_strokes_svg.get("source") or "").strip()
    source_file = str(reference_strokes_svg.get("source_file") or "").strip()
    has_source_url = any(
        bool(str(reference_strokes_svg.get(k) or "").strip())
        for k in ("source_url", "source_file_url", "source_asset_url")
    )
    has_crypto_or_rev = bool(
        str(reference_strokes_svg.get("source_asset_sha256") or "").strip()
        or str(reference_strokes_svg.get("source_revision") or "").strip()
        or "SHA-256" in source_file.upper()
    )

    has_verifiable_source = (
        review_status != "rejected"
        and prov_status != "unverified"
        and bool(source_name)
        and bool(source_file)
        and has_source_url
        and has_crypto_or_rev
        and bool(license_text)
        and "unverified" not in license_text.lower()
    )
    if has_verifiable_source:
        return {"tier": "source_supported", "enforce_stroke_order": True, "instructor_certified": False, "source_supported": True}

    return {"tier": "unverified", "enforce_stroke_order": False, "instructor_certified": False, "source_supported": False}


def _evaluate_handwriting_assessment(
    handwriting_score,
    stroke_order_score,
    ref_classification: dict,
    cnn_res: dict | None = None,
    target_char: str = "",
) -> tuple[str, bool, str | None]:
    """Unified assessment status/pass rule shared by practice attempt creation and lesson completion."""
    shape_ok = handwriting_score is None or float(handwriting_score) >= 60.0
    enforce_stroke = bool(ref_classification.get("enforce_stroke_order"))
    stroke_ok = (not enforce_stroke) or stroke_order_score is None or float(stroke_order_score) >= 55.0

    if cnn_res is not None:
        status_val = cnn_res.get("status", "success")
        if status_val == "empty_canvas":
            return "empty_canvas", False, "Canvas drawing was empty or had insufficient ink for CNN recognition. Please draw the character clearly and retry."
        if status_val == "success":
            pred_c = cnn_res.get("predicted_character")
            pred_conf = cnn_res.get("confidence")
            if pred_c and target_char and pred_c != target_char:
                return (
                    "mismatch_rejected",
                    False,
                    f"Character mismatch: CNN recognized '{pred_c}' ({pred_conf}%) instead of '{target_char}'. "
                    f"Geometric shape similarity ({handwriting_score if handwriting_score is not None else 'N/A'}%) cannot pass a mismatched character. "
                    f"Compare your strokes with the '{target_char}' guide and retry.",
                )
            if not cnn_res.get("is_match"):
                return (
                    "low_confidence_retry",
                    False,
                    f"Low CNN confidence ({pred_conf}%) for '{target_char}'. Please redraw the character clearly and retry.",
                )

    if not shape_ok:
        return "needs_retry", False, None
    if not stroke_ok:
        return "stroke_order_retry", False, None
    if ref_classification.get("tier") == "unverified":
        return (
            "provisional_reference_unverified",
            False,
            "Handwriting shape and CNN matched, but this character's stroke-order reference is unverified/pending attribution, so mandatory stroke-order completion cannot be certified yet.",
        )
    return "passed", True, None


def _drawing_feedback(handwriting_score, stroke_order_score, learner_strokes, reference_strokes, is_too_small=False):
    """Give the learner specific practice guidance from prototype comparison scores."""
    comments = []
    if is_too_small:
        comments.append("The drawing is too small to evaluate accurately; try drawing larger across the canvas.")
    elif handwriting_score is not None:
        if handwriting_score >= 85:
            comments.append("Your overall character shape is close to the reference.")
        elif handwriting_score >= 60:
            comments.append("Your character is partly similar; compare its width, height, and curves with the reference.")
        else:
            comments.append("Try drawing the character larger and follow the reference outline one section at a time.")

    if len(learner_strokes) != len(reference_strokes):
        comments.append(
            f"Your drawing has {len(learner_strokes)} strokes; the saved reference has {len(reference_strokes)}. "
            "Check where the reference lifts the pen between strokes."
        )
    elif stroke_order_score is not None and stroke_order_score >= 85:
        comments.append("Your stroke paths and order are close to the reference.")
    elif stroke_order_score is not None and stroke_order_score >= 60:
        comments.append("The stroke order is partly matched; replay the guide and compare each stroke's direction.")
    elif stroke_order_score is not None:
        comments.append("Replay the stroke guide and practise one stroke at a time, following its direction.")

    comments.append("These are geometric prototype estimates, not scores from a trained handwriting AI model.")
    return " ".join(comments)

@app.post("/api/v1/developer/stroke-preview/evaluate")
def evaluate_stroke_preview(
    preview: StrokePreviewEvaluate,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """Run the production geometric scorer on supplied geometry without reading or writing MySQL."""
    learner_strokes = _valid_strokes(preview.learner_strokes)
    reference_strokes = _valid_strokes(preview.reference_strokes)
    scoring_strokes, ignored_stationary_strokes = _remove_unmatched_stationary_strokes(
        learner_strokes, reference_strokes
    )
    handwriting_score, stroke_order_score, is_too_small = _prototype_scores(
        scoring_strokes, reference_strokes
    )
    feedback = _drawing_feedback(
        handwriting_score, stroke_order_score, scoring_strokes, reference_strokes,
        is_too_small=is_too_small,
    )
    if ignored_stationary_strokes:
        feedback = (
            f"Ignored {ignored_stationary_strokes} stationary pen tap(s) during geometric scoring. "
            + feedback
        )
    return {
        "mode": "dry_run", "persisted": False, "character_id": preview.character_id,
        "handwriting_score": handwriting_score, "stroke_order_score": stroke_order_score,
        "ignored_stationary_strokes": ignored_stationary_strokes, "feedback": feedback,
        "scoring_notice": "Geometric prototype estimate; not CNN accuracy or instructor verification.",
    }


@app.get("/api/v1/developer/stroke-preview/candidates/{character_id}")
def list_stroke_preview_candidates(
    character_id: int,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """Read pending candidate JSON only from the known capture inbox; never touches MySQL."""
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")
    inbox = Path(__file__).resolve().parent / "data" / "reference_strokes" / "capture-inbox"
    if not inbox.is_dir():
        return {"character_id": character_id, "candidates": []}
    inbox_root = inbox.resolve()
    candidates = []
    for path in sorted(inbox.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            if path.resolve(strict=True).parent != inbox_root or path.stat().st_size > 2_000_000:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                continue
            if int(payload.get("character_id", 0)) != character_id:
                continue
            if payload.get("script_code") not in SUPPORTED_SCRIPT_CODES:
                continue
            if payload.get("candidate_status") != "captured_pending_review":
                continue
            if (payload.get("instructor_review") or {}).get("status") != "pending":
                continue
            points = payload.get("points")
            if not isinstance(points, list) or not points:
                continue
            visible = {
                key: payload[key]
                for key in (
                    "schema_version", "capture_id", "captured_at_utc", "character_id",
                    "script_code", "character", "candidate_status", "stroke_count",
                    "point_count", "points", "source", "captured_by", "instructor_review", "svg",
                )
                if key in payload
            }
            candidates.append({"file_name": path.name, "candidate": visible})
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return {"character_id": character_id, "candidates": candidates}


@app.post("/api/v1/practice-attempts", status_code=201)
def create_practice_attempt(attempt: PracticeAttemptCreate, current_user_id: int = Depends(get_current_user_id)):
    require_user_scope(current_user_id, attempt.user_id)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        learner_strokes = _valid_strokes(attempt.stroke_data)
        if not learner_strokes:
            raise HTTPException(status_code=422, detail="Draw at least one stroke before saving.")
        cursor.execute(
            f"""SELECT c.reference_strokes, c.reference_strokes_svg, c.character_text, l.script_code FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (attempt.character_id, *SUPPORTED_SCRIPT_CODES),
        )
        character = cursor.fetchone()
        if not character:
            raise HTTPException(status_code=404, detail="The selected character was not found.")
        reference_strokes = character["reference_strokes"]
        if isinstance(reference_strokes, str):
            reference_strokes = json.loads(reference_strokes)
        reference_strokes = _valid_strokes(reference_strokes)
        ref_classification = _classify_stroke_reference(
            reference_strokes, character.get("reference_strokes_svg")
        )
        stroke_verified = ref_classification["instructor_certified"]
        handwriting_score, stroke_order_score = None, None
        ignored_stationary_strokes = 0
        if reference_strokes:
            scoring_strokes, ignored_stationary_strokes = _remove_unmatched_stationary_strokes(
                learner_strokes, reference_strokes
            )
            handwriting_score, stroke_order_score, is_too_small = _prototype_scores(scoring_strokes, reference_strokes)
            feedback = _drawing_feedback(
                handwriting_score,
                stroke_order_score,
                scoring_strokes,
                reference_strokes,
                is_too_small=is_too_small,
            )
            if ignored_stationary_strokes:
                feedback = (
                    f"Ignored {ignored_stationary_strokes} stationary pen tap(s) during geometric scoring. "
                    + feedback
                )
            if ref_classification["tier"] == "source_supported" and stroke_order_score is not None:
                feedback += " (Stroke-order evaluated against source-attributed reference; independent instructor certification is pending.)"
            elif ref_classification["tier"] == "unverified" and stroke_order_score is not None:
                feedback += " (Stroke-order reference is unverified/pending review; stroke-order score is advisory only.)"
        else:
            feedback = "Drawing saved. No reference drawing exists for this character yet, so drawing scores are pending."

        # Real CNN Handwriting Recognition (Stage 4 & Stage 5B)
        cnn_recognition = None
        cnn_res = None
        target_char = character.get("character_text") or ""
        if attempt.canvas_image_base64:
            script_code = character.get("script_code")
            reg_scripts = model_registry.get_registered_scripts()
            if script_code in reg_scripts and reg_scripts[script_code]["has_trained_model"]:
                trained_classes = reg_scripts[script_code].get("trained_classes", [])
                if trained_classes and target_char not in trained_classes:
                    cnn_recognition = {
                        "status": "character_not_supported_by_cnn",
                        "detail": f"Character '{target_char}' is not among the {len(trained_classes)} trained CNN classes for {script_code}.",
                        "supported_classes": trained_classes,
                    }
                    feedback += f" (Note: Character '{target_char}' is outside the {len(trained_classes)} trained CNN classes for this script; geometric evaluation applied.)"
                else:
                    try:
                        cnn_res = model_registry.predict(
                            image_input=attempt.canvas_image_base64,
                            script_code=script_code,
                            expected_character=target_char,
                        )
                        cnn_recognition = {
                            "status": cnn_res.get("status", "success"),
                            "predicted_character": cnn_res.get("predicted_character"),
                            "confidence": cnn_res.get("confidence"),
                            "is_match": cnn_res.get("is_match"),
                            "top_predictions": cnn_res.get("top_predictions"),
                            "inference_time_ms": cnn_res.get("inference_time_ms"),
                            "model_name": cnn_res.get("model_name"),
                            "inference_runtime": cnn_res.get("inference_runtime"),
                        }
                        if cnn_res.get("is_match"):
                            feedback += f" CNN AI recognized '{cnn_res['predicted_character']}' ({cnn_res['confidence']}%) matching the target character."
                    except Exception as ml_err:
                        cnn_recognition = {"error": str(ml_err)}

        assessment_status, assessment_passed, override_feedback = _evaluate_handwriting_assessment(
            handwriting_score,
            stroke_order_score,
            ref_classification,
            cnn_res=cnn_res,
            target_char=target_char,
        )
        if override_feedback:
            feedback = override_feedback

        stroke_json = json.dumps(learner_strokes)
        cursor.execute(
            """
            INSERT INTO practice_attempts
                (user_id, character_id, stroke_data, handwriting_score, stroke_order_score, feedback)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (current_user_id, attempt.character_id, stroke_json, handwriting_score, stroke_order_score, feedback),
        )
        connection.commit()
        return {
            "message": "Practice drawing saved.",
            "attempt_id": cursor.lastrowid,
            "user_id": attempt.user_id,
            "character_id": attempt.character_id,
            "stroke_count": len(learner_strokes),
            "ignored_stationary_stroke_count": ignored_stationary_strokes,
            "scores": {"handwriting": handwriting_score, "stroke_order": stroke_order_score, "pronunciation": None},
            "assessment": {
                "status": assessment_status,
                "passed": assessment_passed,
                "geometric_similarity": handwriting_score,
                "stroke_order_similarity": stroke_order_score,
                "stroke_verification_tier": ref_classification["tier"],
                "stroke_reference_verified": stroke_verified,
                "instructor_certified": ref_classification["instructor_certified"],
                "cnn_confidence": cnn_recognition.get("confidence") if isinstance(cnn_recognition, dict) else None,
                "cnn_match": cnn_recognition.get("is_match") if isinstance(cnn_recognition, dict) else None,
            },
            "scoring_method": "geometric prototype comparison + CNN AI recognition" if cnn_recognition else "prototype geometric comparison; not trained AI",
            "cnn_recognition": cnn_recognition,
            "feedback": feedback,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except IntegrityError:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=404, detail="The selected user or character was not found.")
    except (Error, ValueError, TypeError, KeyError):
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save or compare the practice drawing.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# --------------------------------------------------
# ML HANDWRITING RECOGNITION ENDPOINTS (STAGE 4)
# --------------------------------------------------

@app.get("/api/v1/ml/models")
def get_ml_models():
    """Return status and metadata for all multi-script handwriting models."""
    return {
        "status": "success",
        "scripts": model_registry.get_registered_scripts()
    }

@app.post("/api/v1/ml/recognize")
def recognize_handwriting(req: HandwritingRecognizeRequest):
    """
    Recognize a handwriting drawing for a given script_code using the CNN pipeline.
    Strictly enforces script boundaries; untrained scripts return status 'script_not_trained'.
    """
    reg_scripts = model_registry.get_registered_scripts()
    if req.script_code not in reg_scripts:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown script code '{req.script_code}'. Registered scripts: {list(reg_scripts.keys())}"
        )
    
    script_info = reg_scripts[req.script_code]
    if not script_info["has_trained_model"]:
        return {
            "status": "script_not_trained",
            "script_code": req.script_code,
            "language_name": script_info["language_name"],
            "detail": f"Handwriting recognition CNN for script '{req.script_code}' is not yet trained. {script_info['note']}",
            "trained_classes": []
        }

    try:
        result = model_registry.predict(
            image_input=req.image_base64,
            script_code=req.script_code,
            expected_character=req.expected_character
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Handwriting recognition failed: {str(e)}")

@app.post("/api/v1/characters/{character_id}/recognize")
def recognize_character_drawing(character_id: int, req: CharacterRecognizeRequest):
    """
    Recognize handwriting drawn for a specific character ID against its target script and symbol.
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT c.id, c.character_text, l.script_code, l.name AS language_name
                FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        char = cursor.fetchone()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found.")

        script_code = char["script_code"]
        reg_scripts = model_registry.get_registered_scripts()
        if script_code not in reg_scripts or not reg_scripts[script_code]["has_trained_model"]:
            return {
                "status": "script_not_trained",
                "character_id": character_id,
                "character_text": char["character_text"],
                "script_code": script_code,
                "language_name": char["language_name"],
                "detail": f"Handwriting CNN for {char['language_name']} ({script_code}) is not yet trained.",
            }

        trained_classes = reg_scripts[script_code].get("trained_classes", [])
        if trained_classes and char["character_text"] not in trained_classes:
            return {
                "status": "character_not_supported_by_cnn",
                "character_id": character_id,
                "character_text": char["character_text"],
                "script_code": script_code,
                "language_name": char["language_name"],
                "detail": f"Character '{char['character_text']}' is not among the {len(trained_classes)} trained CNN classes for {char['language_name']} ({script_code}). CNN classification currently supports: {', '.join(trained_classes)}.",
                "supported_classes": trained_classes,
                "predicted_character": None,
                "confidence": None,
                "is_match": None,
            }

        result = model_registry.predict(
            image_input=req.image_base64,
            script_code=script_code,
            expected_character=char["character_text"]
        )
        result["character_id"] = character_id
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

_whisper_model = None
_whisper_model_lock = threading.Lock()


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_model_lock:
            if _whisper_model is None:
                try:
                    from faster_whisper import WhisperModel
                except ImportError as error:
                    raise RuntimeError("Whisper could not load its Windows audio runtime. Install backend/requirements-ai.txt and check that Windows allows the audio decoder components.") from error
                model_name = os.getenv("STROKESPEAK_WHISPER_MODEL", "base")
                _whisper_model = WhisperModel(model_name, device="cpu", compute_type="int8")
    return _whisper_model

def _clean_text(text: str) -> str:
    """Normalize Unicode and strip whitespace, punctuation, and control characters."""
    if not text:
        return ""
    nfkc = unicodedata.normalize("NFKC", text)
    cleaned = "".join(
        c for c in nfkc
        if not (
            unicodedata.category(c).startswith("P")
            or unicodedata.category(c).startswith("Z")
            or unicodedata.category(c).startswith("C")
            or unicodedata.category(c).startswith("S")
        )
    )
    return cleaned.strip().casefold()


def _strip_diacritics(text: str) -> str:
    """Strip combining marks / accents while preserving base Latin and non-combining glyphs."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_japanese_kana(text: str) -> str:
    """Convert Katakana (U+30A1..U+30F6) to Hiragana and strip Japanese vowel elongation marks."""
    out = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        elif ch in ("\u30fc", "\u301c"):  # chōonpu 'ー' and wave dash '〜'
            continue
        else:
            out.append(ch)
    return "".join(out)


def _strip_vedic_marks(text: str) -> str:
    """Strip Vedic pitch/svara tone marks (U+0951..U+0954, U+1CD0..U+1CFF) while keeping vowel matras."""
    return "".join(
        ch for ch in text
        if not (0x0951 <= ord(ch) <= 0x0954 or 0x1CD0 <= ord(ch) <= 0x1CFF)
    )


def _validate_audio_signal(audio_path: str) -> tuple[float, float]:
    """Decode audio to 16 kHz mono float32 and verify duration and RMS speech energy."""
    try:
        import numpy as np
        from faster_whisper.audio import decode_audio
    except ImportError:
        return 0.0, 0.0

    samples = decode_audio(audio_path, sampling_rate=16000)
    duration = float(len(samples) / 16000.0) if len(samples) > 0 else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0
    if duration < 0.2 or rms < 0.002:
        raise HTTPException(
            status_code=422,
            detail="Recording contains no detectable speech. Please check your microphone and speak clearly.",
        )
    return duration, rms


def _normalized_pronunciation(value: str) -> str:
    return _clean_text(value)


def _transcribe_with_openai(audio_path: str, file_suffix: str, language_code: str):
    """Optional hosted fallback; no request is sent unless explicitly selected and keyed."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Hosted transcription is selected but OPENAI_API_KEY is missing. "
            "Add your API key to backend/.env or switch STROKESPEAK_TRANSCRIPTION_PROVIDER to local."
        )

    boundary = "----StrokeSpeak" + uuid.uuid4().hex
    file_name = "pronunciation" + file_suffix
    mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    def form_field(name: str, value: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")

    body = bytearray()
    body.extend(form_field("model", os.getenv("STROKESPEAK_OPENAI_TRANSCRIPTION_MODEL", "gpt-transcribe")))
    body.extend(form_field("languages[]", language_code))
    body.extend(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8")
    )
    body.extend(audio_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=bytes(body),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise RuntimeError("Hosted transcription rejected the API key. Check OPENAI_API_KEY in backend/.env.") from error
        if error.code == 429:
            raise RuntimeError("Hosted transcription quota or rate limit reached. Check API billing and limits.") from error
        raise RuntimeError(f"Hosted transcription request failed (HTTP {error.code}).") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Could not reach the hosted transcription service. Check the internet connection.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Hosted transcription returned an unreadable response.") from error

    text = str(payload.get("text", "")).strip()
    detected = payload.get("languages") or []
    detected_language = detected[0].get("code") if detected and isinstance(detected[0], dict) else language_code
    return text, detected_language


def _levenshtein_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 100.0
    previous = list(range(len(s2) + 1))
    for row, c1 in enumerate(s1, start=1):
        current = [row]
        for col, c2 in enumerate(s2, start=1):
            current.append(min(
                current[-1] + 1,
                previous[col] + 1,
                previous[col - 1] + (c1 != c2),
            ))
        previous = current
    distance = previous[-1]
    max_len = max(len(s1), len(s2))
    return round(max(0.0, 100.0 * (1.0 - distance / max_len)), 2)


def _multilingual_pronunciation_score(character_text: str, pronunciation_text: str, transcribed_text: str) -> float:
    clean_transcribed = _clean_text(transcribed_text)
    if not clean_transcribed:
        return 0.0

    # Filter out pure combining-mark strings (e.g. decoder zalgo artifacts)
    if not any(not unicodedata.combining(ch) for ch in clean_transcribed):
        return 0.0

    scores = []
    # Target 1: Native Character Symbol (e.g. 'あ', '一', 'अ', 'அ')
    if character_text:
        clean_char = _clean_text(character_text)
        if clean_char:
            scores.append(_levenshtein_similarity(clean_char, clean_transcribed))
            # Japanese Kana normalization (Katakana -> Hiragana + strip elongation 'ー'/'〜')
            kana_char = _normalize_japanese_kana(clean_char)
            kana_trans = _normalize_japanese_kana(clean_transcribed)
            if kana_char and kana_trans:
                scores.append(_levenshtein_similarity(kana_char, kana_trans))
            # Sanskrit Vedic tone mark normalization (preserves vowel matras and virama)
            vedic_char = _strip_vedic_marks(clean_char)
            vedic_trans = _strip_vedic_marks(clean_transcribed)
            if vedic_char and vedic_trans:
                scores.append(_levenshtein_similarity(vedic_char, vedic_trans))

    # Target 2: Phonetic Transliteration (e.g. 'a', 'yī', 'èr', 'ā')
    if pronunciation_text:
        clean_pron = _clean_text(pronunciation_text)
        if clean_pron:
            stripped_pron = _strip_diacritics(clean_pron)
            stripped_trans = _strip_diacritics(clean_transcribed)
            if (
                stripped_pron == stripped_trans
                and clean_pron != clean_transcribed
                and stripped_trans != clean_transcribed
            ):
                # Explicit tone or vowel-length diacritic conflict (e.g. 'yī' vs 'yí'):
                # do not allow lexical tone mismatches to reach >= 50% completion threshold.
                scores.append(min(35.0, _levenshtein_similarity(clean_pron, clean_transcribed)))
            else:
                scores.append(_levenshtein_similarity(clean_pron, clean_transcribed))
                # Diacritic-stripped comparison only when the transcription has no tone/length marks
                # (e.g. 'yī' vs 'yi' -> 85% partial match).
                if stripped_trans == clean_transcribed and stripped_pron != clean_pron:
                    scores.append(round(0.85 * _levenshtein_similarity(stripped_pron, stripped_trans), 2))

    return max(scores) if scores else 0.0


def _transcript_match_feedback(score: float) -> str:
    if score >= 90:
        return "Strong transcript match (speech transcription matched the target text; not an acoustic phoneme grade)."
    if score >= 70:
        return "Partial transcript match (transcription is close to target text; speak clearly and try again)."
    return "Transcript differs from the target (speech transcription did not match target text)."


def _pronunciation_similarity(expected: str, actual: str) -> float:
    return _multilingual_pronunciation_score("", expected, actual)


@app.post("/api/v1/practice-attempts/{attempt_id}/pronunciation-assessment")
def assess_pronunciation(attempt_id: int, assessment: PronunciationAssessmentCreate, current_user_id: int = Depends(get_current_user_id)):
    if attempt_id < 1:
        raise HTTPException(status_code=422, detail="Attempt ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT pa.id, c.character_text, c.pronunciation_text
            FROM practice_attempts pa
            JOIN characters c ON c.id = pa.character_id
            JOIN languages l ON l.id = c.language_id
            WHERE pa.id = %s AND pa.user_id = %s AND {script_filter}
            """.format(script_filter=_supported_script_clause("l")),
            (attempt_id, current_user_id, *SUPPORTED_SCRIPT_CODES),
        )
        attempt = cursor.fetchone()
        if not attempt:
            raise HTTPException(status_code=404, detail="Practice attempt was not found.")
        character_text = attempt["character_text"] or ""
        expected = attempt["pronunciation_text"] or ""
        score = _multilingual_pronunciation_score(character_text, expected, assessment.transcribed_text)
        feedback = _transcript_match_feedback(score)
        cursor.execute(
            """
            UPDATE practice_attempts
            SET transcribed_text = %s,
                pronunciation_score = %s,
                pronunciation_feedback = %s,
                pronunciation_status = 'completed'
            WHERE id = %s
            """,
            (assessment.transcribed_text, score, feedback, attempt_id),
        )
        connection.commit()
        return {
            "message": "Pronunciation assessment saved.",
            "attempt_id": attempt_id,
            "character_text": character_text,
            "expected_text": expected,
            "transcribed_text": assessment.transcribed_text,
            "pronunciation_score": score,
            "feedback": feedback,
            "scoring_method": "normalized transcript text comparison against native character and transliteration; not phoneme or acoustic analysis",
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not assess the pronunciation.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.post("/api/v1/practice-attempts/{attempt_id}/transcribe")
def transcribe_pronunciation(attempt_id: int, current_user_id: int = Depends(get_current_user_id)):
    if attempt_id < 1:
        raise HTTPException(status_code=422, detail="Attempt ID must be positive.")
    connection = None
    cursor = None
    temporary_path = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT pa.audio_data, pa.audio_mime_type, c.character_text, c.pronunciation_text, l.script_code
            FROM practice_attempts pa
            JOIN characters c ON c.id = pa.character_id
            JOIN languages l ON l.id = c.language_id
            WHERE pa.id = %s AND pa.user_id = %s AND {script_filter}
            """.format(script_filter=_supported_script_clause("l")),
            (attempt_id, current_user_id, *SUPPORTED_SCRIPT_CODES),
        )
        attempt = cursor.fetchone()
        if not attempt:
            raise HTTPException(status_code=404, detail="Practice attempt was not found.")
        if not attempt["audio_data"]:
            raise HTTPException(status_code=409, detail="Save a pronunciation recording to this attempt first.")
        language_codes = {
            "ja-hiragana": "ja",
            "ja-katakana": "ja",
            "sa-devanagari": "sa",
            "ta": "ta",
            "zh-hans": "zh",
        }
        language_code = language_codes.get(attempt["script_code"])
        if not language_code:
            raise HTTPException(status_code=422, detail="Speech transcription is not configured for this language yet.")
        extension_by_mime = {
            "audio/webm": ".webm", "audio/wav": ".wav", "audio/x-wav": ".wav",
            "audio/ogg": ".ogg", "audio/mp4": ".m4a", "audio/mpeg": ".mp3",
        }
        suffix = extension_by_mime.get((attempt["audio_mime_type"] or "").split(";")[0], ".audio")
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_audio:
            temporary_audio.write(bytes(attempt["audio_data"]))
            temporary_path = temporary_audio.name
        _validate_audio_signal(temporary_path)
        provider = os.getenv("STROKESPEAK_TRANSCRIPTION_PROVIDER", "local").strip().lower()
        if provider == "openai":
            transcribed_text, detected_language = _transcribe_with_openai(
                temporary_path,
                suffix,
                language_code,
            )
            provider_label = "OpenAI hosted gpt-transcribe"
        elif provider == "local":
            model = _get_whisper_model()
            segments, info = model.transcribe(
                temporary_path,
                language=language_code,
                beam_size=5,
                temperature=0.0,
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                no_speech_threshold=0.6,
                repetition_penalty=1.15,
                no_repeat_ngram_size=2,
                vad_filter=False,
            )
            transcribed_text = " ".join(segment.text.strip() for segment in segments).strip()
            detected_language = getattr(info, "language", language_code)
            provider_label = "local faster-whisper"
        else:
            raise HTTPException(
                status_code=500,
                detail="STROKESPEAK_TRANSCRIPTION_PROVIDER must be either 'local' or 'openai'.",
            )
        clean_trans = _clean_text(transcribed_text)
        if not transcribed_text or not clean_trans or not any(not unicodedata.combining(ch) for ch in clean_trans):
            raise HTTPException(status_code=422, detail="No clear speech was transcribed. Try a longer, clearer recording.")
        character_text = attempt["character_text"] or ""
        expected = attempt["pronunciation_text"] or ""
        score = _multilingual_pronunciation_score(character_text, expected, transcribed_text)
        feedback = _transcript_match_feedback(score)
        cursor.execute(
            """
            UPDATE practice_attempts
            SET transcribed_text = %s,
                pronunciation_score = %s,
                pronunciation_feedback = %s,
                pronunciation_status = 'completed'
            WHERE id = %s
            """,
            (transcribed_text, score, feedback, attempt_id),
        )
        connection.commit()
        return {
            "message": "Speech transcription and transcript matching complete.",
            "attempt_id": attempt_id,
            "character_text": character_text,
            "expected_text": expected,
            "transcribed_text": transcribed_text,
            "pronunciation_score": score,
            "feedback": feedback,
            "detected_language": detected_language,
            "transcription_provider": provider_label,
            "scoring_method": "speech transcription followed by multilingual normalized text similarity; not phoneme or acoustic analysis",
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except RuntimeError as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=503, detail=str(error))
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not transcribe the pronunciation recording.")
    except Exception:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=502, detail="The selected speech transcription service could not process this recording. Check the audio format and provider settings.")
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.get("/api/v1/practice-attempts")
def get_practice_attempts(current_user_id: int = Depends(get_current_user_id)):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                pa.id AS attempt_id,
                pa.user_id,
                pa.character_id,
                c.character_text,
                JSON_LENGTH(pa.stroke_data) AS stroke_count,
                pa.handwriting_score,
                pa.stroke_order_score,
                pa.pronunciation_score,
                pa.pronunciation_status,
                pa.pronunciation_feedback,
                pa.transcribed_text,
                pa.feedback,
                pa.created_at
            FROM practice_attempts pa
            JOIN characters c ON c.id = pa.character_id
            JOIN languages l ON l.id = c.language_id
            WHERE pa.user_id = %s AND {script_filter}
            ORDER BY pa.created_at DESC, pa.id DESC
            """.format(script_filter=_supported_script_clause("l")),
            (current_user_id, *SUPPORTED_SCRIPT_CODES),
        )
        return {"attempts": cursor.fetchall()}

    except Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve practice attempts.",
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.put("/api/v1/practice-attempts/{attempt_id}/pronunciation-audio")
def save_pronunciation_audio(attempt_id: int, audio: PronunciationAudioUpload, current_user_id: int = Depends(get_current_user_id)):
    if attempt_id < 1:
        raise HTTPException(status_code=422, detail="Attempt ID must be positive.")
    try:
        audio_bytes = base64.b64decode(audio.audio_base64, validate=True)
    except (ValueError, base64.binascii.Error):
        raise HTTPException(status_code=422, detail="Audio data must be valid base64.")
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="The audio recording is empty.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT pa.id FROM practice_attempts pa
                JOIN characters c ON c.id = pa.character_id
                JOIN languages l ON l.id = c.language_id
                WHERE pa.id = %s AND pa.user_id = %s AND {_supported_script_clause('l')}""",
            (attempt_id, current_user_id, *SUPPORTED_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Practice attempt was not found.")
        cursor.execute(
            """
            UPDATE practice_attempts
            SET audio_data = %s,
                audio_mime_type = %s,
                pronunciation_status = 'pending_assessment',
                pronunciation_score = NULL,
                transcribed_text = NULL,
                pronunciation_feedback = 'Recording saved; ready for speech assessment.'
            WHERE id = %s AND user_id = %s
            """,
            (audio_bytes, audio.mime_type, attempt_id, current_user_id),
        )
        connection.commit()
        return {
            "message": "Pronunciation recording saved.",
            "attempt_id": attempt_id,
            "status": "pending_assessment",
            "pronunciation_score": None,
            "assessment_note": "Recording saved. Click assess to transcribe and evaluate speech.",
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save the pronunciation recording.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.put("/api/v1/characters/{character_id}/reference-strokes")
def save_character_reference_strokes(
    character_id: int,
    reference: ReferenceStrokesUpdate,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")

    connection = None
    cursor = None
    backup_path = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT c.reference_strokes, c.reference_strokes_svg FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        character = cursor.fetchone()
        if character is None:
            raise HTTPException(status_code=404, detail="Character was not found.")

        old_strokes = character.get("reference_strokes")
        if isinstance(old_strokes, str):
            old_strokes = json.loads(old_strokes)
        metadata = character.get("reference_strokes_svg")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        if not isinstance(metadata, dict):
            metadata = {}

        new_strokes = [
            [point.model_dump() for point in stroke]
            for stroke in reference.stroke_data
        ]
        old_digest = reference_path_fingerprint(old_strokes or [], metadata)
        incoming_digest = reference_path_fingerprint(new_strokes, metadata)
        geometry_changed = old_digest != incoming_digest
        provenance_status = metadata.get("provenance_status", "unverified")

        if geometry_changed and provenance_status in {"source_attributed", "verified"}:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This source-attributed reference cannot be overwritten through the canvas. "
                    "Use a backed-up, source-documented import/update so its license and review stay accurate."
                ),
            )

        if geometry_changed:
            backup_dir = Path(__file__).resolve().parent / "data" / "reference_strokes" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = backup_dir / f"before_admin_reference_edit_char{character_id}_{stamp}_{uuid.uuid4().hex[:8]}.json"
            backup_record = {
                "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "character_id": character_id,
                "edited_by_admin_user_id": current_admin_id,
                "reference_strokes": old_strokes,
                "reference_strokes_svg": metadata,
            }
            with backup_path.open("x", encoding="utf-8") as backup_file:
                json.dump(backup_record, backup_file, ensure_ascii=False, indent=2)

            source_snapshot = {
                key: metadata.get(key)
                for key in ("source", "source_url", "source_file", "source_file_url", "source_version", "license", "license_url", "provenance_status")
                if metadata.get(key) is not None
            }
            history = metadata.get("reference_edit_history")
            if not isinstance(history, list):
                history = []
            history.append({
                "edited_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "edited_by_admin_user_id": current_admin_id,
                "previous_reference_sha256": old_digest,
                "previous_source_metadata": source_snapshot,
            })
            metadata["reference_edit_history"] = history
            metadata["source"] = "Administrator-authored canvas draft"
            metadata["source_url"] = None
            metadata["source_file"] = None
            metadata["source_file_url"] = None
            metadata["source_version"] = None
            metadata["license"] = "Unverified; do not redistribute"
            metadata["license_url"] = None
            metadata["provenance_status"] = "unverified"
            metadata["instructional_review_status"] = "pending"
            metadata["review_invalidated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            metadata["review_invalidated_by_admin_user_id"] = current_admin_id
            metadata["coordinate_transform"] = "Administrator canvas draft; normalized coordinates"
            metadata["source_coordinates"] = "StrokeSpeak normalized canvas coordinates"
            metadata["viewBox"] = "0 0 1 1"
            metadata["strokes"] = []
            metadata["stroke_count"] = len(new_strokes)
            metadata.pop("reviewed_reference_sha256", None)
            metadata.pop("latest_review", None)

        metadata["reference_path_sha256"] = reference_path_fingerprint(new_strokes, metadata)
        cursor.execute(
            "UPDATE characters SET reference_strokes = %s, reference_strokes_svg = %s WHERE id = %s",
            (json.dumps(new_strokes, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False), character_id),
        )
        connection.commit()
        return {
            "message": "Reference drawing saved.",
            "character_id": character_id,
            "stroke_count": len(new_strokes),
            "provenance_status": metadata.get("provenance_status", "unverified"),
            "instructional_review_status": metadata.get("instructional_review_status", "pending"),
            "review_invalidated": geometry_changed,
            "rollback_backup": backup_path.name if backup_path else None,
        }

    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except OSError:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not create a rollback backup for this reference edit.")
    except (Error, ValueError, TypeError, json.JSONDecodeError):
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save the character reference drawing safely.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.get("/api/v1/characters/{character_id}/reference-strokes")
def get_character_reference_strokes(character_id: int):
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT c.reference_strokes, c.reference_strokes_svg FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Character was not found.")

        reference = row["reference_strokes"]
        if isinstance(reference, str):
            reference = json.loads(reference)
        source = row["reference_strokes_svg"]
        if isinstance(source, str):
            source = json.loads(source)

        if isinstance(source, dict):
            current_fingerprint = reference_path_fingerprint(reference or [], source)
            source["reference_path_sha256"] = current_fingerprint
            source["review_current"] = (
                source.get("instructional_review_status") == "approved"
                and source.get("reviewed_reference_sha256") == current_fingerprint
            )
            if source.get("instructional_review_status") == "approved" and not source["review_current"]:
                source["instructional_review_status"] = "pending"
                source["review_invalidated"] = True

        guidance = []
        if source and source.get("strokes"):
            stroke_items = source["strokes"]
            guidance = [
                {
                    "stroke_number": int(stroke["order"]),
                    "path_id": stroke.get("path_id"),
                    "direction_hint": "Follow the moving marker from the path start to its endpoint.",
                    "text": (
                        f"Stroke {stroke['order']} of {len(stroke_items)}. "
                        "Trace the highlighted reference path in the direction shown."
                    ),
                }
                for stroke in stroke_items
            ]
        elif reference:
            guidance = [
                {
                    "stroke_number": index + 1,
                    "path_id": None,
                    "direction_hint": "Follow the saved reference points in their listed order.",
                    "text": f"Trace reference stroke {index + 1} in order.",
                }
                for index, _stroke in enumerate(reference)
            ]

        available = bool(reference) or bool(source)
        return {
            "character_id": character_id,
            "stroke_data": reference,
            "reference_available": available,
            "reference_source": source,
            "stroke_guidance": guidance,
            "message": None if available else "Reference strokes not available yet",
        }

    except HTTPException:
        raise
    except Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the character reference drawing.",
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.post("/api/v1/characters/{character_id}/reference-review", status_code=201)
def record_character_reference_review(
    character_id: int,
    review: ReferenceReviewCreate,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """Record an administrator-attested language review of the exact saved paths."""
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")
    if review.decision == "approve" and not review.attests_exact_reference:
        raise HTTPException(
            status_code=422,
            detail="Approval requires attesting that the displayed reference was checked against the named standard.",
        )

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT c.reference_strokes, c.reference_strokes_svg FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Character was not found.")

        stroke_data = row.get("reference_strokes")
        if isinstance(stroke_data, str):
            stroke_data = json.loads(stroke_data)
        if not stroke_data:
            raise HTTPException(status_code=409, detail="A saved reference path is required before review.")

        metadata = row.get("reference_strokes_svg")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        if not isinstance(metadata, dict):
            metadata = {}

        if review.decision == "approve":
            provenance = metadata.get("provenance_status")
            license_text = str(metadata.get("license") or "").strip()
            has_source = bool(metadata.get("source_url") or metadata.get("source_file_url"))
            forbidden_license_markers = ("unverified", "not authorized", "do not redistribute")
            if provenance not in {"source_attributed", "verified"} or not has_source or not license_text:
                raise HTTPException(
                    status_code=409,
                    detail="Approval requires an attributed source URL and a recorded reuse license.",
                )
            if any(marker in license_text.lower() for marker in forbidden_license_markers):
                raise HTTPException(status_code=409, detail="The current source/license metadata does not allow approval.")

        fingerprint = reference_path_fingerprint(stroke_data, metadata)
        review_record = {
            "decision": review.decision,
            "reviewer_name": review.reviewer_name,
            "reviewer_qualification": review.reviewer_qualification,
            "reference_standard": review.reference_standard,
            "writing_convention": review.writing_convention,
            "notes": review.notes,
            "reviewed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reviewed_reference_sha256": fingerprint,
        }
        history = metadata.get("instructional_review_history")
        if not isinstance(history, list):
            history = []
        history.append(review_record)
        metadata["instructional_review_history"] = history
        metadata["latest_review"] = review_record
        metadata["instructional_review_status"] = "approved" if review.decision == "approve" else "pending"
        metadata["reference_path_sha256"] = fingerprint
        if review.decision == "approve":
            metadata["reviewed_reference_sha256"] = fingerprint
        else:
            metadata.pop("reviewed_reference_sha256", None)

        cursor.execute(
            "UPDATE characters SET reference_strokes_svg = %s WHERE id = %s",
            (json.dumps(metadata, ensure_ascii=False), character_id),
        )
        connection.commit()
        return {
            "message": "Reference review recorded.",
            "character_id": character_id,
            "decision": review.decision,
            "instructional_review_status": metadata["instructional_review_status"],
            "reviewed_reference_sha256": fingerprint,
            "reviewed_at_utc": review_record["reviewed_at_utc"],
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except (Error, ValueError, TypeError, json.JSONDecodeError):
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not record the reference review.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/v1/lessons/{lesson_id}/reference-audio")
def get_lesson_reference_audio(lesson_id: int):
    if lesson_id < 1:
        raise HTTPException(status_code=422, detail="Lesson ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ll.content_text, l.script_code
            FROM learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            WHERE ll.id = %s AND {script_filter}
            """.format(script_filter=_supported_script_clause("l")),
            (lesson_id, *SUPPORTED_SCRIPT_CODES),
        )
        lesson = cursor.fetchone()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson was not found.")
        voice_languages = {
            "ja-hiragana": "ja",
            "ja-katakana": "ja",
            "sa-devanagari": "hi",
            "ta": "ta",
            "zh-hans": "zh-CN",
        }
        voice_language = voice_languages.get(lesson["script_code"])
        if not voice_language:
            raise HTTPException(status_code=422, detail="Reference speech is not configured for this language yet.")
        audio_buffer = io.BytesIO()
        gTTS(text=lesson["content_text"], lang=voice_language, slow=False).write_to_fp(audio_buffer)
        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Could not create reference speech. Check the server’s internet connection and try again.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.get("/api/v1/lessons")
def get_learning_lessons(language_id: int | None = Query(default=None, gt=0), user_id: int | None = Query(default=None, gt=0), current_user_id: int | None = Depends(get_optional_user_id)):
    connection = None
    cursor = None
    if user_id is not None:
        require_user_scope(current_user_id, user_id)
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT
                ll.id,
                ll.language_id,
                l.name AS language_name,
                ll.category,
                ll.level,
                ll.unit_number,
                ll.lesson_order,
                ll.title,
                ll.content_text,
                ll.translation_text,
                ll.pronunciation_text,
                ll.explanation,
                ll.tutorial_video_url,
                ll.tutorial_video_status
            FROM learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            WHERE {script_filter}
        """.format(script_filter=_supported_script_clause("l"))
        parameters = list(SUPPORTED_SCRIPT_CODES)
        if language_id is not None:
            sql += " AND ll.language_id = %s"
            parameters.append(language_id)
        sql += " ORDER BY FIELD(ll.level, 'foundation', 'beginner', 'elementary', 'intermediate', 'advanced'), ll.unit_number, ll.lesson_order, ll.id"
        cursor.execute(sql, tuple(parameters))
        lessons = cursor.fetchall()
        if user_id is not None:
            cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Learner was not found.")
            unlock_cache = {}
            for lesson in lessons:
                key = (lesson["language_id"], lesson["level"], lesson["unit_number"])
                if key not in unlock_cache:
                    unlock_cache[key] = _lesson_is_unlocked(
                        cursor, user_id, lesson["language_id"], lesson["level"], lesson["unit_number"]
                    )
                lesson["is_unlocked"] = unlock_cache[key]
        return {"lessons": lessons}
    except Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve learning lessons. Run the database setup script first.",
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.get("/api/v1/lesson-progress")
def get_lesson_progress(user_id: int = Depends(get_current_user_id)):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT lp.lesson_id, lp.status, lp.score, lp.completed_at, lp.updated_at,
                   ll.language_id, l.name AS language_name, ll.title,
                   ll.level, ll.unit_number, ll.category
            FROM lesson_progress lp
            JOIN learning_lessons ll ON ll.id = lp.lesson_id
            JOIN languages l ON l.id = ll.language_id
            WHERE lp.user_id = %s AND {script_filter}
            ORDER BY lp.updated_at DESC, lp.lesson_id
            """.format(script_filter=_supported_script_clause("l")),
            (user_id, *SUPPORTED_SCRIPT_CODES),
        )
        return {"progress": cursor.fetchall()}
    except Error:
        raise HTTPException(status_code=500, detail="Could not retrieve lesson progress. Run the database setup script first.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/v1/lessons/{lesson_id}/progress")
def save_lesson_progress(lesson_id: int, progress: LessonProgressUpdate, current_user_id: int = Depends(get_current_user_id)):
    require_user_scope(current_user_id, progress.user_id)
    if lesson_id < 1:
        raise HTTPException(status_code=422, detail="Lesson ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT ll.id, ll.language_id, ll.level, ll.unit_number, ll.category, ll.content_text
                FROM learning_lessons ll
                JOIN languages l ON l.id = ll.language_id
                WHERE ll.id = %s AND {_supported_script_clause('l')}""",
            (lesson_id, *SUPPORTED_SCRIPT_CODES),
        )
        lesson = cursor.fetchone()
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson was not found.")
        if not _lesson_is_unlocked(
            cursor, current_user_id, lesson["language_id"], lesson["level"], lesson["unit_number"]
        ):
            level = str(lesson["level"] or "").casefold()
            detail = {
                "beginner": "Complete Foundation and the previous Beginner section quiz first.",
                "elementary": "Pass every Beginner section quiz to unlock Elementary.",
                "intermediate": "Complete all Elementary lessons to unlock Intermediate.",
                "advanced": "Complete all Intermediate lessons to unlock Advanced.",
            }.get(level, "Complete the prerequisite course level to unlock this lesson.")
            raise HTTPException(status_code=403, detail=detail)
        cursor.execute("SELECT id FROM users WHERE id = %s", (current_user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Learner was not found.")

        # Enforce character assessment requirements before allowing 'completed' status
        if progress.status == "completed" and str(lesson.get("category") or "").casefold() == "character":
            cursor.execute(
                "SELECT id, reference_strokes, reference_strokes_svg FROM characters WHERE language_id = %s AND character_text = %s LIMIT 1",
                (lesson["language_id"], lesson["content_text"]),
            )
            char_row = cursor.fetchone()
            if char_row:
                ref_st = char_row["reference_strokes"]
                if isinstance(ref_st, str):
                    ref_st = json.loads(ref_st)
                char_ref_class = _classify_stroke_reference(
                    _valid_strokes(ref_st), char_row.get("reference_strokes_svg")
                )
                cursor.execute(
                    """
                    SELECT id, handwriting_score, stroke_order_score, pronunciation_score, pronunciation_status, feedback
                    FROM practice_attempts
                    WHERE user_id = %s AND character_id = %s
                    ORDER BY id DESC LIMIT 1
                    """,
                    (current_user_id, char_row["id"]),
                )
                latest_att = cursor.fetchone()
                if not latest_att:
                    raise HTTPException(
                        status_code=409,
                        detail="Complete handwriting and pronunciation practice for this character before marking it completed.",
                    )
                fb_lower = str(latest_att.get("feedback") or "").lower()
                if (
                    "character mismatch:" in fb_lower
                    or "instead of" in fb_lower
                    or "empty_canvas" in fb_lower
                    or "insufficient ink" in fb_lower
                    or "low cnn confidence" in fb_lower
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Your latest drawing did not match the target character. Retry handwriting evaluation before marking completed.",
                    )
                att_status, att_passed, _ = _evaluate_handwriting_assessment(
                    latest_att["handwriting_score"],
                    latest_att["stroke_order_score"],
                    char_ref_class,
                )
                if not att_passed:
                    if att_status == "stroke_order_retry":
                        detail_msg = "Stroke order score is below 55%. Follow the stroke guide and retry before marking completed."
                    elif att_status == "provisional_reference_unverified":
                        detail_msg = "Stroke-order reference for this character is unverified/pending attribution; mandatory stroke-order completion cannot be certified yet."
                    else:
                        detail_msg = "Handwriting shape similarity must be at least 60% before marking this character completed."
                    raise HTTPException(status_code=409, detail=detail_msg)
                if (
                    latest_att["pronunciation_status"] != "completed"
                    or latest_att["pronunciation_score"] is None
                    or float(latest_att["pronunciation_score"]) < 60
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Complete Whisper pronunciation assessment (>= 60% transcript match) before marking this character completed.",
                    )
        cursor.execute(
            """
            INSERT INTO lesson_progress (user_id, lesson_id, status, score, completed_at)
            VALUES (%s, %s, %s, %s, CASE WHEN %s = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                score = VALUES(score),
                completed_at = CASE
                    WHEN VALUES(status) = 'completed' THEN COALESCE(completed_at, CURRENT_TIMESTAMP)
                    ELSE NULL
                END
            """,
            (current_user_id, lesson_id, progress.status, progress.score, progress.status),
        )
        connection.commit()
        return {
            "message": "Lesson progress saved.",
            "user_id": current_user_id,
            "lesson_id": lesson_id,
            "status": progress.status,
            "score": progress.score,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save lesson progress.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/v1/lessons/{lesson_id}/video")
def get_lesson_video(lesson_id: int, variant: str | None = Query(default=None, max_length=40)):
    if lesson_id < 1:
        raise HTTPException(status_code=422, detail="Lesson ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT ll.id, ll.tutorial_video_url, ll.tutorial_video_status
                FROM learning_lessons ll
                JOIN languages l ON l.id = ll.language_id
                WHERE ll.id = %s AND {_supported_script_clause('l')}""",
            (lesson_id, *SUPPORTED_SCRIPT_CODES),
        )
        lesson = cursor.fetchone()
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson was not found.")

        if variant is not None and not re.fullmatch(r"[a-z0-9-]{1,40}", variant):
            raise HTTPException(status_code=422, detail="Video variant must be a lowercase filename suffix.")

        static_videos_dir = Path(__file__).resolve().parent / "static" / "videos"
        # Keep the database's published lesson URL working while routing its
        # improved, visibly animated teacher clip to the newer versioned asset.
        effective_variant = (
            "female-lipsync-v5"
            if (lesson_id == 61 and variant in ("female-lipsync-v4", "teacher-static-v2"))
            else variant
        )
        variant_suffix = f"_{effective_variant}" if effective_variant else ""
        matching_videos = list(static_videos_dir.glob(f"*_lesson{lesson_id}{variant_suffix}.mp4"))
        if not matching_videos or not matching_videos[0].is_file():
            raise HTTPException(
                status_code=404,
                detail="Tutorial video file has not been generated for this lesson.",
            )

        video_path = matching_videos[0]
        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=video_path.name,
        )
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Database error verifying lesson video.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/v1/lessons/{lesson_id}/tutorial-video")
def save_lesson_tutorial_video(lesson_id: int, video: TutorialVideoUpdate, current_admin_id: int = Depends(get_current_admin_user_id)):
    if lesson_id < 1:
        raise HTTPException(status_code=422, detail="Lesson ID must be positive.")
    if video.status == "ready" and not video.video_url:
        raise HTTPException(status_code=422, detail="A video URL is required when status is ready.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT ll.id FROM learning_lessons ll
                JOIN languages l ON l.id = ll.language_id
                WHERE ll.id = %s AND {_supported_script_clause('l')}""",
            (lesson_id, *SUPPORTED_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Lesson was not found.")
        cursor.execute(
            "UPDATE learning_lessons SET tutorial_video_url = %s, tutorial_video_status = %s WHERE id = %s",
            (video.video_url, video.status, lesson_id),
        )
        connection.commit()
        return {
            "message": "Tutorial video details saved.",
            "lesson_id": lesson_id,
            "video_url": video.video_url,
            "status": video.status,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save tutorial video details.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# 5. GET ALL LANGUAGES
# --------------------------------------------------
# GET /api/v1/languages
# Retrieves the available languages from MySQL.

@app.get("/api/v1/languages")
def get_languages():
    connection = None
    cursor = None

    try:
        # Connect to the StrokeSpeak database.
        connection = get_db_connection()

        # dictionary=True returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Retrieve language information in alphabetical order.
        cursor.execute(
            f"""
            SELECT
                id,
                CASE script_code
                    WHEN 'sa-devanagari' THEN 'Sanskrit (Devanagari)'
                    WHEN 'zh-hans' THEN 'Simplified Chinese'
                    ELSE name
                END AS name,
                script_code
            FROM languages
            WHERE {_supported_script_clause('languages')}
            ORDER BY name
            """,
            SUPPORTED_SCRIPT_CODES,
        )

        # Present the agreed four public languages. Japanese has two internal
        # character-language rows, which the single Japanese tutor loads together.
        rows = cursor.fetchall()
        rows_by_script = {row["script_code"]: row for row in rows}
        public_languages = []
        hiragana = rows_by_script.get("ja-hiragana")
        if hiragana:
            katakana = rows_by_script.get("ja-katakana")
            japanese = {
                "id": hiragana["id"],
                "name": "Japanese",
                "script_code": "ja-hiragana",
                "character_language_ids": [hiragana["id"]] + ([katakana["id"]] if katakana else []),
            }
            public_languages.append(japanese)
        for script_code in ("sa-devanagari", "ta", "zh-hans"):
            language = rows_by_script.get(script_code)
            if language:
                public_languages.append(language)
        public_languages.sort(key=lambda language: language["name"])
        return {"languages": public_languages}

    except Error:
        # Return an HTTP 500 response if MySQL fails.
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve languages from the database."
        )

    finally:
        # Always close database resources.
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/v1/languages/{language_id}")
def get_language(language_id: int):
    if language_id < 1:
        raise HTTPException(status_code=422, detail="Language ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"SELECT id, name, script_code FROM languages WHERE id = %s AND {_supported_script_clause('languages')}",
            (language_id, *SUPPORTED_SCRIPT_CODES),
        )
        language = cursor.fetchone()
        if language is None:
            raise HTTPException(status_code=404, detail="Language was not found.")
        return {"language": language}
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not retrieve the language.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/v1/languages/{language_id}")
def update_language(language_id: int, language: LanguageCreate, current_admin_id: int = Depends(get_current_admin_user_id)):
    if language_id < 1:
        raise HTTPException(status_code=422, detail="Language ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT id FROM languages WHERE id = %s AND {_supported_script_clause('languages')}",
            (language_id, *SUPPORTED_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Language was not found.")
        cursor.execute(
            "UPDATE languages SET name = %s, script_code = %s WHERE id = %s",
            (language.name, language.script_code, language_id),
        )
        connection.commit()
        return {
            "message": "Language updated successfully.",
            "id": language_id,
            "name": language.name,
            "script_code": language.script_code,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except IntegrityError:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=409, detail="This script code already exists.")
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not update the language.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
# 6. ADD A NEW LANGUAGE
# --------------------------------------------------
# POST /api/v1/languages
# Expects JSON containing name and script_code.

@app.post("/api/v1/languages", status_code=201)
def create_language(language: LanguageCreate, current_admin_id: int = Depends(get_current_admin_user_id)):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert the new language using parameterized SQL.
        # Parameters help prevent SQL injection.
        cursor.execute(
            "INSERT INTO languages (name, script_code) VALUES (%s, %s)",
            (language.name, language.script_code)
        )

        # Save the changes permanently.
        connection.commit()

        # Return the newly created language's database ID.
        return {
            "message": "Language added successfully!",
            "id": cursor.lastrowid,
            "name": language.name,
            "script_code": language.script_code
        }

    except IntegrityError:
        # Undo changes if a database constraint fails.
        if connection and connection.is_connected():
            connection.rollback()

        # For example, the script_code may already exist.
        raise HTTPException(
            status_code=409,
            detail="This script code already exists."
        )

    except Error:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not save the language."
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
# 7. VALIDATE CHARACTER INPUT
# --------------------------------------------------
# This model defines the data needed to add a character.

class CharacterCreate(BaseModel):
    # ID of an existing language in the languages table.
    language_id: int = Field(gt=0)

    # The actual written character, e.g. あ or अ.
    character_text: str = Field(min_length=1, max_length=20)

    # A short explanation of the character.
    meaning: str = Field(min_length=1, max_length=255)

    # The character's expected pronunciation.
    pronunciation_text: str = Field(min_length=1, max_length=100)

    # Reject blank strings and remove surrounding spaces.
    @field_validator(
        "character_text",
        "meaning",
        "pronunciation_text"
    )
    @classmethod
    def validate_character_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


# --------------------------------------------------
# 8. GET CHARACTERS
# --------------------------------------------------
# GET /api/v1/characters
# Retrieves characters along with their language names.
# An optional language_id query parameter filters the results.
# Example: /api/v1/characters?language_id=6

@app.get("/api/v1/characters")
def get_characters(language_id: int | None = Query(default=None, gt=0)):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # JOIN connects each character to its language.
        sql = """
            SELECT
                c.id,
                c.language_id,
                l.name AS language_name,
                c.character_text,
                c.meaning,
                c.pronunciation_text,
                (c.reference_strokes IS NOT NULL AND JSON_LENGTH(c.reference_strokes) > 0) AS has_reference
            FROM characters c
            JOIN languages l ON c.language_id = l.id
            WHERE {script_filter}
        """.format(script_filter=_supported_script_clause("l"))
        parameters = list(SUPPORTED_SCRIPT_CODES)

        # Add a filter only when language_id was provided.
        if language_id is not None:
            sql += " AND c.language_id = %s"
            parameters.append(language_id)

        sql += """
            ORDER BY
                CASE l.script_code
                    WHEN 'ja-hiragana' THEN FIELD(c.character_text, 'あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ', 'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ', 'て', 'と', 'な', 'に', 'ぬ', 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ま', 'み', 'む', 'め', 'も', 'や', 'ゆ', 'よ', 'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'を', 'ん')
                    WHEN 'ja-katakana' THEN FIELD(c.character_text, 'ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ', 'コ', 'サ', 'シ', 'ス', 'セ', 'ソ', 'タ', 'チ', 'ツ', 'テ', 'ト', 'ナ', 'ニ', 'ヌ', 'ネ', 'ノ', 'ハ', 'ヒ', 'フ', 'ヘ', 'ホ', 'マ', 'ミ', 'ム', 'メ', 'モ', 'ヤ', 'ユ', 'ヨ', 'ラ', 'リ', 'ル', 'レ', 'ロ', 'ワ', 'ヲ', 'ン')
                    ELSE c.id
                END, c.id
        """
        cursor.execute(sql, tuple(parameters))
        characters = [c for c in cursor.fetchall() if c["id"] not in HIDDEN_TEST_CHARACTER_IDS]

        return {"characters": characters}

    except Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve characters from the database."
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/v1/characters/{character_id}")
def get_character(character_id: int):
    if character_id in HIDDEN_TEST_CHARACTER_IDS:
        raise HTTPException(status_code=404, detail="Character was not found.")
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.id, c.language_id, l.name AS language_name,
                   c.character_text, c.meaning, c.pronunciation_text,
                   (c.reference_strokes IS NOT NULL AND JSON_LENGTH(c.reference_strokes) > 0) AS has_reference
            FROM characters c
            JOIN languages l ON c.language_id = l.id
            WHERE c.id = %s AND {script_filter}
            """.format(script_filter=_supported_script_clause("l")),
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        character = cursor.fetchone()
        if character is None:
            raise HTTPException(status_code=404, detail="Character was not found.")
        return {"character": character}
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not retrieve the character.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/v1/characters/{character_id}")
def update_character(character_id: int, character: CharacterCreate, current_admin_id: int = Depends(get_current_admin_user_id)):
    if character_id < 1:
        raise HTTPException(status_code=422, detail="Character ID must be positive.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT c.id FROM characters c
                JOIN languages l ON l.id = c.language_id
                WHERE c.id = %s AND {_supported_script_clause('l')}""",
            (character_id, *SUPPORTED_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Character was not found.")
        cursor.execute(
            f"SELECT id FROM languages WHERE id = %s AND {_supported_script_clause('languages')}",
            (character.language_id, *SUPPORTED_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="The selected language was not found or is not supported.")
        cursor.execute(
            """
            UPDATE characters
            SET language_id = %s, character_text = %s, meaning = %s, pronunciation_text = %s
            WHERE id = %s
            """,
            (
                character.language_id,
                character.character_text,
                character.meaning,
                character.pronunciation_text,
                character_id,
            ),
        )
        connection.commit()
        return {
            "message": "Character updated successfully.",
            "id": character_id,
            "language_id": character.language_id,
            "character_text": character.character_text,
            "meaning": character.meaning,
            "pronunciation_text": character.pronunciation_text,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except IntegrityError:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=409, detail="This character already exists for the selected language.")
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not update the character.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
# 9. ADD A NEW CHARACTER
# --------------------------------------------------
# POST /api/v1/characters
# Adds a character belonging to an existing language.

@app.post("/api/v1/characters", status_code=201)
def create_character(character: CharacterCreate, current_admin_id: int = Depends(get_current_admin_user_id)):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # First, confirm that the requested language exists.
        cursor.execute(
            f"SELECT id FROM languages WHERE id = %s AND {_supported_script_clause('languages')}",
            (character.language_id, *SUPPORTED_SCRIPT_CODES)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Language not found. Check language_id "
                    "using GET /api/v1/languages."
                )
            )

        # Insert the character into the characters table.
        cursor.execute(
            """
            INSERT INTO characters
                (language_id, character_text, meaning, pronunciation_text)
            VALUES (%s, %s, %s, %s)
            """,
            (
                character.language_id,
                character.character_text,
                character.meaning,
                character.pronunciation_text
            )
        )

        # Save the inserted record.
        connection.commit()

        # Return details of the newly created character.
        return {
            "message": "Character added successfully!",
            "id": cursor.lastrowid,
            "language_id": character.language_id,
            "character_text": character.character_text,
            "meaning": character.meaning,
            "pronunciation_text": character.pronunciation_text
        }

    except HTTPException:
        # Preserve deliberate HTTP errors such as 404.
        raise

    except IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()

        # Commonly occurs if the same character is inserted
        # twice for a language with a unique constraint.
        raise HTTPException(
            status_code=409,
            detail="This character already exists for the selected language."
        )

    except Error:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not save the character. Check the database schema."
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
















# touch
