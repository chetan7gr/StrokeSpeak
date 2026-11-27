import { useEffect, useRef, useState } from 'react'
import './App.css'
import SectionQuizPanel from './SectionQuizPanel'
import DeveloperQuizPreviewPanel from './DeveloperQuizPreviewPanel'
import DemoQuizAccessPanel from './DemoQuizAccessPanel'
import AuthPanel from './AuthPanel'
import BrandLogo from './BrandLogo'
import { apiFetch, clearAuthToken, getAuthToken, setAuthToken } from './api'

const devanagariStrokeGuides = {
  'अ': { file: 'Devanagari a अ.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'आ': { file: 'Devanagari aa आ.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'इ': { file: 'Devanagari i इ.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'ई': { file: 'Devanagari ii ई.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'उ': { file: 'Devanagari u उ.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'ऊ': { file: 'Devanagari uu ऊ.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'क': { file: 'Deva-क-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'ख': { file: 'Deva-ख-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'ग': { file: 'Deva-ग-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'म': { file: 'Devanagari m म.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'न': { file: 'Devanagari n न.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'प': { file: 'Deva-प-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'र': { file: 'Deva-र-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'ह': { file: 'Deva-ह-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'य': { file: 'Deva-य-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'स': { file: 'Devanagari s स.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'ल': { file: 'Devanagari l ल.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
  'त': { file: 'Deva-त-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'द': { file: 'Deva-द-order.gif', author: 'Opiaterein', license: 'CC BY 3.0', licenseUrl: 'https://creativecommons.org/licenses/by/3.0/' },
  'ब': { file: 'Devanagari b ब.gif', author: 'JackPotte', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/' },
}

const FEATURED_LESSON_IDS = new Set([
  // Japanese Foundation: あ, い, う, え, お
  61, 62, 63, 64, 65,
  // Japanese Beginner: Unit 1 everyday vocabulary
  316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326,
  // Sanskrit Foundation: अ, आ, इ, ई, उ
  339, 340, 341, 342, 343,
  // Sanskrit Beginner: नमस्ते, जलम्, मित्रम्, पुस्तकम्
  344, 345, 346, 347,
  // Tamil Foundation: அ, ஆ, இ, ஈ, உ
  223, 224, 225, 226, 227,
  // Tamil Beginner: வணக்கம், நன்றி, புத்தகம், தண்ணீர் + நான் தண்ணீர் குடிக்கிறேன்.
  353, 354, 355, 356, 302,
  // Simplified Chinese Foundation prototype: 一, 二, 三, 人, 大
  348, 349, 350, 351, 352,
])

const DRAWING_CANVAS_WIDTH = 700
const DRAWING_CANVAS_HEIGHT = 320
const REFERENCE_DRAW_AREA_SIZE = Math.min(DRAWING_CANVAS_WIDTH, DRAWING_CANVAS_HEIGHT)

function parseReferenceViewBox(value) {
  const values = String(value || '0 0 1 1').trim().split(/[\s,]+/).map(Number)
  if (values.length === 4 && values.every(Number.isFinite) && values[2] > 0 && values[3] > 0) {
    return { minX: values[0], minY: values[1], width: values[2], height: values[3] }
  }
  return { minX: 0, minY: 0, width: 1, height: 1 }
}

function getCharacterFontFamily(characterText) {
  const codePoint = Array.from(characterText || '')[0]?.codePointAt(0) || 0
  if ((codePoint >= 0x3040 && codePoint <= 0x30ff) || (codePoint >= 0x31f0 && codePoint <= 0x31ff)) {
    return '"Noto Sans JP", "Yu Gothic UI", Meiryo, "MS Gothic", sans-serif'
  }
  if (codePoint >= 0x0900 && codePoint <= 0x097f) {
    return '"Noto Sans Devanagari", "Nirmala UI", Mangal, sans-serif'
  }
  if (codePoint >= 0x0b80 && codePoint <= 0x0bff) {
    return '"Noto Sans Tamil", "Nirmala UI", Latha, sans-serif'
  }
  if ((codePoint >= 0x3400 && codePoint <= 0x9fff) || (codePoint >= 0x20000 && codePoint <= 0x2ffff)) {
    return '"Noto Sans SC", "Microsoft YaHei", SimHei, sans-serif'
  }
  return 'sans-serif'
}

// Keep this transform identical to backend _normalized_points(): one uniform scale,
// then center the shorter dimension. It is display-only; saved input coordinates stay unchanged.
function normalizeReferenceStrokes(strokes) {
  const validStrokes = (strokes || []).map((stroke) => (stroke || []).filter((point) =>
    Number.isFinite(Number(point?.x)) && Number.isFinite(Number(point?.y)),
  ))
  const points = validStrokes.flat()
  if (!points.length) return []

  const xs = points.map((point) => Number(point.x))
  const ys = points.map((point) => Number(point.y))
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const dx = maxX - minX
  const dy = maxY - minY
  const scale = Math.max(dx, dy, 1e-6)
  const offsetX = (1 - dx / scale) / 2
  const offsetY = (1 - dy / scale) / 2

  return validStrokes.map((stroke) => stroke.map((point) => ({
    ...point,
    x: (Number(point.x) - minX) / scale + offsetX,
    y: (Number(point.y) - minY) / scale + offsetY,
  })))
}

function ReferenceCanvasOverlay({ characterText, fontFamily, strokes, showGhost }) {
  const textRef = useRef(null)
  const [watermarkTransform, setWatermarkTransform] = useState('')
  const normalizedStrokes = normalizeReferenceStrokes(strokes)
  const offsetX = (DRAWING_CANVAS_WIDTH - REFERENCE_DRAW_AREA_SIZE) / 2
  const mappedPoints = normalizedStrokes.flat().map((point) => ({
    x: offsetX + point.x * REFERENCE_DRAW_AREA_SIZE,
    y: point.y * REFERENCE_DRAW_AREA_SIZE,
  }))
  const xs = mappedPoints.map((point) => point.x)
  const ys = mappedPoints.map((point) => point.y)
  const targetBounds = mappedPoints.length ? {
    x: Math.min(...xs),
    y: Math.min(...ys),
    width: Math.max(1, Math.max(...xs) - Math.min(...xs)),
    height: Math.max(1, Math.max(...ys) - Math.min(...ys)),
  } : {
    x: offsetX,
    y: 0,
    width: REFERENCE_DRAW_AREA_SIZE,
    height: REFERENCE_DRAW_AREA_SIZE,
  }

  useEffect(() => {
    let cancelled = false
    let frame = 0
    const measure = () => {
      if (cancelled) return
      frame = window.requestAnimationFrame(() => {
        const element = textRef.current
        if (!element || cancelled) return
        try {
          const glyphBounds = element.getBBox()
          if (!glyphBounds.width || !glyphBounds.height) return
          const scale = Math.min(
            (targetBounds.width * 0.92) / glyphBounds.width,
            (targetBounds.height * 0.92) / glyphBounds.height,
          )
          const centerX = targetBounds.x + targetBounds.width / 2
          const centerY = targetBounds.y + targetBounds.height / 2
          const glyphCenterX = glyphBounds.x + glyphBounds.width / 2
          const glyphCenterY = glyphBounds.y + glyphBounds.height / 2
          setWatermarkTransform(
            `translate(${centerX} ${centerY}) scale(${scale}) translate(${-glyphCenterX} ${-glyphCenterY})`,
          )
        } catch {
          // Keep the visible centered-glyph fallback if SVG measurement is unavailable.
        }
      })
    }
    if (document.fonts?.ready) document.fonts.ready.then(measure, measure)
    else measure()
    return () => {
      cancelled = true
      if (frame) window.cancelAnimationFrame(frame)
    }
  }, [characterText, fontFamily, targetBounds.x, targetBounds.y, targetBounds.width, targetBounds.height])

  return (
    <svg
      viewBox={`0 0 ${DRAWING_CANVAS_WIDTH} ${DRAWING_CANVAS_HEIGHT}`}
      preserveAspectRatio="xMidYMid meet"
      className="pointer-events-none absolute inset-0 z-10 h-full w-full ghost-guide"
      aria-hidden="true"
    >
      <text
        ref={textRef}
        x={DRAWING_CANVAS_WIDTH / 2}
        y={DRAWING_CANVAS_HEIGHT / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#f1f5f9"
        opacity="1"
        style={{ fontFamily, fontSize: `${REFERENCE_DRAW_AREA_SIZE * 0.72}px` }}
        transform={watermarkTransform || undefined}
      >{characterText}</text>
      {showGhost && normalizedStrokes.map((stroke, index) => (
        <polyline
          key={index}
          points={stroke.map((point) => `${offsetX + point.x * REFERENCE_DRAW_AREA_SIZE},${point.y * REFERENCE_DRAW_AREA_SIZE}`).join(' ')}
          fill="none"
          stroke="#5548e8"
          strokeWidth="8"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.3"
        />
      ))}
    </svg>
  )
}

function StrokeOrderGuide({ character, referenceData, animationKey, onReplay }) {
  const [speed, setSpeed] = useState(1)
  const [activeStroke, setActiveStroke] = useState(0)
  const [completedStrokeCount, setCompletedStrokeCount] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [pathLengths, setPathLengths] = useState([])
  const [watermarkTransform, setWatermarkTransform] = useState('')
  const pathElementsRef = useRef([])
  const watermarkRef = useRef(null)
  const metadata = referenceData?.reference_source
  const provenanceUnverified = metadata?.provenance_status === 'unverified'
  const instructionalReviewPending = metadata?.instructional_review_status === 'pending'
  const approvedReview = metadata?.instructional_review_status === 'approved' && metadata?.review_current && metadata?.latest_review
  const sourcePaths = metadata?.strokes || []
  const pointStrokes = referenceData?.stroke_data || []
  const strokeCount = sourcePaths.length || pointStrokes.length
  const viewBoxValue = metadata?.viewBox || '0 0 1 1'
  const viewBox = parseReferenceViewBox(viewBoxValue)
  const characterText = character?.character_text || ''
  const fontFamily = getCharacterFontFamily(characterText)
  const pathStrokeWidth = Math.min(viewBox.width, viewBox.height) * 0.045
  const watermarkFontSize = Math.min(viewBox.width, viewBox.height) * 0.72

  useEffect(() => {
    let cancelled = false
    const frame = window.requestAnimationFrame(() => {
      const nextLengths = Array.from({ length: strokeCount }, (_, index) => {
        const element = pathElementsRef.current[index]
        if (!element || typeof element.getTotalLength !== 'function') return 0
        try {
          const length = element.getTotalLength()
          return Number.isFinite(length) ? length : 0
        } catch {
          return 0
        }
      })
      if (cancelled) return
      const firstDrawableStroke = nextLengths.findIndex((length) => length > 0)
      setActiveStroke(firstDrawableStroke >= 0 ? firstDrawableStroke : Math.max(0, strokeCount - 1))
      setCompletedStrokeCount(firstDrawableStroke >= 0 ? firstDrawableStroke : strokeCount)
      setIsPlaying(firstDrawableStroke >= 0)
      setPathLengths(nextLengths)
    })
    return () => {
      cancelled = true
      window.cancelAnimationFrame(frame)
    }
  }, [
    animationKey,
    character?.id,
    characterText,
    referenceData?.character_id,
    metadata?.reference_path_sha256,
    viewBoxValue,
    strokeCount,
  ])

  useEffect(() => {
    let frame = 0
    let cancelled = false
    const measure = () => {
      if (cancelled) return
      frame = window.requestAnimationFrame(() => {
        const element = watermarkRef.current
        if (!element) return
        try {
          const bounds = element.getBBox()
          if (!bounds.width || !bounds.height) return
          let targetBounds = {
            x: viewBox.minX,
            y: viewBox.minY,
            width: viewBox.width,
            height: viewBox.height,
          }
          let targetFill = 0.76
          if (metadata?.watermark_align_to_reference !== false && sourcePaths.length > 0) {
            const pathBounds = pathElementsRef.current.slice(0, strokeCount)
              .filter(Boolean)
              .map((path) => {
                try { return path.getBBox() } catch { return null }
              })
              .filter((box) => box && (box.width > 0 || box.height > 0))
            if (pathBounds.length) {
              const left = Math.min(...pathBounds.map((box) => box.x))
              const top = Math.min(...pathBounds.map((box) => box.y))
              const right = Math.max(...pathBounds.map((box) => box.x + box.width))
              const bottom = Math.max(...pathBounds.map((box) => box.y + box.height))
              targetBounds = { x: left, y: top, width: right - left, height: bottom - top }
              targetFill = 0.92
            }
          }
          const scale = Math.min(
            (targetBounds.width * targetFill) / bounds.width,
            (targetBounds.height * targetFill) / bounds.height,
          )
          const centerX = targetBounds.x + targetBounds.width / 2
          const centerY = targetBounds.y + targetBounds.height / 2
          const glyphCenterX = bounds.x + bounds.width / 2
          const glyphCenterY = bounds.y + bounds.height / 2
          setWatermarkTransform(
            `translate(${centerX} ${centerY}) scale(${scale}) translate(${-glyphCenterX} ${-glyphCenterY})`,
          )
        } catch {
          // Keep the centered font fallback if the browser cannot measure this glyph.
        }
      })
    }
    if (document.fonts?.ready) document.fonts.ready.then(measure, measure)
    else measure()
    return () => {
      cancelled = true
      if (frame) window.cancelAnimationFrame(frame)
    }
  }, [characterText, fontFamily, metadata?.watermark_align_to_reference, strokeCount, referenceData?.character_id, metadata?.reference_path_sha256, viewBox.height, viewBox.minX, viewBox.minY, viewBox.width])

  if (!referenceData?.reference_available || !strokeCount) {
    return (
      <section className="lesson-card reference-card">
        <div className="card-heading"><div><span className="eyebrow">Stroke order</span><h2>Reference guide · {characterText || 'Character'}</h2></div></div>
        <div className="empty-reference"><span className="empty-glyph">{characterText || '字'}</span><p>Stroke animation not available yet</p><small>No saved reference guide is available for this character. When one exists, its source and instructor-review status are shown here.</small></div>
      </section>
    )
  }

  function finishStroke(index) {
    if (!isPlaying || index !== activeStroke) return
    let nextStroke = index + 1
    while (nextStroke < strokeCount && !(pathLengths[nextStroke] > 0)) nextStroke += 1
    setCompletedStrokeCount(nextStroke)
    if (nextStroke >= strokeCount) {
      setActiveStroke(Math.max(0, strokeCount - 1))
      setIsPlaying(false)
      return
    }
    setActiveStroke(nextStroke)
  }

  function replay() {
    setActiveStroke(0)
    setCompletedStrokeCount(0)
    setIsPlaying(true)
    onReplay?.()
  }

  return (
    <section className="lesson-card reference-card">
      <div className="card-heading">
        <div><span className="eyebrow">Step 1 · Watch</span><h2>Stroke order reference · {characterText}</h2></div>
        <div className="replay-controls"><button type="button" onClick={() => setSpeed(1)} aria-pressed={speed === 1}>1×</button><button type="button" onClick={() => setSpeed(0.75)} aria-pressed={speed === 0.75}>0.75×</button><button type="button" className="primary-button compact" onClick={replay}>↻ Replay</button></div>
      </div>
      <div className="reference-stage">
        <svg viewBox={viewBoxValue} preserveAspectRatio="xMidYMid meet" role="img" aria-label={`Animated stroke order for ${characterText}`}>
          <text
            ref={watermarkRef}
            x={viewBox.minX + viewBox.width / 2}
            y={viewBox.minY + viewBox.height / 2}
            textAnchor="middle"
            dominantBaseline="central"
            className="reference-watermark"
            transform={watermarkTransform || undefined}
            style={{ fontFamily, fontSize: `${watermarkFontSize}px` }}
          >{characterText}</text>
          {sourcePaths.length ? sourcePaths.map((path, index) => {
            const length = pathLengths[index] || 0
            const isComplete = index < completedStrokeCount
            const isActive = isPlaying && index === activeStroke && length > 0
            return (
              <path
                key={`${animationKey}-${path.path_id || index}`}
                ref={(element) => { pathElementsRef.current[index] = element }}
                d={path.d}
                className={`reference-path${isComplete ? ' is-complete' : ''}${isActive ? ' is-active is-animating' : ''}`}
                style={{
                  '--reference-path-length': length,
                  strokeDasharray: length || undefined,
                  strokeDashoffset: isComplete ? 0 : length || 0,
                  strokeWidth: pathStrokeWidth,
                  animationDuration: `${900 / speed}ms`,
                  opacity: isComplete || isActive ? 1 : 0,
                }}
                onAnimationEnd={(event) => {
                  if (event.target === event.currentTarget && event.animationName === 'draw-reference-path') finishStroke(index)
                }}
              />
            )
          }) : pointStrokes.map((stroke, index) => {
            const length = pathLengths[index] || 0
            const isComplete = index < completedStrokeCount
            const isActive = isPlaying && index === activeStroke && length > 0
            return (
              <polyline
                key={`${animationKey}-points-${index}`}
                ref={(element) => { pathElementsRef.current[index] = element }}
                points={stroke.map((point) => `${point.x},${point.y}`).join(' ')}
                className={`reference-path reference-polyline${isComplete ? ' is-complete' : ''}${isActive ? ' is-active is-animating' : ''}`}
                style={{
                  '--reference-path-length': length,
                  strokeDasharray: length || undefined,
                  strokeDashoffset: isComplete ? 0 : length || 0,
                  strokeWidth: pathStrokeWidth,
                  animationDuration: `${900 / speed}ms`,
                  opacity: isComplete || isActive ? 1 : 0,
                }}
                onAnimationEnd={(event) => {
                  if (event.target === event.currentTarget && event.animationName === 'draw-reference-path') finishStroke(index)
                }}
              />
            )
          })}
        </svg>
        <span className="stage-label">{metadata?.source || 'Saved lesson reference'}{metadata?.source_file ? ` · ${metadata.source_file}` : ''}</span>
      </div>
      {provenanceUnverified && <p className="reference-warning" role="note">Draft stroke guide · source attribution is still being verified. Use this animation for practice only; it is not yet an authoritative stroke-order reference.</p>}
      {!provenanceUnverified && instructionalReviewPending && <p className="reference-warning" role="note">Source-attributed stroke data · a qualified instructor has not yet reviewed this exact sequence. Treat it as a practice aid, not a certified teaching standard.</p>}
      {approvedReview && <p className="reference-approved" role="status">Reviewed by {approvedReview.reviewer_name} · {approvedReview.reviewer_qualification} · {approvedReview.writing_convention} · {approvedReview.reviewed_at_utc}</p>}
      <div className="stroke-steps" aria-label="Stroke sequence">
        {Array.from({ length: strokeCount }, (_, index) => {
          const isDone = index < completedStrokeCount
          const isCurrent = isPlaying && index === activeStroke
          return (
            <div className={`stroke-step${isCurrent ? ' active' : ''}`} key={index}>
              <span className="step-number">{index + 1}</span>
              <span><strong>Stroke {index + 1}</strong><small>{isDone ? 'Done' : isCurrent ? 'Playing now' : 'Next'}</small></span>
            </div>
          )
        })}
      </div>
      {metadata?.source_url && <p className="attribution">Source: <a href={metadata.source_url} target="_blank" rel="noreferrer">{metadata.source}</a> · {metadata.license || 'Reference attribution'}</p>}
    </section>
  )
}
function isPracticeAttemptComplete(attempt) {
  return [
    attempt.handwriting_score,
    attempt.stroke_order_score,
    attempt.pronunciation_score,
  ].every((score) => score !== null && score !== undefined)
}

function isPracticeAttemptProcessing(attempt, activeAttemptId) {
  const status = String(attempt.pronunciation_status || '').toLowerCase()
  return ['pending_assessment', 'processing'].includes(status)
    || String(activeAttemptId) === String(attempt.attempt_id)
}

function CharacterGroupPicker({ label, groups, activeGroupKey, onGroupChange, selectedCharacterId, onSelectCharacter }) {
  const activeGroup = groups.find((group) => group.key === activeGroupKey) || groups[0]

  return (
    <>
      <div className="character-group-picker" role="tablist" aria-label={label}>
        {groups.map((group) => (
          <button
            key={group.key}
            type="button"
            role="tab"
            aria-selected={activeGroup?.key === group.key}
            className={activeGroup?.key === group.key ? 'character-group-tab active' : 'character-group-tab'}
            onClick={() => {
              onGroupChange(group.key)
              if (!group.items.some((item) => String(item.id) === selectedCharacterId) && group.items[0]) {
                onSelectCharacter(String(group.items[0].id))
              }
            }}
          >
            <span>{group.title}</span>
            <small>{group.items.length} characters</small>
          </button>
        ))}
      </div>
      {activeGroup && (
        <section className="mt-4" role="tabpanel" aria-label={activeGroup.heading}>
          <h3 className="font-semibold text-indigo-800">{activeGroup.heading}</h3>
          <div className="mt-2 flex flex-wrap gap-3">
            {activeGroup.items.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={String(item.id) === selectedCharacterId}
                onClick={() => onSelectCharacter(String(item.id))}
                title={item.pronunciation_text || item.meaning}
                className={String(item.id) === selectedCharacterId
                  ? 'rounded-xl border-2 border-indigo-700 bg-indigo-50 px-5 py-3 text-3xl font-medium'
                  : 'rounded-xl border border-indigo-300 px-5 py-3 text-3xl hover:border-indigo-500'}
              >
                {item.character_text}
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  )
}

function StrokeSpeakWorkspace({ authUser, onLogout, onProfileUpdated }) {
  const [activePage, setActivePage] = useState('lessons')
  const [animationKey, setAnimationKey] = useState(0)
  const [showVideoDemo, setShowVideoDemo] = useState(false)
  const [selectedCourseLevel, setSelectedCourseLevel] = useState('foundation')
  const [selectedUnitNumber, setSelectedUnitNumber] = useState(null)
  const unitContentRef = useRef(null)
  const [languages, setLanguages] = useState([])
  const [lessonItems, setLessonItems] = useState([])
  const [lessonProgress, setLessonProgress] = useState([])
  const [sectionQuizzes, setSectionQuizzes] = useState([])
  const [sectionProgression, setSectionProgression] = useState({})
  const [progressMessage, setProgressMessage] = useState('')
  const [characters, setCharacters] = useState([])
  const [selectedLanguage, setSelectedLanguage] = useState('')
  const [selectedCharacterId, setSelectedCharacterId] = useState('')
  const selectedCharacterIdRef = useRef(selectedCharacterId)
  selectedCharacterIdRef.current = String(selectedCharacterId || '')
  const [selectedLessonId, setSelectedLessonId] = useState(null)
  const [characterGroupSelection, setCharacterGroupSelection] = useState('')
  const [message, setMessage] = useState('Connecting to StrokeSpeak...')
  const [error, setError] = useState('')
  const [strokeCount, setStrokeCount] = useState(0)
  const [isRecording, setIsRecording] = useState(false)
  const [audioUrl, setAudioUrl] = useState('')
  const [recordedAudio, setRecordedAudio] = useState(null)
  const [activeAttemptId, setActiveAttemptId] = useState(null)
  const [savingAudio, setSavingAudio] = useState(false)
  const [audioSaveMessage, setAudioSaveMessage] = useState('')
  const [audioUploaded, setAudioUploaded] = useState(false)
  const [transcribingAttemptId, setTranscribingAttemptId] = useState(null)
  const [pronunciationResult, setPronunciationResult] = useState(null)
  const [tutorialWatched, setTutorialWatched] = useState(false)
  const [savingProgressLessonId, setSavingProgressLessonId] = useState(null)
  const learnerId = String(authUser.id)
  const learnerDisplayName = authUser.name || 'Learner'
  const [profileEditing, setProfileEditing] = useState(false)
  const [profileName, setProfileName] = useState(learnerDisplayName)
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileMessage, setProfileMessage] = useState('')
  const [savingAttempt, setSavingAttempt] = useState(false)
  const [recognizingCnn, setRecognizingCnn] = useState(false)
  const [cnnResult, setCnnResult] = useState(null)
  const [latestAttemptResult, setLatestAttemptResult] = useState(null)
  const [attemptMessage, setAttemptMessage] = useState('')
  const [attempts, setAttempts] = useState([])
  const [referenceStrokes, setReferenceStrokes] = useState([])
  const [referenceStrokesCharacterId, setReferenceStrokesCharacterId] = useState('')
  const [referenceData, setReferenceData] = useState(null)
  const [referenceStatuses, setReferenceStatuses] = useState({})
  const [referenceMessage, setReferenceMessage] = useState('')
  const [savingReference, setSavingReference] = useState(false)
  const [referenceReviewDraft, setReferenceReviewDraft] = useState({
    reviewer_name: authUser.name || '',
    reviewer_qualification: '',
    reference_standard: '',
    writing_convention: '',
    decision: 'hold',
    notes: '',
    attests_exact_reference: false,
  })
  const [savingReferenceReview, setSavingReferenceReview] = useState(false)
  const [referenceReviewMessage, setReferenceReviewMessage] = useState('')
  const [showGhost, setShowGhost] = useState(true)

  const canvasRef = useRef(null)
  const drawingRef = useRef(false)
  const strokesRef = useRef([])
  const recorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const languageDisplayName = (language) => {
    if (!language) return ''
    if (language.script_code === 'sa-devanagari') return 'Sanskrit (Devanagari)'
    if (language.script_code === 'zh-hans') return 'Chinese'
    return language.name
  }

  const selectedCharacter = characters.find(
    (character) => String(character.id) === selectedCharacterId,
  )
  const referenceDataForSelectedCharacter = Number(referenceData?.character_id) === Number(selectedCharacterId)
    ? referenceData
    : null
  const referenceStrokesForSelectedCharacter = referenceStrokesCharacterId === String(selectedCharacterId)
    ? referenceStrokes
    : []
  const activeLesson = selectedLessonId
    ? lessonItems.find((item) => item.id === selectedLessonId)
    : lessonItems.find(
        (item) => item.category === 'character' && item.content_text === selectedCharacter?.character_text
      )
  const selectedCharacterLesson = activeLesson

  const orderedPracticeLessons = [...lessonItems]
    .filter((item) => item.category === 'character')
    .sort((a, b) => (a.unit_number - b.unit_number) || (a.lesson_order - b.lesson_order) || (a.id - b.id))
  const currentPracticeIndex = activeLesson
    ? orderedPracticeLessons.findIndex((item) => item.id === activeLesson.id)
    : -1
  const prevPracticeLesson = currentPracticeIndex > 0 ? orderedPracticeLessons[currentPracticeIndex - 1] : null
  const nextPracticeLesson = currentPracticeIndex >= 0 && currentPracticeIndex < orderedPracticeLessons.length - 1
    ? orderedPracticeLessons[currentPracticeIndex + 1]
    : null
  const activeUnitLessons = activeLesson
    ? orderedPracticeLessons.filter(
        (item) => String(item.level || '').toLowerCase() === String(activeLesson.level || '').toLowerCase()
          && Number(item.unit_number ?? 1) === Number(activeLesson.unit_number ?? 1)
      )
    : orderedPracticeLessons
  const unitTotalCount = activeUnitLessons.length
  const unitCompletedCount = activeUnitLessons.filter((item) =>
    lessonProgress.some((p) => String(p.lesson_id) === String(item.id) && p.status === 'completed')
  ).length
  const unitProgressPercent = unitTotalCount > 0 ? Math.round((unitCompletedCount / unitTotalCount) * 100) : 0
  const isActiveLessonCompleted = Boolean(
    activeLesson && lessonProgress.some((p) => String(p.lesson_id) === String(activeLesson.id) && p.status === 'completed')
  )
  const tutorialDone = tutorialWatched || !activeLesson?.tutorial_video_url
  const handwritingDone = strokeCount > 0 || Boolean(activeAttemptId) || Boolean(latestAttemptResult)
  const evaluationDone = Boolean(
    latestAttemptResult &&
      selectedCharacter &&
      Number(latestAttemptResult.character_id) === Number(selectedCharacter.id) &&
      Number(latestAttemptResult.user_id) === Number(authUser.id) &&
      latestAttemptResult.assessment?.passed === true
  )
  const pronunciationDone = Boolean(
    pronunciationResult && !pronunciationResult.isError && Number(pronunciationResult.score) >= 60
  )
  const canMarkCompleted = Boolean(activeLesson) && !isActiveLessonCompleted && handwritingDone && evaluationDone && pronunciationDone

  function resetPracticeInteractionState() {
    strokesRef.current = []
    setStrokeCount(0)
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    setCnnResult(null)
    setLatestAttemptResult(null)
    setAttemptMessage('')
    setActiveAttemptId(null)
    setRecordedAudio(null)
    setAudioUrl('')
    setAudioUploaded(false)
    setAudioSaveMessage('')
    setPronunciationResult(null)
    setTutorialWatched(false)
    setProgressMessage('')
  }

  function navigateToPracticeLesson(lessonItem) {
    if (!lessonItem) return
    resetPracticeInteractionState()
    setSelectedLessonId(lessonItem.id)
    const match = characters.find((c) => c.character_text === lessonItem.content_text)
    if (match) {
      setSelectedCharacterId(String(match.id))
    }
    setActivePage('practice')
  }

  function retryCurrentCharacter() {
    resetPracticeInteractionState()
    setAnimationKey((current) => current + 1)
  }

  function handleSelectCharacter(characterId) {
    const charIdStr = String(characterId)
    resetPracticeInteractionState()
    setSelectedCharacterId(charIdStr)
    const charObj = characters.find((c) => String(c.id) === charIdStr)
    if (charObj) {
      const matchingLesson = lessonItems.find(
        (item) => item.category === 'character' && item.content_text === charObj.character_text
      )
      if (matchingLesson) {
        setSelectedLessonId(matchingLesson.id)
      }
    }
    setActivePage('practice')
  }
  const selectedLanguageInfo = languages.find((item) => String(item.id) === selectedLanguage)
  const currentScriptCode = selectedLanguageInfo?.script_code || ''
  const isJapanese = currentScriptCode === 'ja-hiragana' || currentScriptCode === 'ja-katakana'
  const isSanskrit = currentScriptCode === 'sa-devanagari'
  const isTamil = currentScriptCode === 'ta'
  const isChinese = currentScriptCode === 'zh-hans'
  const isDevanagari = isSanskrit || currentScriptCode === 'Deva'
  const progressLessonEntries = lessonItems
    .map((item) => ({
      item,
      progress: lessonProgress.find((saved) => String(saved.lesson_id) === String(item.id)),
    }))
    .filter(({ progress }) => ['completed', 'in_progress', 'processing'].includes(progress?.status))
  const progressCompletedLessonCount = progressLessonEntries
    .filter(({ progress }) => progress.status === 'completed').length
  const progressInProgressLessonCount = progressLessonEntries.length - progressCompletedLessonCount
  const progressPracticeAttempts = attempts.filter((attempt) =>
    isPracticeAttemptComplete(attempt) || isPracticeAttemptProcessing(attempt, transcribingAttemptId),
  )

  useEffect(() => {
    if (!selectedCharacter) return
    const meaning = String(selectedCharacter.meaning || '').toLowerCase()

    if (isJapanese) {
      setCharacterGroupSelection(meaning.includes('katakana') ? 'katakana' : 'hiragana')
    } else if (isDevanagari || isTamil) {
      setCharacterGroupSelection(meaning.includes('consonant') ? 'consonants' : 'vowels')
    } else if (isChinese) {
      setCharacterGroupSelection(['one', 'two', 'three'].includes(meaning.trim()) ? 'numbers' : 'other')
    }
  }, [isJapanese, isDevanagari, isTamil, isChinese, selectedCharacter])
  const selectedLevelItems = lessonItems
    .filter((item) => item.level === selectedCourseLevel)
    .sort((a, b) => {
      const unitA = a.unit_number ?? 0
      const unitB = b.unit_number ?? 0
      if (unitA !== unitB) return unitA - unitB
      const orderA = a.lesson_order ?? a.id
      const orderB = b.lesson_order ?? b.id
      if (orderA !== orderB) return orderA - orderB
      return a.id - b.id
    })

  const japaneseUnitTitles = {
    foundation: [
      'Hiragana · vowels (あ, い, う, え, お)',
      'Hiragana · consonant rows (か through ん)',
      'Katakana · vowels (ア, イ, ウ, エ, オ)',
      'Katakana · consonant rows (カ through ン)',
      'Voiced sounds · sound contrast (が, ざ, だ, ば, ぱ)',
      'First words, useful phrases & summary',
    ],
    beginner: [
      'Essential beginner words',
      'Basic grammar and particles (は, が, を, に, で)',
      'First Japanese sentences',
    ],
    elementary: ['Polite verb tenses (ます, ました, ません)'],
    advanced: ['Dialogue and review'],
  }

  const sanskritUnitTitles = {
    foundation: {
      1: 'स्वर (Svara) · 14 Sanskrit Vowels (अ–औ)',
      2: 'व्यंजन (Vyanjana) · Velar Consonants (क-वर्ग)',
    },
    beginner: {
      1: 'मात्राएँ (Mātrās) · Vowel Signs',
      2: 'सरल शब्द (Sarala Śabdāḥ) · Simple Words',
      3: 'सरल वाक्य (Sarala Vākyāni) · Simple Sentences',
    },
  }

  const tamilUnitTitles = {
    foundation: {
      1: 'உயிரெழுத்து (Uyireḻuttu) · 12 Vowels & Aytham',
      2: 'மெய்யெழுத்து (Meyeḻuttu) · Hard Consonants (வல்லினம்)',
      3: 'உயிர்மெய்யெழுத்து (Uyirmeyeḻuttu) · Ka-Series Combinations',
      4: 'Phrase practice · Polite requests',
    },
    beginner: {
      1: 'சொற்கள் (Soṟkaḷ) · Essential Words',
      2: 'வாக்கியங்கள் (Vākkiyaṅkaḷ) · Everyday Phrases',
      5: 'Essential vocabulary & sentence practice',
    },
    elementary: {
      1: 'காலங்கள் (Kālaṅkaḷ) · Verb Tenses',
      6: 'Tense practice and verb forms',
    },
    advanced: {
      1: 'உரையாடல் (Uraiyādal) · Dialogue and Review',
      7: 'Conversational dialogue and review',
    },
  }

  const chineseUnitTitles = {
    foundation: {
      1: '基础汉字 (Jīchǔ Hànzì) · Foundational Characters (一, 二, 三, 人, 大)',
      2: '常用独体字与部首 · Radicals & Common Characters (口, 日, 月, 山)',
    },
    beginner: {
      1: '常用词汇 (Chángyòng Cíhuì) · Essential Vocabulary (你好, 谢谢, 朋友)',
      2: '基础句型 (Jīchǔ Jùxíng) · Basic Sentences (你好吗, 我是学生)',
    },
  }

  const unitDescriptions = {
    'ja-hiragana': {
      foundation: {
        1: 'Master the 5 core Japanese vowels (あ, い, う, え, お). Foundation of all Japanese phonetics and kana orthography.',
        2: 'Learn the primary consonant rows (k, s, t, n, h, m, y, r, w) and the singular nasal ん in canonical gojuon order.',
        3: 'Master the 5 Katakana vowel glyphs (ア, イ, ウ, エ, オ) used for loanwords, scientific names, and emphasis.',
        4: 'Learn the 41 Katakana consonant syllables in gojuon order with angular, precise stroke technique.',
        5: 'Explore dakuten (voicing dots) and handakuten (p-circle) sound transformations and phonetic contrast.',
        6: 'Essential kana vocabulary combinations, phrase patterns, and Katakana vowel overview summary (Lesson 315).',
      },
      beginner: {
        1: 'High-frequency everyday Japanese vocabulary for greetings, common objects, and expressions.',
        2: 'Grammar building blocks: topic marker は, subject marker が, object marker を, and directional particles.',
        3: 'Form basic declarative, negative, and question sentences in authentic Japanese word order.',
      },
      elementary: {
        1: 'Essential polite verb conjugations (ます present, ました past, ません negative).',
      },
      advanced: {
        1: 'Practical conversational dialogues and comprehensive grammar integration review.',
      },
    },
    'sa-devanagari': {
      foundation: {
        1: 'The complete classical 14-vowel inventory (अ through औ, including vocalic r/l) in canonical Paninian order.',
        2: 'Velar consonants (क-वर्ग: क, ख, ग, घ, ङ) articulated at the throat with authentic shirorekha head bars.',
      },
      beginner: {
        1: 'Diacritical vowel signs (मात्रा / Mātrās) modifying base consonants into syllabic forms.',
        2: 'High-frequency classical Sanskrit vocabulary, greetings, and root words (नमस्ते, जलम्, etc.).',
        3: 'Foundational Sanskrit sentences with subject-verb concord and copula constructions (अहं पठामि).',
      },
    },
    'ta': {
      foundation: {
        1: 'The 12 soul-letters (உயிரெழுத்து) from அ to ஔ and the unique Aytham (ஃ).',
        2: 'Hard body-consonants (வல்லினம்: க், ச், ட், த், ப்) written with canonical pulli dots.',
        3: 'Composite living letters (உயிர்மெய்) combining base consonant க் with vowel signs.',
        4: 'Polite conversational requests and essential cultural phrases.',
      },
      beginner: {
        1: 'Essential Tamil vocabulary for daily communication (வணக்கம், நன்றி, etc.).',
        2: 'Simple Tamil sentences and everyday spoken patterns (நான் தண்ணீர் குடிக்கிறேன்).',
      },
      elementary: {
        1: 'Temporal verb markers and tense conjugations in standard Tamil.',
      },
      advanced: {
        1: 'Conversational dialogue comprehension and literary structure review.',
      },
    },
    'zh-hans': {
      foundation: {
        1: 'Five fundamental single-morpheme Hanzi (一, 二, 三, 人, 大) introducing standard stroke conventions.',
        2: 'Essential pictographs and structural radicals (口, 日, 月, 山) forming the building blocks of hundreds of characters.',
      },
      beginner: {
        1: 'Everyday Chinese vocabulary and high-frequency communicative terms (你好, 谢谢, 朋友).',
        2: 'Basic Subject-Verb-Object sentence structures and question particles (你好吗？, 我是学生。).',
      },
    },
  }

  function getUnitTitle(scriptCode, level, unitNum) {
    if (scriptCode === 'ja-hiragana' || scriptCode === 'ja-katakana') {
      return japaneseUnitTitles[level]?.[unitNum - 1] || `Unit ${unitNum}`
    }
    if (scriptCode === 'sa-devanagari') {
      return sanskritUnitTitles[level]?.[unitNum] || sanskritUnitTitles[level]?.[unitNum - 1] || `Unit ${unitNum}`
    }
    if (scriptCode === 'ta') {
      return tamilUnitTitles[level]?.[unitNum] || (level === 'foundation' ? tamilUnitTitles.foundation?.[unitNum] : undefined) || `Unit ${unitNum}`
    }
    if (scriptCode === 'zh-hans') {
      return chineseUnitTitles[level]?.[unitNum] || chineseUnitTitles[level]?.[unitNum - 1] || `Unit ${unitNum}`
    }
    return `Unit ${unitNum}`
  }

  function getUnitNote(scriptCode, level, unitNum) {
    const key = (scriptCode === 'ja-katakana') ? 'ja-hiragana' : scriptCode
    const customNote = unitDescriptions[key]?.[level]?.[unitNum]
    if (customNote) return customNote
    const count = selectedLevelItems.filter((item) => Number(item.unit_number) === Number(unitNum)).length
    return `${count} lesson${count === 1 ? '' : 's'} in this unit.`
  }

  const courseSteps = [...new Set(
    selectedLevelItems
      .map((item) => item.unit_number)
      .filter((unit) => unit !== null && unit !== undefined && unit !== '')
      .map(Number)
      .filter(Number.isFinite)
  )]
    .sort((a, b) => a - b)
    .map((unit) => ({
      id: unit,
      title: getUnitTitle(currentScriptCode, selectedCourseLevel, unit),
      note: getUnitNote(currentScriptCode, selectedCourseLevel, unit),
    }))
  useEffect(() => {
    if (selectedUnitNumber === null) return
    const frame = window.requestAnimationFrame(() => {
      unitContentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [selectedUnitNumber])

  const foundationLevelQuiz = selectedCourseLevel === 'foundation'
    ? sectionQuizzes.find((quiz) => quiz.level === 'foundation')
    : null

  function isDraftLesson(item) {
    if (!item) return false
    // Sanskrit newly extended traditional vowels (ॠ, ऌ, ॡ: IDs 392, 393, 394)
    if (item.id >= 392 && item.id <= 394) return true
    return false
  }
  const devanagariVowelSequence = ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ']
  const sanskritVowelSequence = ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ॠ', 'ऌ', 'ॡ', 'ए', 'ऐ', 'ओ', 'औ']
  const devanagariConsonantSequence = ['क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ', 'ट', 'ठ', 'ड', 'ढ', 'ण', 'त', 'थ', 'द', 'ध', 'न', 'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व', 'श', 'ष', 'स', 'ह']
  const devanagariVowels = characters
    .filter((character) => {
      const meaning = String(character.meaning || '').toLowerCase()
      return meaning.includes('vowel') || meaning.includes('diphthong')
    })
    .sort((a, b) => {
      const seq = isSanskrit ? sanskritVowelSequence : devanagariVowelSequence
      const ia = seq.indexOf(a.character_text)
      const ib = seq.indexOf(b.character_text)
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
  const devanagariConsonants = characters
    .filter((character) => character.meaning?.toLowerCase().includes('consonant'))
    .sort((a, b) => devanagariConsonantSequence.indexOf(a.character_text) - devanagariConsonantSequence.indexOf(b.character_text))
  const tamilVowelSequence = ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ']
  const tamilVowels = characters
    .filter((character) => character.meaning?.toLowerCase().includes('vowel'))
    .sort((a, b) => {
      const ia = tamilVowelSequence.indexOf(a.character_text)
      const ib = tamilVowelSequence.indexOf(b.character_text)
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
  const tamilConsonants = characters
    .filter((character) => character.meaning?.toLowerCase().includes('consonant'))
  const hiraganaCharacters = characters.filter((character) => character.meaning?.includes('Hiragana'))
  const katakanaCharacters = characters.filter((character) => character.meaning?.includes('Katakana'))
  const chineseNumberCharacters = characters.filter((character) =>
    ['one', 'two', 'three'].includes(String(character.meaning || '').trim().toLowerCase()),
  )
  const chineseNumberIds = new Set(chineseNumberCharacters.map((character) => String(character.id)))
  const chineseOtherCharacters = characters.filter((character) => !chineseNumberIds.has(String(character.id)))

  useEffect(() => {
    apiFetch('/api/v1/languages')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => {
        const items = data.languages || []
        setLanguages(items)
        const preferred = items.find((item) => item.script_code === 'ja-hiragana') || items.find((item) => item.script_code === 'ta') || items[0]
        setSelectedLanguage(preferred?.id ? String(preferred.id) : '')
        setMessage(items.length ? 'Language list loaded from your database.' : 'No languages found yet.')
      })
      .catch(() => {
        setError('Could not connect to the backend. Check that the backend server is running.')
        setMessage('')
      })
  }, [])

  useEffect(() => {
    if (!selectedLanguage) {
      setLessonItems([])
      setSelectedUnitNumber(null)
      return
    }
    const selectedLanguageInfo = languages.find((item) => String(item.id) === selectedLanguage)
    const lessonLanguageIds = selectedLanguageInfo?.script_code === 'ja-hiragana'
      ? selectedLanguageInfo.character_language_ids || [selectedLanguage]
      : [selectedLanguage]
    const lessonRequests = lessonLanguageIds.map((languageId) =>
      apiFetch('/api/v1/lessons?language_id=' + languageId + '&user_id=' + learnerId)
    )
    Promise.all(lessonRequests)
      .then((responses) => {
        if (responses.some((response) => !response.ok)) throw new Error()
        return Promise.all(responses.map((response) => response.json()))
      })
      .then((results) => {
        const items = results.flatMap((data) => data.lessons || [])
        const unique = new Map()
        items.forEach((item) => unique.set(item.id, item))
        setLessonItems(Array.from(unique.values()))
      })
      .catch(() => setError('Could not load lessons for this language.'))
  }, [selectedLanguage, learnerId, languages])
  useEffect(() => {
    loadSectionQuizzes().catch(() => {
      setSectionQuizzes([])
      setSectionProgression({})
    })
  }, [selectedLanguage, learnerId])
  useEffect(() => {
    if (!selectedLanguage) {
      setCharacters([])
      setSelectedCharacterId('')
      setSelectedLessonId(null)
      return
    }

    const selectedLanguageInfo = languages.find((item) => String(item.id) === selectedLanguage)
    const characterLanguageIds = selectedLanguageInfo?.script_code === 'ja-hiragana'
      ? selectedLanguageInfo.character_language_ids || [selectedLanguage]
      : [selectedLanguage]
    const characterRequests = characterLanguageIds.map((languageId) =>
      apiFetch(`/api/v1/characters?language_id=${languageId}`),
    )

    Promise.all(characterRequests)
      .then((responses) => {
        if (responses.some((response) => !response.ok)) throw new Error()
        return Promise.all(responses.map((response) => response.json()))
      })
      .then((results) => {
        const items = results.flatMap((data) => data.characters || [])
        setCharacters(items)
        setReferenceStatuses(Object.fromEntries(items.map((item) => [String(item.id), Boolean(item.has_reference)])))
        setSelectedCharacterId(items[0]?.id ? String(items[0].id) : '')
        setSelectedLessonId(null)
        clearCanvas()
      })
      .catch(() => setError('Could not load characters for this language.'))
  }, [selectedLanguage, languages])

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  useEffect(() => {
    loadPracticeAttempts().catch(() => setAttempts([]))
    loadLessonProgress().catch(() => setLessonProgress([]))
  }, [learnerId])

  useEffect(() => {
    clearCanvas()
    setCnnResult(null)
    setLatestAttemptResult(null)
    setAttemptMessage('')
    setReferenceMessage('')
    setActiveAttemptId(null)
    setRecordedAudio(null)
    setAudioUploaded(false)
    setAudioSaveMessage('')
    setPronunciationResult(null)
  }, [selectedCharacterId])

  useEffect(() => {
    const requestedCharacterId = String(selectedCharacterId || '')
    if (!requestedCharacterId) {
      setReferenceStrokes([])
      setReferenceStrokesCharacterId('')
      setReferenceData(null)
      return undefined
    }

    const controller = new AbortController()
    let cancelled = false
    setReferenceStrokes([])
    setReferenceStrokesCharacterId('')
    setReferenceData(null)

    apiFetch('/api/v1/characters/' + requestedCharacterId + '/reference-strokes', {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error('Reference strokes are unavailable.')
        return response.json()
      })
      .then((data) => {
        const isCurrentRequest = !cancelled
          && !controller.signal.aborted
          && selectedCharacterIdRef.current === requestedCharacterId
          && Number(data.character_id) === Number(requestedCharacterId)
        if (!isCurrentRequest) return
        setReferenceData(data)
        setReferenceStrokes(data.stroke_data || [])
        setReferenceStrokesCharacterId(requestedCharacterId)
        setReferenceStatuses((current) => ({
          ...current,
          [requestedCharacterId]: Boolean(data.reference_available),
        }))
      })
      .catch((error) => {
        if (cancelled || controller.signal.aborted || error?.name === 'AbortError') return
        if (selectedCharacterIdRef.current !== requestedCharacterId) return
        setReferenceData(null)
        setReferenceStrokes([])
        setReferenceStrokesCharacterId('')
      })

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [selectedCharacterId])
  useEffect(() => {
    if (canvasRef.current) {
      const context = canvasRef.current.getContext('2d')
      if (context) {
        context.lineWidth = 10
        context.lineCap = 'round'
        context.lineJoin = 'round'
        context.strokeStyle = '#000000'
      }
    }
  }, [])

  function getCanvasPoint(event) {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()

    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height),
      time: Date.now(),
    }
  }

  function startDrawing(event) {
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    drawingRef.current = true
    canvas.setPointerCapture(event.pointerId)

    // Invalidate stale evaluation/CNN/attempt state as soon as the drawing changes
    if (latestAttemptResult || cnnResult || activeAttemptId) {
      setLatestAttemptResult(null)
      setCnnResult(null)
      setActiveAttemptId(null)
      setAttemptMessage('')
    }

    context.lineWidth = 10
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.strokeStyle = '#000000'

    const point = getCanvasPoint(event)
    strokesRef.current.push([point])
    setStrokeCount(strokesRef.current.length)

    context.beginPath()
    context.moveTo(point.x, point.y)
  }

  function draw(event) {
    if (!drawingRef.current) return

    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    context.lineWidth = 10
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.strokeStyle = '#000000'

    const point = getCanvasPoint(event)
    const currentStroke = strokesRef.current[strokesRef.current.length - 1]

    currentStroke.push(point)
    context.lineTo(point.x, point.y)
    context.stroke()
  }

  function stopDrawing() {
    drawingRef.current = false
  }

  function clearCanvas() {
    const canvas = canvasRef.current
    if (canvas) {
      const context = canvas.getContext('2d')
      if (context) {
        context.clearRect(0, 0, canvas.width, canvas.height)
        context.lineWidth = 10
        context.lineCap = 'round'
        context.lineJoin = 'round'
        context.strokeStyle = '#000000'
      }
    }

    strokesRef.current = []
    setStrokeCount(0)
    setCnnResult(null)
    setLatestAttemptResult(null)
  }

  async function savePracticeAttempt() {
    setError('')
    setAttemptMessage('')

    if (!selectedCharacter) {
      setAttemptMessage('Choose a character first.')
      return
    }
    if (strokesRef.current.length === 0) {
      setAttemptMessage('Draw the character before saving.')
      return
    }

    const cleanId = String(learnerId).trim()
    const numericUserId = Number(cleanId)
    if (!/^\d+$/.test(cleanId) || !Number.isInteger(numericUserId) || numericUserId < 1) {
      setAttemptMessage('Enter a valid learner ID (positive whole number).')
      return
    }

    setSavingAttempt(true)
    try {
      let canvasImageBase64 = null
      if (canvasRef.current) {
        try {
          const dataUrl = canvasRef.current.toDataURL('image/png')
          canvasImageBase64 = dataUrl.split(',')[1] || null
        } catch (canvasErr) {
          console.warn('Canvas export skipped:', canvasErr)
        }
      }

      const response = await apiFetch('/api/v1/practice-attempts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: numericUserId,
          character_id: selectedCharacter.id,
          stroke_data: strokesRef.current,
          canvas_image_base64: canvasImageBase64,
        }),
      })
      const data = await response.json()
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Learner ID ${numericUserId} is not registered in StrokeSpeak. Please select a valid learner.`)
        }
        throw new Error(data.detail || 'Could not save the drawing.')
      }
      await loadPracticeAttempts()
      setActiveAttemptId(data.attempt_id)
      setLatestAttemptResult(data)
      if (data.cnn_recognition) {
        setCnnResult(data.cnn_recognition)
      }
      setAttemptMessage(`Drawing attempt #${data.attempt_id} saved successfully.`)
    } catch (saveError) {
      setAttemptMessage(saveError.message || 'Could not save the drawing.')
    } finally {
      setSavingAttempt(false)
    }
  }

  async function recognizeWithCnn() {
    setCnnResult(null)
    setAttemptMessage('')
    if (!selectedCharacter) {
      setAttemptMessage('Choose a character first.')
      return
    }
    if (strokesRef.current.length === 0 || !canvasRef.current) {
      setAttemptMessage('Draw the character before running CNN recognition.')
      return
    }

    let canvasImageBase64 = null
    try {
      const dataUrl = canvasRef.current.toDataURL('image/png')
      canvasImageBase64 = dataUrl.split(',')[1] || null
    } catch (err) {
      setAttemptMessage('Could not capture drawing from canvas.')
      return
    }

    setRecognizingCnn(true)
    try {
      const response = await apiFetch(`/api/v1/characters/${selectedCharacter.id}/recognize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: canvasImageBase64 }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'CNN recognition request failed.')
      }
      setCnnResult(data)
      if (data.status === 'script_not_trained') {
        setAttemptMessage(`CNN info: ${data.detail}`)
      } else if (data.status === 'character_not_supported_by_cnn') {
        setAttemptMessage('CNN recognition is not available for this character yet.')
      } else if (data.status === 'empty_canvas') {
        setAttemptMessage('The canvas is blank. Please draw the character before recognition.')
      } else {
        setAttemptMessage(
          `CNN Recognition: "${data.predicted_character}" (Confidence: ${data.confidence}% · ${data.is_match ? 'Match ✓' : 'Mismatch ✗'} · ${data.inference_time_ms}ms CPU)`
        )
      }
    } catch (err) {
      setAttemptMessage(err.message || 'CNN recognition failed.')
    } finally {
      setRecognizingCnn(false)
    }
  }
  async function saveCharacterReference() {
    setReferenceMessage('')
    if (!selectedCharacter) {
      setReferenceMessage('Choose a character first.')
      return
    }
    if (strokesRef.current.length === 0) {
      setReferenceMessage('Draw the reference in the canvas before saving it.')
      return
    }

    setSavingReference(true)
    try {
      const response = await apiFetch(
        `/api/v1/characters/${selectedCharacter.id}/reference-strokes`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stroke_data: strokesRef.current }),
        },
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not save the reference.')
      setReferenceMessage(`Reference saved with ${data.stroke_count} stroke(s).`)
      if (selectedCharacterIdRef.current === String(selectedCharacter.id)) {
        setReferenceStrokes(strokesRef.current.map((stroke) => stroke.map((point) => ({ ...point }))))
        setReferenceStrokesCharacterId(String(selectedCharacter.id))
      }
      setReferenceStatuses((current) => ({ ...current, [String(selectedCharacter.id)]: true }))
    } catch (saveError) {
      setReferenceMessage(saveError.message || 'Could not save the reference.')
    } finally {
      setSavingReference(false)
    }
  }
  async function submitCharacterReferenceReview(event) {
    event.preventDefault()
    setReferenceReviewMessage('')
    if (!selectedCharacter) {
      setReferenceReviewMessage('Choose a character before recording a review.')
      return
    }
    if (referenceReviewDraft.decision === 'approve' && !referenceReviewDraft.attests_exact_reference) {
      setReferenceReviewMessage('Confirm that you checked the displayed path against the named standard before approving it.')
      return
    }

    setSavingReferenceReview(true)
    try {
      const response = await apiFetch(`/api/v1/characters/${selectedCharacter.id}/reference-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(referenceReviewDraft),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not record this reference review.')
      setReferenceReviewMessage(`Review recorded. Current status: ${data.instructional_review_status}.`)
      const refreshed = await apiFetch(`/api/v1/characters/${selectedCharacter.id}/reference-strokes`)
      if (refreshed.ok) {
        const reference = await refreshed.json()
        if (selectedCharacterIdRef.current === String(selectedCharacter.id)
          && Number(reference.character_id) === Number(selectedCharacter.id)) {
          setReferenceData(reference)
          setReferenceStrokes(reference.stroke_data || [])
          setReferenceStrokesCharacterId(String(selectedCharacter.id))
        }
      }
    } catch (reviewError) {
      setReferenceReviewMessage(reviewError.message || 'Could not record this reference review.')
    } finally {
      setSavingReferenceReview(false)
    }
  }

  async function loadSectionQuizzes() {
    const numericUserId = Number(learnerId)
    if (!selectedLanguage || !Number.isInteger(numericUserId) || numericUserId < 1) {
      setSectionQuizzes([])
      setSectionProgression({})
      return
    }
    const response = await apiFetch('/api/v1/section-quizzes?language_id=' + selectedLanguage + '&user_id=' + numericUserId)
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Could not load section quizzes.')
    setSectionQuizzes(data.quizzes || [])
    setSectionProgression(data.progression || {})
  }

  async function loadLessonProgress() {
    const cleanId = String(learnerId).trim()
    const numericUserId = Number(cleanId)
    if (!/^\d+$/.test(cleanId) || !Number.isInteger(numericUserId) || numericUserId < 1) {
      setLessonProgress([])
      return
    }
    try {
      const response = await apiFetch(`/api/v1/lesson-progress?user_id=${numericUserId}`)
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Learner ID ${numericUserId} not found or progress unavailable.`)
      }
      const data = await response.json()
      setLessonProgress(data.progress || [])
    } catch (err) {
      setLessonProgress([])
      setProgressMessage(err.message || 'Could not load lesson progress for this learner.')
    }
  }

  async function saveLessonProgress(lessonId, status) {
    if (savingProgressLessonId === lessonId) return
    setProgressMessage('')
    const cleanId = String(learnerId).trim()
    const numericUserId = Number(cleanId)
    if (!/^\d+$/.test(cleanId) || !Number.isInteger(numericUserId) || numericUserId < 1) {
      setProgressMessage('Enter a valid learner ID (positive whole number) first.')
      return
    }
    setSavingProgressLessonId(lessonId)
    try {
      const response = await apiFetch(`/api/v1/lessons/${lessonId}/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: numericUserId, status }),
      })
      const data = await response.json()
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Learner ID ${numericUserId} is not registered. Please choose a valid learner.`)
        }
        throw new Error(data.detail || 'Could not save lesson progress.')
      }
      await loadLessonProgress()
      await loadSectionQuizzes()
      setProgressMessage(status === 'completed' ? 'Character marked completed.' : 'Lesson started. Your progress is saved.')
    } catch (saveError) {
      setProgressMessage(saveError.message || 'Could not save lesson progress.')
    } finally {
      setSavingProgressLessonId(null)
    }
  }

  async function loadPracticeAttempts() {
    const cleanId = String(learnerId).trim()
    const numericUserId = Number(cleanId)
    if (!/^\d+$/.test(cleanId) || !Number.isInteger(numericUserId) || numericUserId < 1) {
      setAttempts([])
      return
    }
    try {
      const response = await apiFetch(`/api/v1/practice-attempts?user_id=${numericUserId}`)
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Learner ID ${numericUserId} not found or history unavailable.`)
      }
      const data = await response.json()
      setAttempts(data.attempts || [])
    } catch (err) {
      setAttempts([])
      setAttemptMessage(err.message || 'Could not load saved attempts for this learner.')
    }
  }
  async function savePronunciationAudio() {
    setAudioSaveMessage('')
    if (!activeAttemptId) {
      setAudioSaveMessage('Save a drawing attempt first so the recording has an attempt to belong to.')
      return
    }
    if (!recordedAudio) {
      setAudioSaveMessage('Record your pronunciation first.')
      return
    }
    setSavingAudio(true)
    try {
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = () => reject(new Error('Could not read the audio recording.'))
        reader.readAsDataURL(recordedAudio)
      })
      const audioBase64 = String(dataUrl).split(',')[1]
      const response = await apiFetch(`/api/v1/practice-attempts/${activeAttemptId}/pronunciation-audio`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_base64: audioBase64, mime_type: recordedAudio.type || 'audio/webm' }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not save the recording.')
      await loadPracticeAttempts()
      setAudioUploaded(true)
      setAudioSaveMessage(data.message + ' Recording saved. Use Assess with Whisper below.')
    } catch (saveError) {
      setAudioSaveMessage(saveError.message || 'Could not save the recording.')
    } finally {
      setSavingAudio(false)
    }
  }

  async function transcribePronunciation(attemptId) {
    const targetAttemptId = attemptId || activeAttemptId
    if (!targetAttemptId) {
      setAudioSaveMessage('Save your drawing and pronunciation first.')
      return
    }
    setTranscribingAttemptId(targetAttemptId)
    setPronunciationResult(null)
    setAudioSaveMessage('The speech service is transcribing your recording. This may take a little while.')
    try {
      const response = await apiFetch(`/api/v1/practice-attempts/${targetAttemptId}/transcribe`, { method: 'POST' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not transcribe the recording.')
      await loadPracticeAttempts()
      const targetText = data.expected_text || selectedCharacter.pronunciation_text || selectedCharacter.character_text
      const transcriptScore = Math.round(Number(data.pronunciation_score ?? 0))
      const scoreNote = transcriptScore < 70
        ? 'Whisper can mishear short isolated sounds; this transcript score does not prove your articulation was wrong.'
        : 'This is a normalized transcript text similarity score, not a direct acoustic phoneme grade.'
      setPronunciationResult({
        attemptId: targetAttemptId,
        targetText,
        characterText: data.character_text || selectedCharacter.character_text,
        transcribedText: data.transcribed_text,
        score: transcriptScore,
        feedback: data.feedback,
        scoreNote,
        provider: data.transcription_provider || 'local faster-whisper',
        detectedLanguage: data.detected_language || '',
        isError: false,
      })
      setAudioSaveMessage('')
    } catch (transcriptionError) {
      setPronunciationResult({
        attemptId: targetAttemptId,
        isError: true,
        feedback: transcriptionError.message || 'Could not transcribe the recording.',
      })
      setAudioSaveMessage('')
    } finally {
      setTranscribingAttemptId(null)
    }
  }
  async function startRecording() {
    setError('')
    setAudioSaveMessage('')
    setPronunciationResult(null)
    setAudioUploaded(false)
    setRecordedAudio(null)

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError('Audio recording is not supported by this browser. Try a recent version of Chrome or Edge.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunksRef.current = []

      const recorder = new MediaRecorder(stream)
      recorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        })

        if (audioUrl) URL.revokeObjectURL(audioUrl)
        setRecordedAudio(audioBlob)
        setAudioUrl(URL.createObjectURL(audioBlob))
        stream.getTracks().forEach((track) => track.stop())
      }

      recorder.start()
      setIsRecording(true)
    } catch {
      setError('Microphone access failed. Allow microphone access in your browser, then try again.')
    }
  }

  async function saveProfileName(event) {
    event.preventDefault()
    const cleanName = profileName.trim()
    if (cleanName.length < 2) {
      setProfileMessage('Name must contain at least 2 characters.')
      return
    }

    setSavingProfile(true)
    setProfileMessage('')
    try {
      const response = await apiFetch('/api/v1/auth/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: cleanName }),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(' ')
          : data.detail
        throw new Error(detail || 'Could not update your profile.')
      }
      onProfileUpdated(data.user)
      setProfileName(data.user.name)
      setProfileEditing(false)
      setProfileMessage('Profile updated.')
    } catch (profileError) {
      setProfileMessage(profileError.message || 'Could not update your profile.')
    } finally {
      setSavingProfile(false)
    }
  }

  function stopRecording() {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
      setIsRecording(false)
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><BrandLogo size="sidebar" /></div>
        <div className="side-label">CURRICULUM</div>
        <button className={`side-link ${activePage === 'lessons' ? 'selected' : ''}`} onClick={() => setActivePage('lessons')}>▦ <span>Dashboard</span></button>
        <button className={`side-link ${activePage === 'practice' ? 'selected' : ''}`} onClick={() => setActivePage('practice')}>✎ <span>Practice Studio</span></button>
        <button className={`side-link ${activePage === 'progress' ? 'selected' : ''}`} onClick={() => setActivePage('progress')}>▤ <span>Progress</span></button>
        <div className="sidebar-note">
          <strong>Learning progress</strong>
          <span>{lessonProgress.filter((item) => item.status === 'completed').length} lessons completed</span>
          {activePage === 'practice' && activeUnitLessons.length > 0 && (
            <div className="mt-3 border-t border-slate-200 pt-2.5">
              <div className="mb-1.5 flex items-center justify-between text-[11px] font-semibold text-slate-600">
                <span>Unit {activeLesson?.unit_number ?? 1}</span>
                <span>{unitCompletedCount}/{unitTotalCount}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {activeUnitLessons.map((item) => {
                  const done = lessonProgress.some((p) => String(p.lesson_id) === String(item.id) && p.status === 'completed')
                  const isCurrent = activeLesson?.id === item.id
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => navigateToPracticeLesson(item)}
                      title={item.title}
                      className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-semibold transition ${
                        isCurrent
                          ? 'bg-indigo-700 text-white shadow-sm'
                          : done
                          ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      <span>{item.content_text || item.lesson_order}</span>
                      {done && <span aria-label="Completed">✓</span>}
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <BrandLogo size="compact" showName={false} className="topbar-logo" />
          <div className="course-chip" aria-live="polite">
            <span className={selectedLanguage ? 'language-status-dot is-active' : 'language-status-dot'} aria-hidden="true" />
            <span className="course-label">{languageDisplayName(languages.find((item) => String(item.id) === selectedLanguage)) || 'Choose a language'}</span>
          </div>
          {authUser.developer_mode && <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold text-indigo-800">Developer Mode</span>}
          {authUser.demo_quiz_access && <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-bold text-violet-800">Demo Quiz Access</span>}
          <nav className="top-tabs" aria-label="Main navigation">
            {[
              { id: 'lessons', label: 'Dashboard' },
              { id: 'practice', label: 'Practice Studio' },
              { id: 'progress', label: 'Progress' },
              ...(authUser.developer_mode ? [{ id: 'developer-quizzes', label: 'Quiz Preview' }] : []),
              ...(authUser.demo_quiz_access ? [{ id: 'demo-quizzes', label: 'Quiz Practice' }] : []),
            ].map((page) => (
              <button key={page.id} type="button" onClick={() => setActivePage(page.id)} aria-current={activePage === page.id ? 'page' : undefined}>{page.label}</button>
            ))}
          </nav>
          <details className="profile-menu">
            <summary className="profile-trigger" aria-label={"Profile menu for " + learnerDisplayName} title="Profile">
              <span className="profile-avatar" aria-hidden="true">{learnerDisplayName.trim().charAt(0).toUpperCase()}</span>
              <span className="profile-trigger-name">{learnerDisplayName}</span>
              <span className="profile-chevron" aria-hidden="true">⌄</span>
            </summary>
            <div className="profile-menu-panel">
              <div className="profile-menu-identity">
                <strong>{learnerDisplayName}</strong>
                <span>{authUser.email}</span>
              </div>
              {profileEditing ? (
                <form className="profile-edit-form" onSubmit={saveProfileName}>
                  <label htmlFor="profile-display-name">Display name</label>
                  <input
                    id="profile-display-name"
                    value={profileName}
                    onChange={(event) => setProfileName(event.target.value)}
                    minLength={2}
                    maxLength={100}
                    required
                  />
                  <div className="profile-edit-actions">
                    <button type="button" className="profile-cancel-button" onClick={() => { setProfileEditing(false); setProfileName(learnerDisplayName); setProfileMessage('') }}>Cancel</button>
                    <button type="submit" className="profile-save-button" disabled={savingProfile}>{savingProfile ? 'Saving…' : 'Save changes'}</button>
                  </div>
                </form>
              ) : (
                <button
                  type="button"
                  className="profile-edit-button"
                  onClick={() => { setProfileName(learnerDisplayName); setProfileMessage(''); setProfileEditing(true) }}
                >
                  Edit profile
                </button>
              )}
              {profileMessage && <p className={'profile-message' + (profileMessage === 'Profile updated.' ? ' success' : '')} role="status">{profileMessage}</p>}
              <button type="button" className="profile-logout-button" onClick={onLogout}>Log out</button>
            </div>
          </details>
        </header>
        <section className="workspace">
          <div className="page-intro"><div><span className="eyebrow">LINGUISTIC PRACTICE · ACTIVE LEARNING</span><h1>{activePage === 'lessons' ? 'Welcome to your learning dashboard' : activePage === 'practice' ? 'Practice Studio' : activePage === 'developer-quizzes' ? 'Developer quiz preview' : activePage === 'demo-quizzes' ? 'Quiz practice' : 'Your progress'}</h1><p>{activePage === 'lessons' ? 'Choose a script and continue through the available lessons in order.' : activePage === 'practice' ? 'Watch, trace, and listen to practise your selected character.' : activePage === 'developer-quizzes' ? 'Read-only answer keys and explanations for available quizzes.' : activePage === 'demo-quizzes' ? 'Take available quizzes across the supported languages while keeping lesson progression normal.' : 'View lessons and assessments that are complete or in progress.'}</p></div><div className="avatar-chip">{languageDisplayName(languages.find((item) => String(item.id) === selectedLanguage))?.slice(0, 2) || 'SS'}</div></div>
          {activePage === 'developer-quizzes' && authUser.developer_mode && <DeveloperQuizPreviewPanel />}
          {activePage === 'demo-quizzes' && authUser.demo_quiz_access && <DemoQuizAccessPanel languages={languages} learnerId={learnerId} />}
          {activePage === 'lessons' && <div className="metric-grid"><article className="metric-card"><span>LESSONS COMPLETED</span><strong>{lessonProgress.filter((item) => item.status === 'completed').length}<small> / {lessonItems.length || '—'}</small></strong><div className="metric-note">Saved progress for learner {learnerId}</div></article><article className="metric-card"><span>PRACTICE ATTEMPTS</span><strong>{attempts.length}</strong><div className="metric-note">Loaded from your account</div></article><article className="metric-card"><span>GEOMETRIC PRACTICE SCORE</span><strong>{attempts.filter((item) => item.handwriting_score != null).length ? `${Math.round(attempts.filter((item) => item.handwriting_score != null).reduce((sum, item) => sum + Number(item.handwriting_score), 0) / attempts.filter((item) => item.handwriting_score != null).length)}%` : '—'}</strong><div className="metric-note">{attempts.some((item) => item.handwriting_score != null) ? 'Geometric prototype · not a trained AI model' : 'Not available yet'}</div></article></div>}
          {activePage === 'lessons' && attempts.length > 0 && (
            <section className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">Recent Learning Activity</h3>
                  <p className="text-xs text-slate-500">Your latest practice attempts and speech evaluations</p>
                </div>
                <button
                  type="button"
                  onClick={() => setActivePage('progress')}
                  className="text-xs font-semibold text-indigo-700 hover:text-indigo-900"
                >
                  View full history →
                </button>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {attempts.slice(0, 3).map((attempt) => {
                  const scores = [
                    attempt.handwriting_score != null ? `Draw: ${Math.round(Number(attempt.handwriting_score))}%` : null,
                    attempt.pronunciation_score != null ? `Transcript match: ${Math.round(Number(attempt.pronunciation_score))}%` : null,
                  ].filter(Boolean).join(' · ')
                  return (
                    <div key={attempt.attempt_id} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 p-2.5 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-indigo-900" dir="auto">{attempt.character_text}</span>
                        <div>
                          <p className="font-semibold text-slate-800">Attempt #{attempt.attempt_id}</p>
                          <p className="text-slate-500">{scores || `${attempt.stroke_count ?? 0} strokes`}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const char = characters.find((c) => c.character_text === attempt.character_text)
                          if (char) {
                            handleSelectCharacter(char.id)
                          } else {
                            setActivePage('practice')
                          }
                        }}
                        className="rounded bg-indigo-50 px-2 py-1 font-semibold text-indigo-700 hover:bg-indigo-100"
                      >
                        Practise →
                      </button>
                    </div>
                  )
                })}
              </div>
            </section>
          )}
          <p className="text-slate-600">{message}</p>

          {error && (
            <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-700">{error}</p>
          )}

          {activePage === 'lessons' ? (
            <>
              <h2 className="mt-5 text-xl font-bold">Choose a language</h2>
              <label className="mt-3 block font-medium" htmlFor="language">Language</label>
              <select
                id="language"
                className="mt-2 w-full max-w-md rounded-lg border border-slate-300 bg-white p-3"
                value={selectedLanguage}
                onChange={(event) => {
                  setSelectedLanguage(event.target.value)
                  setSelectedCourseLevel('foundation')
                  setSelectedUnitNumber(null)
                }}
              >
                <option value="">Select a language</option>
                {languages.filter((language) => language.script_code !== 'ja-katakana').map((language) => (
                  <option key={language.id} value={language.id}>{languageDisplayName(language)}</option>
                ))}
              </select>

              <h2 className="mt-8 text-xl font-bold">Choose a character</h2>
              {isJapanese ? (
                <CharacterGroupPicker
                  label="Choose Japanese script"
                  groups={[
                    { key: 'hiragana', title: 'Hiragana', heading: 'Hiragana characters', items: hiraganaCharacters },
                    { key: 'katakana', title: 'Katakana', heading: 'Katakana characters', items: katakanaCharacters },
                  ]}
                  activeGroupKey={characterGroupSelection}
                  onGroupChange={setCharacterGroupSelection}
                  selectedCharacterId={selectedCharacterId}
                  onSelectCharacter={handleSelectCharacter}
                />
              ) : isDevanagari ? (
                <CharacterGroupPicker
                  label="Choose Sanskrit character group"
                  groups={[
                    { key: 'vowels', title: 'Vowels', heading: 'Sanskrit vowels (Svara) · स्वर', items: devanagariVowels },
                    { key: 'consonants', title: 'Consonants', heading: 'Sanskrit consonants (Vyanjana) · व्यंजन', items: devanagariConsonants },
                  ]}
                  activeGroupKey={characterGroupSelection}
                  onGroupChange={setCharacterGroupSelection}
                  selectedCharacterId={selectedCharacterId}
                  onSelectCharacter={handleSelectCharacter}
                />
              ) : isTamil ? (
                <CharacterGroupPicker
                  label="Choose Tamil character group"
                  groups={[
                    { key: 'vowels', title: 'Vowels', heading: 'Tamil vowels (Uyireḻuttu) · உயிரெழுத்து', items: tamilVowels },
                    { key: 'consonants', title: 'Consonants', heading: 'Tamil consonants (Meyeḻuttu) · மெய்யெழுத்து', items: tamilConsonants },
                  ]}
                  activeGroupKey={characterGroupSelection}
                  onGroupChange={setCharacterGroupSelection}
                  selectedCharacterId={selectedCharacterId}
                  onSelectCharacter={handleSelectCharacter}
                />
              ) : isChinese ? (
                <CharacterGroupPicker
                  label="Choose Chinese character group"
                  groups={[
                    { key: 'numbers', title: 'Numbers', heading: 'Chinese number characters · 数字', items: chineseNumberCharacters },
                    { key: 'other', title: 'Other Hanzi', heading: 'Other starter characters · 汉字', items: chineseOtherCharacters },
                  ]}
                  activeGroupKey={characterGroupSelection}
                  onGroupChange={setCharacterGroupSelection}
                  selectedCharacterId={selectedCharacterId}
                  onSelectCharacter={handleSelectCharacter}
                />
              ) : (
                <div className="mt-4 flex flex-wrap gap-3">
                  {characters.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      aria-pressed={String(item.id) === selectedCharacterId}
                      onClick={() => handleSelectCharacter(item.id)}
                      title={item.pronunciation_text || item.meaning}
                      className={String(item.id) === selectedCharacterId
                        ? 'rounded-xl border-2 border-indigo-700 bg-indigo-50 px-5 py-3 text-3xl font-medium'
                        : 'rounded-xl border border-indigo-300 px-5 py-3 text-3xl hover:border-indigo-500'}
                    >
                      {item.character_text}
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : null}
          {activePage === 'lessons' && (
            <section className="mt-8 rounded-xl border border-slate-200 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold">Course path: foundations to advanced</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Follow the curriculum step by step. Choose a level, then select any module to open its ordered lessons from foundations upward.
                  </p>
                </div>
                {selectedCharacter && (
                  <button type="button" onClick={() => setShowVideoDemo(true)} className="rounded-lg bg-indigo-700 px-4 py-2 font-semibold text-white hover:bg-indigo-800">
                    Preview guided lesson
                  </button>
                )}
              </div>

              {/* Level Selector: 1. Foundations -> 2. Beginner -> 3. Elementary -> 4. Intermediate -> 5. Advanced */}
              <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                {[
                  { id: 'foundation', label: '1. Foundations', summary: 'Core script, vowels, and basic characters' },
                  { id: 'beginner', label: '2. Beginner', summary: 'Vocabulary, word formation, and basic grammar' },
                  { id: 'elementary', label: '3. Elementary', summary: 'Verb tenses, noun declensions, and sentence structures' },
                  { id: 'intermediate', label: '4. Intermediate', summary: 'Complex grammar and contextual usage' },
                  { id: 'advanced', label: '5. Advanced', summary: 'Fluent reading, dialogue, and classical literature' },
                ].map((level) => {
                  const levelLessons = lessonItems.filter((item) => item.level === level.id)
                  const count = levelLessons.length
                  const completedCount = levelLessons.filter((item) =>
                    lessonProgress.some((p) => String(p.lesson_id) === String(item.id) && p.status === 'completed')
                  ).length
                  const selected = selectedCourseLevel === level.id
                  const isLocked =
                    (level.id === 'beginner' && sectionProgression.beginner_unlocked === false) ||
                    (level.id === 'elementary' && sectionProgression.elementary_unlocked === false)
                  return (
                    <button
                      key={level.id}
                      type="button"
                      aria-pressed={selected}
                      disabled={isLocked}
                      onClick={() => {
                        if (!isLocked) {
                          setSelectedCourseLevel(level.id)
                          setSelectedUnitNumber(null)
                        }
                      }}
                      className={selected
                        ? 'rounded-lg border-2 border-indigo-700 bg-indigo-50 p-3 text-left ring-2 ring-indigo-100'
                        : 'rounded-lg border border-slate-200 bg-white p-3 text-left hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-60 disabled:cursor-not-allowed'}
                    >
                      <div className="flex items-center justify-between">
                        <span className="block text-sm font-semibold">{level.label}</span>
                        {completedCount > 0 && completedCount === count && (
                          <span className="text-xs font-bold text-emerald-700">✓</span>
                        )}
                      </div>
                      <span className="mt-1 block text-xs text-slate-600">
                        {isLocked
                          ? 'Locked · complete previous stage and pass its quiz'
                          : count > 0
                            ? `${count} lessons · ${completedCount} completed`
                            : 'Coming later'}
                      </span>
                    </button>
                  )
                })}
              </div>

              {/* Active Level Header & Linguistic Context */}
              <div className="mt-6 flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <h3 className="text-lg font-bold text-slate-900">
                  {isSanskrit ? 'Sanskrit Learning Path (Devanagari)' : isTamil ? 'Tamil Learning Path' : isChinese ? 'Chinese Learning Path' : isJapanese ? 'Japanese Tutor (Hiragana & Katakana)' : isDevanagari ? 'Sanskrit Learning Path (Devanagari)' : 'Course Path'} · {selectedCourseLevel[0].toUpperCase() + selectedCourseLevel.slice(1)}
                </h3>
                <span className="text-xs font-medium text-slate-500">
                  {selectedLevelItems.length} total lessons in this level
                </span>
              </div>

              {isChinese && (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                  <strong>Logographic Curriculum:</strong> Chinese is organized progressively: foundational characters (一, 二, 三, 人, 大), radicals & common characters (口, 日, 月, 山), beginner vocabulary (你好, 谢谢, 朋友), and simple sentences (你好吗, 我是学生).
                </div>
              )}
              {isSanskrit && selectedCourseLevel === 'foundation' && (
                <div className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-900">
                  <strong>Traditional Sanskrit Orthography:</strong> Unit 1 covers the complete 14-vowel inventory in canonical Paninian order (अ–औ). Vowels ॠ, ऌ, ॡ are classical rare forms; reference audio is a synthetic Indic approximation pending expert review.
                </div>
              )}

              {selectedLevelItems.length === 0 ? (
                <p className="mt-5 rounded-lg bg-slate-50 p-4 text-slate-600">
                  No lessons are available in this level yet. Choose another level above.
                </p>
              ) : (
                <>
                  {/* Module / Unit Selector Bar: Selecting a module opens its correctly ordered lessons */}
                  {courseSteps.length > 0 && (
                    <div className="mt-5 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-indigo-900">
                          Course Modules ({courseSteps.length} in this level)
                        </span>
                        <span className="text-xs text-slate-500">
                          Click a module to open its lessons in sequence from foundations upward
                        </span>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedUnitNumber(null)}
                          className={`rounded-lg px-3 py-2 text-xs font-semibold transition-all ${
                            selectedUnitNumber === null
                              ? 'bg-indigo-700 text-white shadow-sm ring-2 ring-indigo-200'
                              : 'border border-slate-300 bg-white text-slate-700 hover:border-indigo-400 hover:bg-white'
                          }`}
                        >
                          All Modules ({selectedLevelItems.length} lessons)
                        </button>
                        {courseSteps.map((step) => {
                          const stepLessons = selectedLevelItems.filter((item) => Number(item.unit_number) === step.id)
                          const completedInStep = stepLessons.filter((item) =>
                            lessonProgress.some((p) => String(p.lesson_id) === String(item.id) && p.status === 'completed')
                          ).length
                          const isComplete = stepLessons.length > 0 && completedInStep === stepLessons.length
                          const isSelected = Number(selectedUnitNumber) === step.id
                          const isFinalCourseUnit = step.id === courseSteps[courseSteps.length - 1]?.id
                          const hasQuiz = selectedCourseLevel === 'beginner'
                            ? sectionQuizzes.some((q) => q.level === 'beginner' && Number(q.unit_number) === Number(step.id))
                            : selectedCourseLevel === 'foundation' && isFinalCourseUnit && sectionQuizzes.some((q) => q.level === 'foundation')

                          return (
                            <button
                              key={step.id}
                              type="button"
                              onClick={() => setSelectedUnitNumber(step.id)}
                              className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all ${
                                isSelected
                                  ? 'bg-indigo-700 text-white shadow-sm ring-2 ring-indigo-200'
                                  : 'border border-slate-300 bg-white text-slate-700 hover:border-indigo-400 hover:bg-white'
                              }`}
                            >
                              <span>Unit {step.id}: {step.title.split('·')[0].trim()}</span>
                              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                isSelected
                                  ? 'bg-indigo-800 text-indigo-100'
                                  : isComplete
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-slate-100 text-slate-600'
                              }`}>
                                {isComplete ? '✓ Done' : `${completedInStep}/${stepLessons.length}`}
                              </span>
                              {hasQuiz && (
                                <span className={`text-[10px] ${isSelected ? 'text-indigo-200' : 'text-indigo-600'}`}>
                                  [Quiz]
                                </span>
                              )}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Render Lessons: Single Selected Module or All Modules */}
                  <div ref={unitContentRef} className="mt-6 scroll-mt-24 space-y-6">
                    {selectedUnitNumber !== null && (
                      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900" role="status">
                        <span className="font-semibold">Showing Unit {selectedUnitNumber} · {selectedLevelItems.filter((item) => Number(item.unit_number) === Number(selectedUnitNumber)).length} lessons</span>
                        <button type="button" onClick={() => setSelectedUnitNumber(null)} className="font-semibold text-indigo-700 underline underline-offset-2">Show all units</button>
                      </div>
                    )}
                    {courseSteps
                      .filter((step) => selectedUnitNumber === null || Number(selectedUnitNumber) === step.id)
                      .map((step) => {
                        const items = selectedLevelItems.filter((item) => Number(item.unit_number) === step.id)
                        const sectionQuiz = selectedCourseLevel === 'beginner'
                          ? sectionQuizzes.find((quiz) => quiz.level === 'beginner' && Number(quiz.unit_number) === Number(step.id))
                          : null
                        const completedCount = items.filter((item) =>
                          lessonProgress.some((p) => String(p.lesson_id) === String(item.id) && p.status === 'completed')
                        ).length
                        const pct = items.length > 0 ? Math.round((completedCount / items.length) * 100) : 0
                        const stepIndex = courseSteps.findIndex((s) => s.id === step.id)
                        const prevStep = stepIndex > 0 ? courseSteps[stepIndex - 1] : null
                        const nextStep = stepIndex < courseSteps.length - 1 ? courseSteps[stepIndex + 1] : null

                        const COURSE_LEVEL_ORDER = ['foundation', 'beginner', 'elementary', 'intermediate', 'advanced']
                        const currentLevelIndex = COURSE_LEVEL_ORDER.indexOf(selectedCourseLevel)
                        const nextLevelId = currentLevelIndex >= 0 && currentLevelIndex < COURSE_LEVEL_ORDER.length - 1 ? COURSE_LEVEL_ORDER[currentLevelIndex + 1] : null
                        const nextLevelUnlocked = nextLevelId === 'beginner' ? sectionProgression.beginner_unlocked !== false : nextLevelId === 'elementary' ? sectionProgression.elementary_unlocked !== false : true
                        const hasLessonsInNextLevel = nextLevelId ? lessonItems.some((item) => item.level === nextLevelId) : false

                        if (items.length === 0) return null

                        return (
                          <section key={step.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                            {/* Module Header with Progress */}
                            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
                              <div className="max-w-2xl">
                                <div className="flex items-center gap-2">
                                  <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-800">
                                    Unit {step.id}
                                  </span>
                                  {Number(selectedUnitNumber) === step.id && (
                                    <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                                      Active Module
                                    </span>
                                  )}
                                  {sectionQuiz && (
                                    <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                                      {sectionQuiz?.level === 'foundation' ? 'Foundation Final Quiz' : 'End-of-Unit Quiz'}
                                    </span>
                                  )}
                                </div>
                                <h4 className="mt-2 text-lg font-bold text-slate-900">{step.title}</h4>
                                <p className="mt-1 text-sm text-slate-600">{step.note}</p>
                              </div>
                              <div className="text-right">
                                <span className="text-xs font-semibold text-slate-500">
                                  {completedCount} of {items.length} completed ({pct}%)
                                </span>
                                <div className="mt-1.5 h-2 w-32 overflow-hidden rounded-full bg-slate-100">
                                  <div className="h-full bg-emerald-500 transition-all duration-300" style={{ width: `${pct}%` }} />
                                </div>
                                {selectedUnitNumber === null && (
                                  <button
                                    type="button"
                                    onClick={() => setSelectedUnitNumber(step.id)}
                                    className="mt-2 text-xs font-semibold text-indigo-700 hover:text-indigo-900"
                                  >
                                    Focus on this module →
                                  </button>
                                )}
                              </div>
                            </div>

                            {/* Correctly Ordered Lessons for this Module */}
                            <div className="mt-4 grid gap-3 md:grid-cols-2">
                              {items.map((item) => {
                                const isFeatured = FEATURED_LESSON_IDS.has(item.id)
                                const isDraft = isDraftLesson(item)
                                return (
                                  <article key={item.id} className={`rounded-lg p-4 border transition-all ${isFeatured ? 'is-featured border-indigo-300 bg-indigo-50/20' : 'bg-slate-50 border-slate-200'}`}>
                                    <div className="flex items-center justify-between gap-2">
                                      <div className="flex items-center gap-2 flex-wrap">
                                        <h5 className="font-semibold text-slate-900">{item.title}</h5>
                                        {item.category && (
                                          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize ${
                                            item.category === 'character' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                                            item.category === 'word' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                            item.category === 'sentence' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                                            'bg-amber-50 text-amber-700 border-amber-200'
                                          }`}>
                                            {item.category}
                                          </span>
                                        )}
                                        {isDraft && (
                                          <span className="inline-flex items-center rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-900" title="Instructional review pending">
                                            Draft · Pending review
                                          </span>
                                        )}
                                      </div>
                                      {isFeatured && (
                                        <span className="featured-badge" title="Featured curriculum lesson">
                                          ★ Featured
                                        </span>
                                      )}
                                    </div>
                                    <p className="mt-1 text-xs uppercase tracking-wide text-teal-700 font-medium">
                                      {item.level} · Lesson {item.lesson_order}
                                    </p>
                                    <p className="mt-2 text-2xl font-medium text-slate-900" dir="auto">{item.content_text}</p>
                                    {item.pronunciation_text && <p className="mt-2 text-sm text-slate-600">Say it: <strong className="text-slate-800">{item.pronunciation_text}</strong></p>}
                                    <div className="mt-3 rounded-lg border border-indigo-100 bg-white p-3">
                                      <p className="mb-2 text-sm font-semibold text-indigo-800">Reference pronunciation</p>
                                      <audio className="w-full" controls preload="none" src={`/api/v1/lessons/${item.id}/reference-audio`}>
                                        Your browser does not support audio playback.
                                      </audio>
                                      {isSanskrit && (
                                        <p className="mt-1 text-xs text-slate-500 italic">Reference voice: synthetic Indic voice, approximate for Sanskrit</p>
                                      )}
                                    </div>
                                    {item.translation_text && <p className="mt-1 text-sm text-slate-700">Meaning: {item.translation_text}</p>}
                                    {item.explanation && <p className="mt-2 text-sm text-slate-600">{item.explanation}</p>}
                                    {(() => {
                                      const progress = lessonProgress.find((p) => String(p.lesson_id) === String(item.id))
                                      const status = progress?.status || 'not started'
                                      const score = progress?.score != null ? Math.round(Number(progress.score)) : null
                                      const badgeClass = status === 'completed'
                                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                        : status === 'in_progress'
                                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                                          : 'bg-slate-100 text-slate-600 border-slate-300'
                                      const label = status === 'completed' ? 'Completed' : status === 'in_progress' ? 'In Progress' : 'Not Started'
                                      return (
                                        <div className="mt-3 flex flex-wrap items-center gap-2">
                                          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${badgeClass}`}>
                                            {label}
                                          </span>
                                          {score !== null && (
                                            <span className="text-xs font-medium text-slate-600">
                                              Score: <strong className="text-slate-800">{score}%</strong>
                                            </span>
                                          )}
                                        </div>
                                      )
                                    })()}
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      <button
                                        type="button"
                                        disabled={item.is_unlocked === false}
                                        onClick={() => saveLessonProgress(item.id, 'in_progress')}
                                        className="rounded-lg border border-teal-700 px-3 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-50"
                                      >
                                        Start / continue
                                      </button>
                                      <button
                                        type="button"
                                        disabled={item.is_unlocked === false}
                                        onClick={() => saveLessonProgress(item.id, 'completed')}
                                        className="rounded-lg bg-teal-700 px-3 py-2 text-sm font-semibold text-white hover:bg-teal-800"
                                      >
                                        Mark complete
                                      </button>
                                    </div>
                                    {item.tutorial_video_status === 'ready' && item.tutorial_video_url ? (
                                      <div className="mt-4">
                                        <p className="mb-2 text-sm font-semibold text-indigo-800">Lesson tutorial video</p>
                                        <video className="w-full rounded-lg bg-slate-900" controls src={item.tutorial_video_url}>
                                          Your browser does not support video playback.
                                        </video>
                                      </div>
                                    ) : (
                                      <p className="mt-3 text-xs text-slate-500">
                                        {item.tutorial_video_status === 'processing' ? 'Tutorial video is being prepared.' : item.tutorial_video_status === 'failed' ? 'Tutorial video is not available yet.' : 'Tutorial video has not been added yet.'}
                                      </p>
                                    )}
                                    {item.category === 'character' && !item.title.startsWith('Sound contrast:') && (
                                      <div className="mt-3 flex flex-wrap gap-2">
                                        <button
                                          type="button"
                                          disabled={item.is_unlocked === false}
                                          onClick={() => {
                                            setSelectedLessonId(item.id)
                                            const match = characters.find((character) => character.character_text === item.content_text)
                                            if (match) { setSelectedCharacterId(String(match.id)) }
                                            setShowVideoDemo(true)
                                          }}
                                          className="rounded-lg border border-indigo-300 px-4 py-2 font-semibold text-indigo-800 hover:bg-indigo-50"
                                        >
                                          Guided stroke and sound
                                        </button>
                                        <button
                                          type="button"
                                          disabled={item.is_unlocked === false}
                                          onClick={() => {
                                            setSelectedLessonId(item.id)
                                            const match = characters.find((character) => character.character_text === item.content_text)
                                            if (match) { setSelectedCharacterId(String(match.id)) }
                                            setActivePage('practice')
                                          }}
                                          className="rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800"
                                        >
                                          Practise this letter
                                        </button>
                                      </div>
                                    )}
                                  </article>
                                )
                              })}
                            </div>

                            {/* End of Module Section Quiz */}
                            {sectionQuiz && (
                              <SectionQuizPanel
                                quiz={sectionQuiz}
                                learnerId={learnerId}
                                onUpdated={loadSectionQuizzes}
                              />
                            )}

                            {/* Module Sequential Navigation Footer (When focusing on a single module) */}
                            {selectedUnitNumber !== null && (
                              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
                                <div>
                                  {prevStep ? (
                                    <button
                                      type="button"
                                      onClick={() => setSelectedUnitNumber(prevStep.id)}
                                      className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:border-indigo-400 hover:bg-slate-50"
                                    >
                                      ← Unit {prevStep.id}: {prevStep.title.split('·')[0].trim()}
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={() => setSelectedUnitNumber(null)}
                                      className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
                                    >
                                      All Modules
                                    </button>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  {nextStep ? (
                                    <button
                                      type="button"
                                      onClick={() => setSelectedUnitNumber(nextStep.id)}
                                      className="rounded-lg bg-indigo-700 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-800 shadow-sm"
                                    >
                                      Next: Unit {nextStep.id}: {nextStep.title.split('·')[0].trim()} →
                                    </button>
                                  ) : hasLessonsInNextLevel && nextLevelUnlocked ? (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setSelectedCourseLevel(nextLevelId)
                                        setSelectedUnitNumber(null)
                                      }}
                                      className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 shadow-sm"
                                    >
                                      Advance to {nextLevelId[0].toUpperCase() + nextLevelId.slice(1)} →
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={() => setSelectedUnitNumber(null)}
                                      className="rounded-lg bg-emerald-700 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-800 shadow-sm"
                                    >
                                      Completed Level Modules ✓
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </section>
                        )
                      })}
                  </div>

                  {foundationLevelQuiz && (
                    <SectionQuizPanel
                      quiz={foundationLevelQuiz}
                      learnerId={learnerId}
                      onUpdated={loadSectionQuizzes}
                    />
                  )}
                </>
              )}
            </section>
          )}

          {activePage === 'practice' && selectedCharacter && (
            <>
              <section className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50/70 p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-md bg-indigo-100 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-indigo-800">
                        Practice Studio
                      </span>
                      {activeLesson && (
                        <span className="text-xs font-semibold text-slate-600">
                          {activeLesson.level ? activeLesson.level.toUpperCase() : 'FOUNDATION'} · Unit {activeLesson.unit_number ?? 1}
                          {currentPracticeIndex >= 0 ? ` · Character ${currentPracticeIndex + 1} of ${orderedPracticeLessons.length}` : ''}
                        </span>
                      )}
                      {isActiveLessonCompleted && (
                        <span className="rounded-full border border-emerald-300 bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
                          ✓ Completed
                        </span>
                      )}
                    </div>
                    <h2 className="mt-2 text-2xl font-bold text-slate-900">
                      {activeLesson ? activeLesson.title : `Character ${selectedCharacter.character_text}`}
                    </h2>
                    <div className="mt-3 flex items-center gap-4">
                      <span className="text-6xl font-medium text-indigo-800">
                        {selectedCharacter.character_text}
                      </span>
                      <div>
                        <p className="font-semibold text-slate-800">
                          {selectedCharacter.meaning || 'Practise writing and speech'}
                        </p>
                        {selectedCharacter.pronunciation_text && (
                          <p className="text-sm text-slate-600">
                            Pronunciation target: <span className="font-semibold text-indigo-700">“{selectedCharacter.pronunciation_text}”</span>
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {activeLesson?.tutorial_video_url && (
                      <button
                        type="button"
                        onClick={() => {
                          setTutorialWatched(true)
                          setShowVideoDemo(true)
                        }}
                        className="rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800 shadow-sm"
                      >
                        ▶ Watch Sensei Kai Video
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setActivePage('lessons')}
                      className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
                    >
                      ← Back to Dashboard
                    </button>
                  </div>
                </div>

                {activeLesson && (
                  <div className="mt-4 max-w-xl rounded-lg border border-indigo-100 bg-white p-3">
                    <p className="mb-2 text-sm font-semibold text-indigo-800">Listen to the lesson example</p>
                    <audio className="w-full" controls preload="none" src={`/api/v1/lessons/${activeLesson.id}/reference-audio`}>
                      Your browser does not support audio playback.
                    </audio>
                    {isSanskrit && (
                      <p className="mt-1 text-xs text-slate-500 italic">Reference voice: synthetic Indic voice, approximate for Sanskrit</p>
                    )}
                    <p className="mt-2 text-xs text-slate-500">Listen, follow the stroke replay, then practise writing and speech below.</p>
                  </div>
                )}
              </section>

              <StrokeOrderGuide
                key={`${selectedCharacter.id}-${animationKey}-${referenceData?.reference_source?.reference_path_sha256 || ''}`}
                character={selectedCharacter}
                referenceData={referenceDataForSelectedCharacter}
                animationKey={animationKey}
                onReplay={() => setAnimationKey((current) => current + 1)}
              />
              <section className="mt-6 rounded-xl border border-indigo-100 bg-white p-4">
                <h2 className="text-lg font-bold">Reference pronunciation</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Listen to the target sound for {selectedCharacter.character_text} before recording your pronunciation.
                </p>
                {selectedCharacterLesson ? (
                  <audio
                    className="mt-3 block w-full max-w-md"
                    controls
                    preload="none"
                    src={'/api/v1/lessons/' + selectedCharacterLesson.id + '/reference-audio'}
                  >
                    Your browser does not support audio playback.
                  </audio>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">Reference audio is not available for this character yet.</p>
                )}
                {isSanskrit && (
                  <p className="mt-2 text-xs text-slate-500 italic">
                    Reference voice: synthetic Indic voice, approximate for Sanskrit.
                  </p>
                )}
              </section>

              <section className="mt-8">
                <h2 className="text-xl font-bold">Drawing practice</h2>
                <p className="mt-2 text-slate-600">
                  Draw in the box with your mouse, finger, or stylus.
                </p>

                <div className="canvas-board relative mt-4 overflow-hidden rounded-xl border-2 border-dashed border-slate-300 bg-white">
                  <ReferenceCanvasOverlay
                    characterText={selectedCharacter.character_text}
                    fontFamily={getCharacterFontFamily(selectedCharacter.character_text)}
                    strokes={referenceStrokesForSelectedCharacter}
                    showGhost={showGhost}
                  />                  <canvas
                    ref={canvasRef}
                    width={DRAWING_CANVAS_WIDTH}
                    height={DRAWING_CANVAS_HEIGHT}
                    className="drawing-canvas relative z-20 block h-auto w-full touch-none"
                    style={{ touchAction: 'none' }}
                    onPointerDown={startDrawing}
                    onPointerMove={draw}
                    onPointerUp={stopDrawing}
                    onPointerCancel={stopDrawing}
                  />
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-4">
                  <button
                    type="button"
                    onClick={clearCanvas}
                    className="rounded-lg bg-slate-200 px-4 py-2 font-semibold hover:bg-slate-300"
                  >
                    Clear drawing
                  </button>
                  <p className="text-slate-600">
                    Strokes drawn: <strong>{strokeCount}</strong>
                  </p>
                </div>
              </section>

              {authUser.role === 'admin' && (
              <details className="instructor-tools"><summary>Instructor tools · reference maintenance</summary>
              <section className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
                <h2 className="text-lg font-bold">Instructor reference setup</h2>
                <p className="mt-2 text-slate-700">
                  Draw the model for this character in the canvas above, following the reference animation. Then save it here. This is separate from a learner practice attempt.
                </p>
                <button
                  type="button"
                  onClick={saveCharacterReference}
                  disabled={savingReference}
                  className="mt-4 rounded-lg bg-amber-700 px-4 py-2 font-semibold text-white hover:bg-amber-800 disabled:opacity-60"
                >
                  {savingReference ? 'Saving reference...' : 'Save as character reference'}
                </button>
                {referenceMessage && (
                  <p className="mt-3 text-slate-700" role="status">
                    {referenceMessage}
                  </p>
                )}
                <form onSubmit={submitCharacterReferenceReview} className="mt-5 rounded-xl border border-indigo-200 bg-white p-4">
                  <h3 className="font-bold text-slate-900">Record qualified reference review</h3>
                  <p className="mt-1 text-sm text-slate-600">Review the displayed stroke paths and the saved drawing together. Approval is tied to their exact current geometry; changing the path clears approval.</p>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <label className="grid gap-1 text-sm font-medium text-slate-700">Reviewer name
                      <input required minLength={2} maxLength={120} value={referenceReviewDraft.reviewer_name} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, reviewer_name: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2" />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-slate-700">Language qualification
                      <input required minLength={5} maxLength={300} value={referenceReviewDraft.reviewer_qualification} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, reviewer_qualification: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2" placeholder="For example, Sanskrit language instructor" />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-slate-700">Reference standard and citation
                      <input required minLength={5} maxLength={500} value={referenceReviewDraft.reference_standard} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, reference_standard: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Book, syllabus, page, or URL" />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-slate-700">Writing convention
                      <input required minLength={3} maxLength={200} value={referenceReviewDraft.writing_convention} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, writing_convention: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Region, school, or style" />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-slate-700">Decision
                      <select value={referenceReviewDraft.decision} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, decision: event.target.value, attests_exact_reference: event.target.value === 'approve' ? draft.attests_exact_reference : false }))} className="rounded-lg border border-slate-300 px-3 py-2">
                        <option value="hold">Hold for more evidence</option>
                        <option value="revise">Needs revision</option>
                        <option value="approve">Approve this exact path</option>
                      </select>
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-2">Review notes
                      <textarea maxLength={2000} rows={3} value={referenceReviewDraft.notes} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, notes: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Record stroke count, order, direction, acceptable variants, or required corrections." />
                    </label>
                  </div>
                  {referenceReviewDraft.decision === 'approve' && <label className="mt-3 flex items-start gap-2 text-sm text-slate-700"><input type="checkbox" checked={referenceReviewDraft.attests_exact_reference} onChange={(event) => setReferenceReviewDraft((draft) => ({ ...draft, attests_exact_reference: event.target.checked }))} className="mt-1" /><span>I am qualified for this script and have checked this exact displayed path against the named source and convention.</span></label>}
                  <button type="submit" disabled={savingReferenceReview} className="mt-4 rounded-lg bg-indigo-700 px-4 py-2 font-semibold text-white hover:bg-indigo-800 disabled:opacity-60">{savingReferenceReview ? 'Saving review...' : 'Save review decision'}</button>
                  {referenceReviewMessage && <p className="mt-3 text-sm text-slate-700" role="status">{referenceReviewMessage}</p>}
                </form>
                <div className="mt-4 rounded-lg bg-white p-4">
                  <p className="font-semibold">Reference checklist: {characters.filter((character) => referenceStatuses[String(character.id)]).length} of {characters.length} saved</p>
                  <p className="mt-1 text-sm text-slate-600">Choose a letter, trace its correct model in the canvas, then save it. Selecting another letter clears the canvas.</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {characters.map((character) => {
                      const ready = Boolean(referenceStatuses[String(character.id)])
                      const active = String(character.id) === selectedCharacterId
                      return (
                        <button
                          key={character.id}
                          type="button"
                          onClick={() => setSelectedCharacterId(String(character.id))}
                          aria-pressed={active}
                          title={ready ? 'Reference saved' : 'Reference needed'}
                          className={`rounded-lg border px-3 py-2 ${active ? 'border-teal-700 bg-teal-50' : 'border-slate-300'} ${ready ? 'text-green-800' : 'text-slate-700'}`}
                        >
                          {character.character_text} {ready ? '✓' : '·'}
                        </button>
                      )
                    })}
                  </div>
                </div>
              </section></details>
              )}
              <div className="mt-6 rounded-xl bg-slate-50 p-4 submit-attempt-card">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold">Signed in as {authUser.name}</p>
                    <p className="text-sm text-slate-600">{authUser.email} · Account #{authUser.id}</p>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={savePracticeAttempt}
                    disabled={savingAttempt}
                    className="rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800 disabled:opacity-60 evaluate-button"
                  >
                    {savingAttempt ? 'Saving...' : 'Save drawing attempt'}
                  </button>
                  <button
                    type="button"
                    onClick={recognizeWithCnn}
                    disabled={recognizingCnn || savingAttempt}
                    className="rounded-lg bg-indigo-700 px-4 py-2 font-semibold text-white hover:bg-indigo-800 disabled:opacity-60 cnn-recognize-button"
                  >
                    {recognizingCnn ? 'Recognizing...' : 'Recognize with CNN (AI)'}
                  </button>
                </div>
                {/* Standalone CNN Recognition Card (when 'Recognize with CNN' button is clicked) */}
                {cnnResult && !cnnResult.error && (
                  <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 text-sm text-indigo-950 cnn-result-card shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-indigo-200/80 pb-2 font-semibold">
                      <span className="flex items-center gap-1.5 text-indigo-900">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-indigo-600"></span>
                        CNN AI Character Recognition
                      </span>
                      {cnnResult.status === 'character_not_supported_by_cnn' ? (
                        <span className="rounded-full border border-slate-300 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                          Not In Trained Vocabulary
                        </span>
                      ) : cnnResult.status === 'empty_canvas' ? (
                        <span className="rounded-full border border-amber-300 bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                          Empty Drawing
                        </span>
                      ) : cnnResult.is_match != null && (
                        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${
                          cnnResult.is_match
                            ? 'border-emerald-300 bg-emerald-100 text-emerald-800'
                            : 'border-amber-300 bg-amber-100 text-amber-800'
                        }`}>
                          {cnnResult.is_match ? 'Match ✓' : 'Mismatch ✗'}
                        </span>
                      )}
                    </div>

                    {cnnResult.status === 'character_not_supported_by_cnn' ? (
                      <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-slate-800">
                        <p className="font-semibold text-slate-900">
                          CNN recognition is not available for this character yet.
                        </p>
                        <p className="mt-1 text-xs text-slate-600">
                          {cnnResult.detail || 'This character is not among the trained CNN classes.'}
                        </p>
                        <p className="mt-2 text-xs font-medium text-teal-800">
                          You can still practice using the stroke guide and geometric evaluation.
                        </p>
                      </div>
                    ) : cnnResult.status === 'empty_canvas' ? (
                      <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                        {cnnResult.message || 'The canvas is blank. Please draw the character before recognition.'}
                      </div>
                    ) : cnnResult.predicted_character ? (
                      <>
                        <div className="mt-3 flex flex-wrap items-baseline gap-3">
                          {cnnResult.expected_character && !cnnResult.is_match && (
                            <span className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-sm font-semibold text-slate-700" dir="auto">
                              Target: <strong className="text-lg text-slate-900">{cnnResult.expected_character}</strong>
                            </span>
                          )}
                          <span className="text-sm font-semibold text-slate-600">
                            {cnnResult.is_match ? 'Recognized:' : 'CNN Saw:'}
                          </span>
                          <span className="text-4xl font-extrabold text-indigo-900" dir="auto">
                            {cnnResult.predicted_character}
                          </span>
                          <span className="text-sm font-medium text-slate-700">
                            Confidence: <strong>{cnnResult.confidence != null ? `${cnnResult.confidence}%` : 'N/A'}</strong>
                          </span>
                          {cnnResult.inference_time_ms != null && (
                            <span className="text-xs text-indigo-600">
                              ({cnnResult.inference_time_ms} ms CPU inference)
                            </span>
                          )}
                        </div>

                        {!cnnResult.is_match && cnnResult.message && (
                          <p className="mt-2 rounded border border-amber-200 bg-amber-50 p-2 text-xs font-medium text-amber-900">
                            {cnnResult.message}
                          </p>
                        )}

                        {cnnResult.confidence != null && cnnResult.confidence < 40 && (
                          <p className="mt-2 rounded border border-amber-200 bg-amber-100/70 p-1.5 text-xs font-medium text-amber-800">
                            Recognition confidence is low; please redraw the character clearly.
                          </p>
                        )}

                        {cnnResult.top_predictions && cnnResult.top_predictions.length > 1 && (
                          <div className="mt-2 text-xs text-indigo-900/90">
                            <span className="font-semibold">Top candidates:</span>{' '}
                            {cnnResult.top_predictions.map((p) => `${p.character} (${p.confidence}%)`).join(' · ')}
                          </div>
                        )}
                        <div className="mt-1.5 text-[11px] text-slate-500">
                          Model: {cnnResult.model_name || 'StrokeSpeak CNN'} · OpenCV 32×32 pipeline
                        </div>
                      </>
                    ) : (
                      <p className="mt-2 text-xs text-slate-700">{cnnResult.detail || cnnResult.message}</p>
                    )}
                  </div>
                )}

                {/* Structured Attempt Evaluation Summary (when 'Save drawing attempt' is clicked) */}
                {latestAttemptResult && (
                  <div className={`mt-4 rounded-xl border bg-white p-4 shadow-sm text-slate-800 practice-evaluation-card ${
                    latestAttemptResult.assessment?.passed === false
                      ? 'border-amber-300'
                      : 'border-teal-200'
                  }`}>
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                      <div>
                        <h4 className="flex items-center gap-2 text-base font-bold text-slate-900">
                          <span className={`inline-block h-2.5 w-2.5 rounded-full ${
                            latestAttemptResult.assessment?.passed === false ? 'bg-amber-500' : 'bg-teal-600'
                          }`}></span>
                          Handwriting Evaluation Summary
                        </h4>
                        <p className="text-xs text-slate-500">
                          Attempt #{latestAttemptResult.attempt_id} · Saved to MySQL
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full border px-3 py-1 text-xs font-bold ${
                          latestAttemptResult.assessment?.passed === false
                            ? 'border-amber-300 bg-amber-100 text-amber-900'
                            : 'border-emerald-300 bg-emerald-100 text-emerald-800'
                        }`}>
                          {latestAttemptResult.assessment?.status === 'mismatch_rejected'
                            ? 'Mismatch — Retry Required ✗'
                            : latestAttemptResult.assessment?.status === 'stroke_order_retry'
                            ? 'Stroke Order Retry ✗'
                            : latestAttemptResult.assessment?.passed === false
                            ? 'Needs Retry ✗'
                            : 'Assessment Passed ✓'}
                        </span>
                        {latestAttemptResult.assessment?.passed === false && (
                          <button
                            type="button"
                            onClick={retryCurrentCharacter}
                            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          >
                            ↻ Retry
                          </button>
                        )}
                      </div>
                    </div>

                    {/* 3 Metric Cards Grid */}
                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                      {/* 1. Geometric Shape Similarity */}
                      <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3">
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Geometric Similarity
                        </p>
                        <div className="mt-1 flex items-baseline gap-1">
                          <span className="text-2xl font-extrabold text-slate-900">
                            {latestAttemptResult.scores?.handwriting != null
                              ? latestAttemptResult.scores.handwriting
                              : '—'}
                          </span>
                          {latestAttemptResult.scores?.handwriting != null && (
                            <span className="text-xs text-slate-500">/ 100</span>
                          )}
                        </div>
                        <p className="mt-1 text-[11px] text-slate-600">
                          {latestAttemptResult.assessment?.status === 'mismatch_rejected'
                            ? 'Overlap only (wrong character)'
                            : latestAttemptResult.scores?.handwriting == null
                            ? 'Reference pending'
                            : latestAttemptResult.scores.handwriting >= 85
                            ? 'Close to reference ✓'
                            : latestAttemptResult.scores.handwriting >= 60
                            ? 'Moderately similar'
                            : 'Needs practice'}
                        </p>
                      </div>

                      {/* 2. Stroke Order Score */}
                      <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3">
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Stroke Order
                        </p>
                        <div className="mt-1 flex items-baseline gap-1">
                          <span className="text-2xl font-extrabold text-slate-900">
                            {latestAttemptResult.scores?.stroke_order != null
                              ? latestAttemptResult.scores.stroke_order
                              : '—'}
                          </span>
                          {latestAttemptResult.scores?.stroke_order != null && (
                            <span className="text-xs text-slate-500">/ 100</span>
                          )}
                        </div>
                        <p className="mt-1 text-[11px] text-slate-600">
                          {latestAttemptResult.scores?.stroke_order == null
                            ? 'Reference pending'
                            : latestAttemptResult.scores.stroke_order >= 85
                            ? 'Accurate sequence ✓'
                            : latestAttemptResult.scores.stroke_order >= 60
                            ? 'Partly matched'
                            : 'Review guide'}
                        </p>
                      </div>

                      {/* 3. CNN AI Recognition Card */}
                      <div className={`rounded-lg border p-3 ${
                        latestAttemptResult.cnn_recognition?.status === 'character_not_supported_by_cnn'
                          ? 'border-slate-200 bg-slate-50/70'
                          : latestAttemptResult.cnn_recognition?.is_match
                          ? 'border-emerald-200 bg-emerald-50/40'
                          : 'border-indigo-100 bg-indigo-50/40'
                      }`}>
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                          CNN Recognition
                        </p>

                        {latestAttemptResult.cnn_recognition?.status === 'character_not_supported_by_cnn' ? (
                          <div className="mt-1.5">
                            <span className="inline-block rounded bg-slate-200 px-1.5 py-0.5 text-[11px] font-semibold text-slate-700">
                              Not In CNN Set
                            </span>
                            <p className="mt-1 text-[11px] leading-tight text-slate-600">
                              CNN recognition is not available for this character yet. Geometric evaluation active.
                            </p>
                          </div>
                        ) : latestAttemptResult.cnn_recognition?.status === 'empty_canvas' ? (
                          <div className="mt-1.5 text-xs text-amber-700">
                            Empty / Insufficient Ink
                          </div>
                        ) : latestAttemptResult.cnn_recognition?.predicted_character ? (
                          <div>
                            <div className="mt-1 flex items-baseline gap-2">
                              <span className="text-2xl font-black text-indigo-950" dir="auto">
                                {latestAttemptResult.cnn_recognition.predicted_character}
                              </span>
                              <span className="text-xs font-semibold text-slate-700">
                                {latestAttemptResult.cnn_recognition.confidence != null ? `${latestAttemptResult.cnn_recognition.confidence}%` : ''}
                              </span>
                            </div>
                            <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-bold ${
                              latestAttemptResult.cnn_recognition.is_match
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}>
                              {latestAttemptResult.cnn_recognition.is_match ? 'Match ✓' : 'Mismatch ✗'}
                            </span>
                          </div>
                        ) : (
                          <p className="mt-2 text-xs text-slate-500">Geometric comparison only</p>
                        )}
                      </div>
                    </div>

                    {/* Learner Feedback Section */}
                    {latestAttemptResult.feedback && (
                      <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700">
                        <span className="font-semibold text-slate-900">Feedback: </span>
                        {latestAttemptResult.feedback}
                      </div>
                    )}
                  </div>
                )}

                {attemptMessage && (
                  <p className="mt-3 text-sm text-slate-700" role="status">
                    {attemptMessage}
                  </p>
                )}
              </div>

              <section className="mt-8 border-t border-slate-200 pt-6">
                <h2 className="text-xl font-bold">Speaking practice (local recording & reference audio)</h2>
                <p className="mt-2 text-slate-600">
                  Say “{selectedCharacter.pronunciation_text || selectedCharacter.character_text}”,
                  then play your recording back to self-compare with reference pronunciation.
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  Hold the sound clearly for about one second before stopping. Whisper checks its written transcript against the target; short sounds may be misheard, and this is not a direct articulation score.
                </p>

                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`mt-4 rounded-lg px-4 py-2 font-semibold text-white ${
                    isRecording
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                >
                  {isRecording ? 'Stop recording' : 'Start recording'}
                </button>

                {audioUrl && (
                  <div className="mt-4 space-y-3">
                    <audio className="block w-full max-w-md" controls src={audioUrl} />

                    {!activeAttemptId && (
                      <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-800">
                        Please save a drawing attempt above first so this audio recording can be linked to your practice attempt.
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={savePronunciationAudio}
                        disabled={savingAudio || !activeAttemptId || !recordedAudio}
                        className={`rounded-lg px-4 py-2 text-sm font-semibold text-white ${
                          savingAudio || !activeAttemptId || !recordedAudio
                            ? 'cursor-not-allowed bg-slate-400'
                            : 'bg-emerald-600 hover:bg-emerald-700'
                        }`}
                      >
                        {savingAudio ? 'Saving recording…' : 'Save pronunciation'}
                      </button>

                      <button
                        type="button"
                        onClick={() => transcribePronunciation(activeAttemptId)}
                        disabled={Boolean(transcribingAttemptId) || !activeAttemptId || !audioUploaded}
                        className={`rounded-lg px-4 py-2 text-sm font-semibold text-white ${
                          Boolean(transcribingAttemptId) || !activeAttemptId || !audioUploaded
                            ? 'cursor-not-allowed bg-slate-400'
                            : 'bg-indigo-600 hover:bg-indigo-700'
                        }`}
                        title={!audioUploaded ? 'Save your pronunciation first to assess with Whisper' : ''}
                      >
                        {transcribingAttemptId === activeAttemptId ? 'Transcribing with Whisper…' : 'Assess speech with Whisper'}
                      </button>
                    </div>

                    {audioSaveMessage && (
                      <div className="rounded-lg border border-slate-200 bg-slate-100 p-3 text-sm text-slate-800">
                        {audioSaveMessage}
                      </div>
                    )}

                    {pronunciationResult && (
                      <div
                        className={`rounded-xl border p-4 text-sm shadow-sm ${
                          pronunciationResult.isError
                            ? 'border-red-200 bg-red-50 text-red-900'
                            : 'border-indigo-200 bg-indigo-50/70 text-slate-800'
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-xs font-bold uppercase tracking-wide text-indigo-900">
                            Whisper Speech &amp; Transcript Evaluation
                          </span>
                          {pronunciationResult.isError ? (
                            <span className="rounded-full border border-red-300 bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-800">
                              Audio Rejected
                            </span>
                          ) : (
                            <span
                              className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${
                                pronunciationResult.score >= 90
                                  ? 'border-emerald-300 bg-emerald-100 text-emerald-800'
                                  : pronunciationResult.score >= 70
                                  ? 'border-indigo-300 bg-indigo-100 text-indigo-800'
                                  : 'border-amber-300 bg-amber-100 text-amber-800'
                              }`}
                            >
                              {pronunciationResult.score >= 90
                                ? `Strong Match (${pronunciationResult.score}%)`
                                : pronunciationResult.score >= 70
                                ? `Partial Match (${pronunciationResult.score}%)`
                                : `Transcript Differs (${pronunciationResult.score}%)`}
                            </span>
                          )}
                        </div>

                        {pronunciationResult.isError ? (
                          <p className="mt-2 text-xs font-medium text-red-800">
                            {pronunciationResult.feedback}
                          </p>
                        ) : (
                          <>
                            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                              <div className="rounded-lg border border-slate-200 bg-white p-2.5">
                                <span className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                                  Expected Target
                                </span>
                                <span className="mt-0.5 block text-base font-bold text-slate-900" dir="auto">
                                  {pronunciationResult.characterText} ({pronunciationResult.targetText})
                                </span>
                              </div>
                              <div className="rounded-lg border border-slate-200 bg-white p-2.5">
                                <span className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                                  Whisper Heard
                                </span>
                                <span className="mt-0.5 block text-base font-bold text-indigo-900" dir="auto">
                                  “{pronunciationResult.transcribedText}”
                                </span>
                              </div>
                            </div>
                            <p className="mt-2.5 text-xs font-medium text-slate-800">
                              {pronunciationResult.feedback}
                            </p>
                            <p className="mt-1 text-[11px] text-slate-500">
                              {pronunciationResult.scoreNote} ({pronunciationResult.provider}
                              {pronunciationResult.detectedLanguage ? ` · lang: ${pronunciationResult.detectedLanguage}` : ''})
                            </p>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </section>

              {/* Unit Progress Bar, Completion Checklist & Sequential Character Navigation */}
              {unitTotalCount > 0 && (
                <section className="mt-6 rounded-xl border border-indigo-200/80 bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold text-slate-700">
                    <span>
                      Unit {activeLesson?.unit_number ?? 1} Progress: {unitCompletedCount} / {unitTotalCount} characters completed
                    </span>
                    <span className="text-indigo-700">{unitProgressPercent}%</span>
                  </div>
                  <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-200" role="progressbar" aria-valuenow={unitProgressPercent} aria-valuemin={0} aria-valuemax={100}>
                    <div className="h-full rounded-full bg-emerald-600 transition-all duration-300" style={{ width: `${unitProgressPercent}%` }} />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        disabled={!prevPracticeLesson}
                        onClick={() => navigateToPracticeLesson(prevPracticeLesson)}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        ← Previous Character
                      </button>
                      <button
                        type="button"
                        disabled={!nextPracticeLesson}
                        onClick={() => navigateToPracticeLesson(nextPracticeLesson)}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        Next Character →
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={retryCurrentCharacter}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        ↻ Retry Practice
                      </button>
                      {activeLesson && (
                        <button
                          type="button"
                          disabled={!canMarkCompleted || savingProgressLessonId === activeLesson.id}
                          onClick={() => saveLessonProgress(activeLesson.id, 'completed')}
                          className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm ${
                            isActiveLessonCompleted
                              ? 'bg-emerald-700 opacity-90 cursor-default'
                              : canMarkCompleted
                              ? 'bg-emerald-600 hover:bg-emerald-700'
                              : 'bg-slate-400 cursor-not-allowed'
                          }`}
                        >
                          {isActiveLessonCompleted
                            ? '✓ Completed'
                            : savingProgressLessonId === activeLesson.id
                            ? 'Saving…'
                            : '✓ Mark as Completed'}
                        </button>
                      )}
                      {(unitCompletedCount >= unitTotalCount || (!nextPracticeLesson && isActiveLessonCompleted)) && (
                        <button
                          type="button"
                          onClick={() => setActivePage('lessons')}
                          className="rounded-lg bg-indigo-700 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-800 shadow-sm"
                        >
                          Take Section Quiz →
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Completion Checklist */}
                  <div className="mt-3 grid grid-cols-2 gap-2 border-t border-slate-100 pt-2.5 text-xs sm:grid-cols-4">
                    <span className={tutorialDone ? 'font-semibold text-emerald-700' : 'text-slate-500'}>
                      {tutorialDone ? '✓' : '○'} {activeLesson?.tutorial_video_url ? 'Tutorial watched' : 'Tutorial (optional)'}
                    </span>
                    <span className={handwritingDone ? 'font-semibold text-emerald-700' : 'text-slate-500'}>
                      {handwritingDone ? '✓' : '○'} Handwriting drawn
                    </span>
                    <span className={evaluationDone ? 'font-semibold text-emerald-700' : 'text-slate-500'}>
                      {evaluationDone ? '✓' : '○'} CNN / Stroke evaluated
                    </span>
                    <span className={pronunciationDone ? 'font-semibold text-emerald-700' : 'text-slate-500'}>
                      {pronunciationDone ? '✓' : '○'} Pronunciation saved
                    </span>
                  </div>
                  {progressMessage && (
                    <p className="mt-2 text-xs font-medium text-emerald-800" role="status">
                      {progressMessage}
                    </p>
                  )}
                </section>
              )}
            </>
          )}

          {activePage === 'practice' && !selectedCharacter && (
            <section className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <span className="text-4xl" role="img" aria-label="pen">✍</span>
              <h2 className="mt-3 text-xl font-bold text-slate-800">Practice Studio is Ready</h2>
              <p className="mt-1 text-sm text-slate-600 max-w-md mx-auto">
                Select a character or lesson from the Dashboard to begin stroke-order animation, handwriting canvas practice, and speech evaluation.
              </p>
              <button
                type="button"
                onClick={() => setActivePage('lessons')}
                className="mt-4 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800 shadow-sm"
              >
                Go to Dashboard
              </button>
            </section>
          )}

          {activePage === 'progress' && (
            <>
              <section className="mt-6 rounded-xl border border-teal-200 bg-teal-50 p-4">
                <h2 className="text-lg font-bold">Lesson progress</h2>
                <p className="mt-2 text-sm text-slate-700">
                  {progressCompletedLessonCount} completed · {progressInProgressLessonCount} in progress
                </p>
                {progressMessage && <p className="mt-2 text-sm text-teal-800" role="status">{progressMessage}</p>}
                <button
                  type="button"
                  onClick={() => loadLessonProgress().catch(() => setProgressMessage('Could not refresh lesson progress.'))}
                  className="mt-3 rounded-lg bg-white px-3 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-100"
                >
                  Refresh lesson progress
                </button>
                {progressLessonEntries.length === 0 ? (
                  <p className="mt-3 text-sm text-slate-600">No lessons are complete or in progress yet.</p>
                ) : (
                  <ul className="mt-3 space-y-2">
                    {progressLessonEntries.map(({ item, progress }) => {
                      const status = progress.status
                      const label = status === 'completed' ? 'Completed' : status === 'processing' ? 'Processing' : 'In Progress'
                      const badgeClass = status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                      const score = progress.score != null ? Math.round(Number(progress.score)) : null
                      return (
                        <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white p-3 text-sm">
                          <span>{item.title}</span>
                          <span className="flex items-center gap-2">
                            <span className={`rounded px-2 py-0.5 text-xs font-semibold ${badgeClass}`}>{label}</span>
                            {score !== null && <span className="text-xs font-bold text-slate-700">{score}%</span>}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </section>

              <section className="mt-6 rounded-xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">Practice assessments</h2>
                    <p className="mt-1 text-sm text-slate-600">Showing complete assessments and assessments in progress.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => loadPracticeAttempts().catch(() => setAttemptMessage('Could not load saved attempts.'))}
                    className="rounded-lg bg-slate-200 px-3 py-2 font-semibold hover:bg-slate-300"
                  >
                    Refresh history
                  </button>
                </div>
                {progressPracticeAttempts.length === 0 ? (
                  <p className="mt-3 text-slate-600">No completed or in-progress practice assessments yet.</p>
                ) : (
                  <div className="mt-4 space-y-3">
                    {progressPracticeAttempts.map((attempt) => {
                      const processing = isPracticeAttemptProcessing(attempt, transcribingAttemptId)
                      const transcribing = String(transcribingAttemptId) === String(attempt.attempt_id)
                      const statusLabel = transcribing ? 'Processing' : processing ? 'In Progress' : 'Completed'
                      const statusClass = processing ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                      const scoreSummary = [
                        attempt.handwriting_score != null ? `Handwriting ${Math.round(Number(attempt.handwriting_score))}%` : null,
                        attempt.stroke_order_score != null ? `Stroke order ${Math.round(Number(attempt.stroke_order_score))}%` : null,
                        attempt.pronunciation_score != null ? `Transcript match ${Math.round(Number(attempt.pronunciation_score))}%` : null,
                      ].filter(Boolean).join(' · ')
                      return (
                        <article key={attempt.attempt_id} className="rounded-lg bg-slate-50 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-semibold">Attempt {attempt.attempt_id} · Character {attempt.character_text}</p>
                            <span className="flex items-center gap-2">
                              <span className={`rounded px-2 py-0.5 text-xs font-semibold ${statusClass}`}>{statusLabel}</span>
                              <span className="text-sm text-slate-500">{new Date(attempt.created_at).toLocaleString()}</span>
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-slate-600">Strokes: {attempt.stroke_count ?? 0}{scoreSummary ? ` · ${scoreSummary}` : ''}</p>
                          {attempt.transcribed_text && <p className="mt-2 text-sm text-slate-700">Recognized speech: {attempt.transcribed_text}</p>}
                          {attempt.pronunciation_feedback && <p className="mt-2 rounded-md bg-indigo-50 p-3 text-sm text-indigo-900">{attempt.pronunciation_feedback}</p>}
                          {attempt.pronunciation_status === 'pending_assessment' && (
                            <button
                              type="button"
                              onClick={() => transcribePronunciation(attempt.attempt_id)}
                              disabled={transcribingAttemptId === attempt.attempt_id}
                              className="mt-2 rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400"
                            >
                              {transcribingAttemptId === attempt.attempt_id ? 'Processing…' : 'Continue speech assessment'}
                            </button>
                          )}
                          {attempt.feedback && (
                            <p className="mt-2 rounded-md border border-teal-100 bg-white p-3 text-sm text-slate-700">
                              <strong>Feedback:</strong> {attempt.feedback}
                            </p>
                          )}
                        </article>
                      )
                    })}
                  </div>
                )}
              </section>
            </>
          )}
          {activePage === 'practice' && !selectedCharacter && (
            <section className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <span className="text-4xl" role="img" aria-label="pen">✍</span>
              <h2 className="mt-3 text-xl font-bold text-slate-800">Practice Studio is Ready</h2>
              <p className="mt-1 text-sm text-slate-600 max-w-md mx-auto">
                Select a character or lesson from the Dashboard to begin stroke-order animation, handwriting canvas practice, and speech evaluation.
              </p>
              <button
                type="button"
                onClick={() => setActivePage('lessons')}
                className="mt-4 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800 shadow-sm"
              >
                Go to Dashboard
              </button>
            </section>
          )}
        </section>
        {showVideoDemo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4" role="dialog" aria-modal="true" aria-labelledby="video-demo-title" onClick={() => setShowVideoDemo(false)}>
            <section className="modal-dialog max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-5 shadow-2xl" onClick={(event) => event.stopPropagation()}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-indigo-700">Interactive guided lesson</p>
                  <h2 id="video-demo-title" className="mt-1 text-2xl font-bold">{selectedCharacter?.character_text || 'Character'} · {selectedCharacter?.pronunciation_text || 'sound and strokes'}</h2>
                </div>
                <button type="button" onClick={() => setShowVideoDemo(false)} className="rounded-lg bg-slate-100 px-3 py-2 font-semibold hover:bg-slate-200">Close</button>
              </div>
              <p className="mt-3 text-sm text-slate-600">Follow Sensei Kai's AI teacher video tutorial and verified stroke replay.</p>
              {selectedCharacterLesson?.tutorial_video_status === 'ready' && selectedCharacterLesson?.tutorial_video_url && (
                <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50/60 p-3">
                  <p className="mb-2 text-sm font-semibold text-indigo-800">AI Teacher Video Tutorial · Sensei Kai</p>
                  <video className="w-full rounded-lg bg-slate-900 shadow-md" controls autoPlay playsInline preload="metadata" src={selectedCharacterLesson.tutorial_video_url}>
                    Your browser does not support video playback.
                  </video>
                </div>
              )}
              {selectedCharacter && (
                <StrokeOrderGuide
                  key={`${selectedCharacter.id}-${animationKey}-${referenceData?.reference_source?.reference_path_sha256 || ''}`}
                  character={selectedCharacter}
                  referenceData={referenceDataForSelectedCharacter}
                  animationKey={animationKey}
                  onReplay={() => setAnimationKey((current) => current + 1)}
                />
              )}
              <section className="mt-4 rounded-xl bg-indigo-50 p-4">
                <h3 className="font-bold text-indigo-900">Lesson steps</h3>
                <ol className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                  <li className="rounded-lg bg-white p-3"><strong>1. Watch</strong><br />Follow the stroke path in order.</li>
                  <li className="rounded-lg bg-white p-3"><strong>2. Listen</strong><br />Hear the saved reference pronunciation.</li>
                  <li className="rounded-lg bg-white p-3"><strong>3. Practise</strong><br />Trace the character and review your attempt.</li>
                </ol>
                {selectedCharacterLesson ? (
                  <audio className="mt-4 w-full" controls preload="none" src={`/api/v1/lessons/${selectedCharacterLesson.id}/reference-audio`}>
                    Your browser does not support audio playback.
                  </audio>
                ) : (
                  <p className="mt-3 text-sm text-amber-800">No matching lesson audio is available for this character yet.</p>
                )}
                <button
                  type="button"
                  onClick={() => { setShowVideoDemo(false); setActivePage('practice') }}
                  className="mt-4 rounded-lg bg-indigo-700 px-4 py-2 font-semibold text-white hover:bg-indigo-800"
                >
                  Open drawing and speech practice
                </button>
              </section>
            </section>
          </div>
        )}
      <footer className="workspace-footer">
        <strong>StrokeSpeak</strong>
        <span>Multilingual handwriting and pronunciation practice</span>
      </footer>
      </div>
    </main>
  )
}

function App() {
  const [authUser, setAuthUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)

  useEffect(() => {
    const token = getAuthToken()
    if (!token) {
      setAuthReady(true)
      return
    }
    let active = true
    apiFetch('/api/v1/auth/me')
      .then(async (response) => {
        const data = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(data.detail || 'Your sign-in expired. Please sign in again.')
        if (active) setAuthUser(data.user)
      })
      .catch(() => { if (active) clearAuthToken() })
      .finally(() => { if (active) setAuthReady(true) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    function handleUnauthorized() { setAuthUser(null) }
    window.addEventListener('strokespeak:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('strokespeak:unauthorized', handleUnauthorized)
  }, [])

  function handleAuthenticated(user, token) {
    setAuthToken(token)
    setAuthUser(user)
  }

  function handleLogout() {
    clearAuthToken()
    setAuthUser(null)
  }

  function handleProfileUpdated(user) {
    setAuthUser(user)
  }

  if (!authReady) return <main className="auth-page"><p className="auth-loading">Opening your StrokeSpeak account…</p></main>
  if (!authUser) return <AuthPanel onAuthenticated={handleAuthenticated} />
  return <StrokeSpeakWorkspace key={authUser.id} authUser={authUser} onLogout={handleLogout} onProfileUpdated={handleProfileUpdated} />
}

export default App





























