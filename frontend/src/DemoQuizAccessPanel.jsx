import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiFetch } from './api'
import SectionQuizPanel from './SectionQuizPanel'

const PUBLIC_SCRIPT_CODES = new Set(['ja-hiragana', 'ja-katakana', 'sa-devanagari', 'ta', 'zh-hans'])

export default function DemoQuizAccessPanel({ languages, learnerId }) {
  const [quizzes, setQuizzes] = useState([])
  const [quizId, setQuizId] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const publicLanguages = useMemo(() => (languages || []).filter((language) => PUBLIC_SCRIPT_CODES.has(language.script_code)), [languages])

  const requestQuizzes = useCallback(async () => {
    const results = await Promise.allSettled(publicLanguages.map(async (language) => {
      const response = await apiFetch('/api/v1/section-quizzes?language_id=' + language.id + '&user_id=' + learnerId)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not load quizzes for ' + language.name + '.')
      return data.quizzes || []
    }))
    const loaded = results.filter((item) => item.status === 'fulfilled').flatMap((item) => item.value)
    const failures = results.filter((item) => item.status === 'rejected')
    const notice = failures.length
      ? loaded.length ? 'Some language quiz lists could not load. You can still use the available quizzes below.' : failures[0].reason?.message || 'Could not load quizzes.'
      : ''
    return { quizzes: loaded, notice }
  }, [learnerId, publicLanguages])

  useEffect(() => {
    let cancelled = false
    requestQuizzes().then((result) => {
      if (cancelled) return
      setQuizzes(result.quizzes)
      setQuizId((current) => result.quizzes.some((quiz) => String(quiz.id) === String(current)) ? current : String(result.quizzes[0]?.id || ''))
      setMessage(result.notice)
      setLoading(false)
    }).catch((error) => {
      if (cancelled) return
      setMessage(error.message || 'Could not load quizzes.')
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [requestQuizzes])

  async function refreshQuizzes() {
    setLoading(true)
    setMessage('')
    try {
      const result = await requestQuizzes()
      setQuizzes(result.quizzes)
      setQuizId((current) => result.quizzes.some((quiz) => String(quiz.id) === String(current)) ? current : String(result.quizzes[0]?.id || ''))
      setMessage(result.notice)
    } catch (error) {
      setMessage(error.message || 'Could not load quizzes.')
    } finally {
      setLoading(false)
    }
  }

  const selectedQuiz = quizzes.find((quiz) => String(quiz.id) === String(quizId)) || null

  return (
    <section className="mt-5 rounded-2xl border border-violet-200 bg-white p-5 shadow-sm" aria-labelledby="demo-quiz-access-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="inline-flex rounded-full bg-violet-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-violet-800">Demo quiz access</span>
          <h2 id="demo-quiz-access-title" className="mt-3 text-xl font-bold text-slate-900">Quiz practice across all languages</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">Choose any available quiz in Japanese, Sanskrit, Tamil, or Chinese. You must answer and submit it yourself. Correct answers appear only after submission. Lesson and chapter unlocks still require the normal course progress.</p>
        </div>
        <label className="min-w-64 text-sm font-semibold text-slate-700">Choose a quiz
          <select className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2" value={quizId} onChange={(event) => setQuizId(event.target.value)} disabled={loading || quizzes.length === 0}>
            {quizzes.map((quiz) => <option key={quiz.id} value={quiz.id}>{quiz.language_name} · {quiz.level === 'foundation' ? 'Foundation final quiz' : quiz.level + ' · Unit ' + quiz.unit_number}</option>)}
          </select>
        </label>
      </div>
      {loading && <p className="mt-4 text-sm text-slate-600" role="status">Loading available quizzes…</p>}
      {message && <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900" role="status">{message}</p>}
      {!loading && quizzes.length === 0 && !message && <p className="mt-4 text-sm text-slate-600">No quizzes are currently available. Check again later.</p>}
      {selectedQuiz && <SectionQuizPanel key={selectedQuiz.id} quiz={selectedQuiz} learnerId={learnerId} onUpdated={refreshQuizzes} />}
    </section>
  )
}
