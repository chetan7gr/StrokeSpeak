export default function BrandLogo({ size = "sidebar", showName = true, className = "" }) {
  return (
    <span className={"strokespeak-brand " + className}>
      <span className={"strokespeak-mark strokespeak-mark--" + size} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" focusable="false">
          <path
            d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
            stroke="currentColor"
            strokeWidth="2.1"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {showName && <span className="strokespeak-wordmark">StrokeSpeak</span>}
    </span>
  )
}
