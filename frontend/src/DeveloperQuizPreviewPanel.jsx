import { useEffect, useState } from 'react'
import { apiFetch } from './api'

export default function DeveloperQuizPreviewPanel() {
  const [quizzes, setQuizzes] = useState([])
  const [quizId, setQuizId] = useState('')
  const [preview, setPreview] = useState(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadQuizzes() {
      setLoadingList(true)
      setMessage('')
      try {
        const response = await apiFetch('/api/v1/admin/section-quizzes')
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || 'Could not load developer quiz preview.')
        if (cancelled) return
        const items = data.quizzes || []
        setQuizzes(items)
        setQuizId((current) => items.some((item) => String(item.id) === String(current)) ? current : String(items[0]?.id || ''))
      } catch (error) {
        if (!cancelled) setMessage(error.message || 'Could not load developer quiz preview.')
      } finally {
        if (!cancelled) setLoadingList(false)
      }
    }
    loadQuizzes()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!quizId) return undefined
    let cancelled = false
    async function loadPreview() {
      setLoadingPreview(true)
      setMessage('')
      setPreview(null)
      try {
        const response = await apiFetch('/api/v1/admin/section-quizzes/' + quizId + '/preview')
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || 'Could not load this quiz preview.')
        if (!cancelled) setPreview(data)
      } catch (error) {
        if (!cancelled) setMessage(error.message || 'Could not load this quiz preview.')
      } finally {
        if (!cancelled) setLoadingPreview(false)
      }
    }
    loadPreview()
    return () => { cancelled = true }
  }, [quizId])

  return (
    <section className="mt-5 rounded-2xl border border-indigo-200 bg-white p-5 shadow-sm" aria-labelledby="developer-quiz-preview-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="inline-flex rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-indigo-800">Developer Mode</span>
          <h2 id="developer-quiz-preview-title" className="mt-3 text-xl font-bold text-slate-900">Read-only quiz answer preview</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">Review every available quiz across Japanese Hiragana and Katakana, Sanskrit, Tamil, and Chinese. This page does not create attempts or change learner progress.</p>
        </div>
        <label className="min-w-64 text-sm font-semibold text-slate-700">Choose a quiz
          <select className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2" value={quizId} onChange={(event) => setQuizId(event.target.value)} disabled={loadingList || quizzes.length === 0}>
            {quizzes.map((quiz) => <option key={quiz.id} value={quiz.id}>{quiz.language_name} · {quiz.level === 'foundation' ? 'Foundation final quiz' : quiz.level + ' · Unit ' + quiz.unit_number} ({quiz.question_count} questions)</option>)}
          </select>
        </label>
      </div>
      {(loadingList || loadingPreview) && <p className="mt-5 text-sm text-slate-600" role="status">{loadingList ? 'Loading quizzes…' : 'Loading answer key…'}</p>}
      {message && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-800" role="alert">{message}</p>}
      {!loadingList && quizzes.length === 0 && !message && <p className="mt-5 text-sm text-slate-600">No quizzes are currently available to preview.</p>}
      {preview && !loadingPreview && (
        <div className="mt-5 space-y-4">
          <div className="rounded-xl bg-slate-50 p-4">
            <h3 className="font-bold text-slate-900">{preview.quiz.language_name} · {preview.quiz.level === 'foundation' ? 'Foundation final quiz' : preview.quiz.level + ' · Unit ' + preview.quiz.unit_number}</h3>
            <p className="mt-1 text-sm text-slate-600">Pass mark: {preview.quiz.pass_percentage}% · {preview.questions.length} questions</p>
          </div>
          {preview.questions.map((question) => (
            <article key={question.id} className="rounded-xl border border-slate-200 p-4">
              <h4 className="font-semibold text-slate-900">{question.question_order}. {question.prompt}</h4>
              <ol className="mt-3 grid gap-2 sm:grid-cols-2">
                {question.options.map((option, index) => (
                  <li key={index} className={'rounded-lg border px-3 py-2 text-sm ' + (index === question.correct_option_index ? 'border-emerald-300 bg-emerald-50 font-semibold text-emerald-900' : 'border-slate-200 bg-slate-50 text-slate-700')}>
                    <span dir="auto">{option}</span>{index === question.correct_option_index && <span className="ml-2 text-xs uppercase tracking-wide">Correct answer</span>}
                  </li>
                ))}
              </ol>
              {question.explanation && <p className="mt-3 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-950"><strong>Explanation:</strong> {question.explanation}</p>}
              {question.source_lesson_title && <p className="mt-2 text-xs text-slate-500">Related lesson: {question.source_lesson_title}</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
