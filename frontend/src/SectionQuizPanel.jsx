import { useState } from 'react'
import { apiFetch } from './api'

export default function SectionQuizPanel({ quiz, learnerId, onUpdated }) {
  const [questions, setQuestions] = useState([])
  const [history, setHistory] = useState([])
  const [answers, setAnswers] = useState({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  if (!quiz) return null

  async function startQuiz() {
    setLoading(true)
    setMessage('')
    setResult(null)
    setAnswers({})
    setCurrentQuestionIndex(0)
    try {
      const response = await apiFetch('/api/v1/section-quizzes/' + quiz.id + '?user_id=' + learnerId)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not open this quiz.')
      setQuestions(data.questions || [])
      setHistory(data.history || [])
    } catch (error) {
      setMessage(error.message || 'Could not open this quiz.')
    } finally {
      setLoading(false)
    }
  }

  async function submitQuiz() {
    if (questions.some((question) => answers[question.id] === undefined)) {
      setMessage('Choose one answer for every question before submitting.')
      return
    }
    setLoading(true)
    setMessage('')
    try {
      const response = await apiFetch('/api/v1/section-quizzes/' + quiz.id + '/attempts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(learnerId),
          answers: questions.map((question) => ({
            question_id: question.id,
            selected_option_index: Number(answers[question.id]),
          })),
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not save your quiz attempt.')
      setResult(data)
      setHistory((current) => [{
        id: data.attempt_id,
        score: data.score,
        passed: data.passed,
        created_at: new Date().toISOString(),
      }, ...current].slice(0, 10))
      setQuestions([])
      setAnswers({})
      setCurrentQuestionIndex(0)
      await onUpdated?.()
    } catch (error) {
      setMessage(error.message || 'Could not save your quiz attempt.')
    } finally {
      setLoading(false)
    }
  }

  const isFoundationAssessment = quiz.level === 'foundation'
  const unavailableMessage = !quiz.quiz_available
    ? !quiz.is_unlocked
      ? 'Locked: finish the previous course section and pass its quiz first.'
      : isFoundationAssessment
        ? 'Complete all Foundation lessons first (' + quiz.completed_lessons + '/' + quiz.lesson_count + ' complete).'
        : 'Complete all ' + quiz.lesson_count + ' lessons in this unit first (' + quiz.completed_lessons + '/' + quiz.lesson_count + ' complete).'
    : ''
  const canAdvanceNormally = quiz.developer_mode || (quiz.is_unlocked && quiz.lessons_complete)
  const currentQuestion = questions[currentQuestionIndex]
  const answeredCount = questions.filter((question) => answers[question.id] !== undefined).length

  return (
    <>
    <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/70 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h5 className="font-semibold text-indigo-950">{isFoundationAssessment ? 'Foundation Final Quiz' : 'Unit quiz'}</h5>
          <p className="mt-1 text-sm text-slate-700">
            Pass mark: {Number(quiz.pass_percentage)}% · {quiz.attempt_count} attempt{quiz.attempt_count === 1 ? '' : 's'}
            {quiz.best_score !== null && quiz.best_score !== undefined ? ' · Best: ' + Math.round(Number(quiz.best_score)) + '%' : ''}
          </p>
          {unavailableMessage && <p className="mt-2 text-sm text-amber-800">{unavailableMessage}</p>}
          {quiz.developer_mode && <p className="mt-2 text-sm text-indigo-800">Developer Mode: course content and quizzes are available for review. Quiz preview does not change learner progress.</p>}
          {quiz.demo_quiz_access && !quiz.developer_mode && <p className="mt-2 text-sm text-indigo-800">Demo quiz access: you may attempt quizzes early. Lesson and chapter unlocks still follow the normal learning path.</p>}
          {quiz.lesson_requirement_override && !quiz.demo_quiz_access && !quiz.developer_mode && <p className="mt-2 text-sm text-indigo-800">Early access is enabled for this account. Taking the quiz will not mark lessons complete.</p>}
          {quiz.passed && <p className="mt-2 text-sm font-semibold text-emerald-800">{canAdvanceNormally ? (isFoundationAssessment ? 'Passed. Beginner is now unlocked.' : 'Passed. The next course section is unlocked.') : 'Quiz passed. Complete the normal lesson prerequisites to unlock the next section.'}</p>}
          {result && (
            <p role="status" aria-live="polite" className={'mt-2 text-sm font-semibold ' + (result.passed ? 'text-emerald-800' : 'text-amber-800')}>
              {result.feedback} Score: {Math.round(Number(result.score))}% ({result.correct_count}/{result.question_count}).
            </p>
          )}
          {message && <p role="alert" className="mt-2 text-sm text-rose-700">{message}</p>}
        </div>
        {questions.length === 0 && (
          <button
            type="button"
            disabled={loading || !quiz.quiz_available}
            onClick={startQuiz}
            className="rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Loading…' : isFoundationAssessment
              ? quiz.attempt_count ? 'Retake Foundation Final Quiz' : 'Take Foundation Final Quiz'
              : quiz.attempt_count ? 'Retake unit quiz' : 'Take unit quiz'}
          </button>
        )}
      </div>

      {questions.length > 0 && currentQuestion && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-700" aria-live="polite">
              Question {currentQuestionIndex + 1} of {questions.length} · {answeredCount} answered
            </p>
            <div className="flex flex-wrap gap-1" role="group" aria-label="Question navigation">
              {questions.map((question, index) => {
                const isAnswered = answers[question.id] !== undefined
                const isCurrent = index === currentQuestionIndex
                return (
                  <button
                    key={question.id}
                    type="button"
                    aria-label={'Go to question ' + (index + 1) + (isAnswered ? ', answered' : ', unanswered')}
                    aria-current={isCurrent ? 'step' : undefined}
                    onClick={() => setCurrentQuestionIndex(index)}
                    className={'min-h-9 min-w-9 rounded-md border px-2 text-sm font-semibold ' + (isCurrent
                      ? 'border-indigo-700 bg-indigo-700 text-white'
                      : isAnswered
                        ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                        : 'border-slate-300 bg-white text-slate-700 hover:bg-indigo-50')}
                  >
                    {index + 1}
                  </button>
                )
              })}
            </div>
          </div>

          <fieldset className="rounded-lg border border-indigo-100 bg-white p-4">
            <legend className="px-1 text-base font-semibold text-slate-900">
              {currentQuestionIndex + 1}. {currentQuestion.prompt}
            </legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {currentQuestion.options.map((option, optionIndex) => (
                <label key={currentQuestion.id + '-' + optionIndex} className="flex cursor-pointer items-start gap-2 rounded-md border border-slate-200 p-3 text-sm hover:bg-indigo-50 has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-50">
                  <input
                    type="radio"
                    name={'quiz-' + quiz.id + '-question-' + currentQuestion.id}
                    value={optionIndex}
                    checked={Number(answers[currentQuestion.id]) === optionIndex}
                    onChange={() => setAnswers((current) => ({ ...current, [currentQuestion.id]: optionIndex }))}
                  />
                  <span dir="auto">{option}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              type="button"
              disabled={loading || currentQuestionIndex === 0}
              onClick={() => setCurrentQuestionIndex((index) => Math.max(0, index - 1))}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={loading || currentQuestionIndex === questions.length - 1}
              onClick={() => setCurrentQuestionIndex((index) => Math.min(questions.length - 1, index + 1))}
              className="rounded-lg border border-indigo-300 bg-white px-4 py-2 text-sm font-semibold text-indigo-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={submitQuiz}
              className="rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Submitting…' : 'Submit quiz'}
            </button>
          </div>
        </div>
      )}

      {result?.answers?.length > 0 && (
        <section className="mt-5 space-y-3" aria-label="Answer review">
          <h6 className="font-semibold text-slate-900">Answer review</h6>
          {result.answers.map((answer) => (
            <article key={answer.question_id} className={'rounded-lg border p-3 ' + (answer.correct ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50')}>
              <p className="font-medium text-slate-900">{answer.question_order}. {answer.prompt}</p>
              <p className={'mt-2 text-sm font-semibold ' + (answer.correct ? 'text-emerald-800' : 'text-amber-900')}>
                {answer.correct ? 'Correct' : 'Incorrect'}
              </p>
              <p className="mt-1 text-sm text-slate-700">Your answer: <span dir="auto">{answer.selected_option}</span></p>
              <p className="mt-1 text-sm text-slate-700">Correct answer: <strong dir="auto">{answer.correct_option}</strong></p>
              {answer.teaching_notes?.length > 0 && (
                <div className="mt-2 space-y-1 text-sm text-slate-600">
                  {answer.teaching_notes.map((note, index) => <p key={index}>{note}</p>)}
                </div>
              )}
            </article>
          ))}
        </section>
      )}

      {history.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm font-medium text-indigo-800">Recent quiz attempts</summary>
          <ul className="mt-2 space-y-1 text-xs text-slate-600">
            {history.slice(0, 5).map((attempt) => (
              <li key={attempt.id}>
                {Math.round(Number(attempt.score))}% · {attempt.passed ? 'Passed' : 'Try again'} · {new Date(attempt.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
    </>
  )
}
