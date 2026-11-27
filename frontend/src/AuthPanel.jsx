import { useState } from "react"
import { apiFetch } from "./api"
import BrandLogo from "./BrandLogo"

export default function AuthPanel({ onAuthenticated }) {
  const [mode, setMode] = useState("login") // 'login' | 'register'
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [forgotEmail, setForgotEmail] = useState("")
  const [forgotSent, setForgotSent] = useState(false)
  const [showGoogleModal, setShowGoogleModal] = useState(false)
  const [googleEmail, setGoogleEmail] = useState("chetan@example.com")
  const [googleBusy, setGoogleBusy] = useState(false)
  const [googleMessage, setGoogleMessage] = useState("")

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage("")
    try {
      const isRegister = mode === "register"
      const response = await apiFetch(`/api/v1/auth/${isRegister ? "register" : "login"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(isRegister ? { name, email, password } : { email, password }),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data.detail || "Could not log in. Please check your credentials.")
      onAuthenticated(data.user, data.token)
    } catch (error) {
      setMessage(error.message || "Could not connect to StrokeSpeak.")
    } finally {
      setBusy(false)
    }
  }

  async function handleGoogleDirectLogin() {
    setGoogleBusy(true)
    setGoogleMessage("")
    try {
      const gEmail = googleEmail.trim() || "chetan@example.com"
      const gName = gEmail.split("@")[0] || "Learner"
      const gPass = "GoogleOAuthLocalPass2026!"

      let res = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: gEmail, password: gPass }),
      })
      let data = await res.json().catch(() => ({}))

      if (!res.ok) {
        res = await apiFetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: gName, email: gEmail, password: gPass }),
        })
        data = await res.json().catch(() => ({}))
      }

      if (!res.ok) {
        throw new Error(data.detail || "Could not authenticate Google account.")
      }

      setShowGoogleModal(false)
      onAuthenticated(data.user, data.token)
    } catch (err) {
      setGoogleMessage(err.message || "Google authentication failed.")
    } finally {
      setGoogleBusy(false)
    }
  }

  function handleForgotPasswordSubmit(e) {
    e.preventDefault()
    if (!forgotEmail) return
    setForgotSent(true)
  }

  return (
    <main className="auth-page">
      <div className="auth-layout">
        {/* Left Hero Showcase Pane (Matching Reference Design) */}
        <section className="auth-hero-pane">
          <BrandLogo size="auth-hero" className="auth-brand auth-brand--hero" />

          <div className="space-y-4">
            <h1 className="auth-hero-title">
              Master Non-<br />
              Latin Scripts<br />
              with AI
            </h1>
            <p className="auth-hero-desc">
              Learn Devanagari, Hiragana and more with interactive practice, real-time AI feedback and personalized learning paths.
            </p>
          </div>

          <div className="auth-features-row">
            <div className="auth-feature-item">
              <span className="auth-feature-icon" aria-hidden="true">✍</span>
              <div className="auth-feature-text">
                <span className="auth-feature-title">Handwriting</span>
                <span className="auth-feature-sub">Recognition</span>
              </div>
            </div>
            <div className="auth-feature-item">
              <span className="auth-feature-icon" aria-hidden="true">🎙</span>
              <div className="auth-feature-text">
                <span className="auth-feature-title">Speech</span>
                <span className="auth-feature-sub">Analysis</span>
              </div>
            </div>
            <div className="auth-feature-item">
              <span className="auth-feature-icon" aria-hidden="true">📊</span>
              <div className="auth-feature-text">
                <span className="auth-feature-title">Progress</span>
                <span className="auth-feature-sub">Tracking</span>
              </div>
            </div>
          </div>
        </section>

        {/* Right Floating Authentication Card */}
        <section className="auth-card-pane">
          <div className="auth-card">
            {/* Centered Brand Header */}
            <div className="auth-card-header">
              <h2 className="auth-brand-heading"><BrandLogo size="auth-card" className="auth-brand auth-brand--card" /></h2>
              <p className="auth-card-welcome">Welcome to StrokeSpeak</p>
              <p className="auth-card-subtitle">Your AI Language Tutor</p>
            </div>

            {/* Mode Tabs: Login | Register */}
            <div className="auth-tab-bar" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === "login"}
                onClick={() => { setMode("login"); setMessage("") }}
                className={`auth-tab-btn ${mode === "login" ? "active" : ""}`}
              >
                Login
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "register"}
                onClick={() => { setMode("register"); setMessage("") }}
                className={`auth-tab-btn ${mode === "register" ? "active" : ""}`}
              >
                Register
              </button>
            </div>

            {/* 1. Direct Google Account Login Button */}
            <button
              type="button"
              onClick={() => setShowGoogleModal(true)}
              className="auth-google-btn"
              title="Quick sign-in with Google (Local profile preview)"
            >
              <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.14z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
              </svg>
              <span>Sign in with Google (Local Sandbox)</span>
            </button>

            <div className="auth-divider">or</div>

            {/* Email / Password Form */}
            <form onSubmit={submit} className="auth-form">
              {mode === "register" && (
                <div className="auth-input-group">
                  <label className="auth-input-label" htmlFor="auth-name">Your name</label>
                  <input
                    id="auth-name"
                    type="text"
                    autoComplete="name"
                    placeholder="Learner name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    minLength={2}
                    maxLength={100}
                    required
                    className="auth-text-input"
                  />
                </div>
              )}

              <div className="auth-input-group">
                <label className="auth-input-label" htmlFor="auth-email">Email address</label>
                <input
                  id="auth-email"
                  type="email"
                  autoComplete="email"
                  placeholder="chetan@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  maxLength={255}
                  required
                  className="auth-text-input"
                />
              </div>

              <div className="auth-input-group">
                <div className="auth-input-label-row">
                  <label className="auth-input-label" htmlFor="auth-password">Password</label>
                  {/* 3. Add Forgot Password */}
                  <button
                    type="button"
                    onClick={() => { setShowForgotPassword(true); setForgotSent(false); setForgotEmail(email); }}
                    className="auth-forgot-link"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="auth-password-control">
                  <input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete={mode === "register" ? "new-password" : "current-password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    minLength={mode === "register" ? 8 : 1}
                    maxLength={128}
                    required
                    className="auth-text-input"
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowPassword((visible) => !visible)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {message && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 text-xs text-red-700" role="alert">
                  {message}
                </div>
              )}

              <button type="submit" className="auth-submit-btn" disabled={busy}>
                <span>{busy ? "Please wait…" : mode === "register" ? "Create profile →" : "Sign in to learn →"}</span>
              </button>
            </form>

            {/* Bottom Switcher */}
            <div className="auth-card-footer">
              <p className="auth-footer-or">or</p>
              {mode === "login" ? (
                <button
                  type="button"
                  onClick={() => { setMode("register"); setMessage(""); }}
                  className="auth-toggle-link"
                >
                  Create profile
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => { setMode("login"); setMessage(""); }}
                  className="auth-toggle-link"
                >
                  Already have an account? Log in
                </button>
              )}
            </div>
          </div>
        </section>
      </div>

      <footer className="auth-page-footer">
        <strong>StrokeSpeak</strong>
        <span>Multilingual handwriting and pronunciation practice</span>
      </footer>
      {/* Forgot Password Modal (Honest Development Notice) */}
      {showForgotPassword && (
        <div className="auth-modal-backdrop" onClick={() => setShowForgotPassword(false)}>
          <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900">Password Recovery Notice</h3>
              <button
                type="button"
                onClick={() => setShowForgotPassword(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900 leading-relaxed">
                <p className="font-bold text-sm mb-1">Local Deployment Notice</p>
                <p>
                  Automated self-service email password recovery is not configured in this local environment (no SMTP service attached).
                </p>
                <p className="mt-2">
                  To reset credentials for <strong>{email || "your account"}</strong>, please contact the database administrator or register a new profile with another email address.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(false)}
                  className="w-full rounded-xl bg-indigo-700 py-2.5 text-xs font-semibold text-white hover:bg-indigo-800"
                >
                  Understood · Return to login
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Direct Google Account Login Modal (Explicit Sandbox Notice) */}
      {showGoogleModal && (
        <div className="auth-modal-backdrop" onClick={() => setShowGoogleModal(false)}>
          <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.14z"/>
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                  <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                </svg>
                <h3 className="text-lg font-bold text-slate-900">Google Sandbox Sign-In</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>Development Sandbox Mode:</strong> Live Google Identity OAuth2 requires client credentials and an active internet connection. This action logs into or creates a local sandbox learner profile for the email below.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1" htmlFor="google-email">
                  Google Account Email
                </label>
                <input
                  id="google-email"
                  type="email"
                  required
                  placeholder="chetan@example.com"
                  value={googleEmail}
                  onChange={(e) => setGoogleEmail(e.target.value)}
                  className="auth-text-input"
                />
              </div>

              {googleMessage && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 text-xs text-red-700">
                  {googleMessage}
                </div>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowGoogleModal(false)}
                  className="flex-1 rounded-xl border border-slate-300 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={googleBusy}
                  onClick={handleGoogleDirectLogin}
                  className="flex-1 rounded-xl bg-indigo-700 py-2.5 text-xs font-semibold text-white hover:bg-indigo-800 disabled:opacity-60 shadow-sm"
                >
                  {googleBusy ? "Connecting…" : "Sign In with Sandbox Profile →"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
