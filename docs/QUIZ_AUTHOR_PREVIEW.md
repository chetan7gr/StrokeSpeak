# Creator Quiz Preview

Use this workflow to inspect or try a quiz without completing lessons as a learner. Preview grading does not create a quiz attempt or change learner progress. Normal learner quiz submission still follows the lesson and quiz prerequisites.

## Configure your own account as an administrator

1. Start the backend and sign in to your own account from the app or the API docs at `http://127.0.0.1:8000/docs`.
2. In the docs, authorize with your Bearer token and call `GET /api/v1/auth/me`. Note the `user.id` for the account you control.
3. Stop the backend. In `backend/.env`, set the administrator list to your account ID, for example `STROKESPEAK_ADMIN_USER_IDS=4` only if the returned ID is 4. Keep any existing secret and database settings private.
4. Restart the backend and sign in again. `GET /api/v1/auth/me` should show `role: admin` for that account.

Do not assign another learner's account as an administrator. The environment variable may contain multiple comma-separated IDs when deliberately configured.

## Find a quiz ID

With your own signed-in account, call `GET /api/v1/section-quizzes?language_id=<your-language-id>&user_id=<your-account-id>`. This lists quiz IDs and learner availability. A quiz can remain locked for normal submission while still being available to an administrator through preview.

## Preview questions and answer key

Call `GET /api/v1/admin/section-quizzes/<quiz-id>/preview`. The response includes the questions, choices, and correct answer for review. This is read-only.

## Try the quiz without recording an attempt

Call `POST /api/v1/admin/section-quizzes/<quiz-id>/preview-grade` with an answer for every question, for example:

```json
{
  "answers": [
    {"question_id": 101, "selected_option_index": 0},
    {"question_id": 102, "selected_option_index": 2},
    {"question_id": 103, "selected_option_index": 1}
  ]
}
```

Use the actual question IDs and option indexes from the preview response. The result reports the score and whether the learner would pass. It does not write a `section_quiz_attempts` row and does not unlock any learner course section.

For real progression validation, use a separate test learner and complete the genuine prerequisite flow. Do not edit or fabricate learner progress to test it.
