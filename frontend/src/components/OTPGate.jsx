import { useState, useRef, useEffect, useCallback } from 'react'
import { Phone, ShieldCheck, ArrowRight, Loader, RefreshCw, Lock } from 'lucide-react'
import { sendOTP, verifyOTP } from '../api'
import './OTPGate.css'

export default function OTPGate({ room, onVerified }) {
  const [step, setStep] = useState('phone') // 'phone' | 'otp' | 'verified'
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [demoCode, setDemoCode] = useState('')
  const [countdown, setCountdown] = useState(0)
  const inputRefs = useRef([])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown])

  const handleSendOTP = async (e) => {
    e.preventDefault()
    setError('')
    const phone = phoneNumber.trim()
    if (!phone || phone.length < 7) {
      setError('Enter a valid phone number')
      return
    }
    setLoading(true)
    try {
      const data = await sendOTP(phone, room.slug)
      setDemoCode(data.otp_code || '')
      setStep('otp')
      setCountdown(data.expires_in || 300)
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = useCallback(async (code) => {
    setError('')
    setLoading(true)
    try {
      await verifyOTP(phoneNumber.trim(), room.slug, code)
      setStep('verified')
      // Store verification in sessionStorage
      const key = `otp-verified-${room.slug}`
      sessionStorage.setItem(key, Date.now().toString())
      setTimeout(() => onVerified(), 600)
    } catch (err) {
      setError(err.message)
      setOtp(['', '', '', '', '', ''])
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    } finally {
      setLoading(false)
    }
  }, [phoneNumber, room.slug, onVerified])

  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return
    const newOtp = [...otp]
    newOtp[index] = value.slice(-1)
    setOtp(newOtp)

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all digits are filled
    const fullCode = newOtp.join('')
    if (fullCode.length === 6) {
      handleVerify(fullCode)
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (!paste) return
    const newOtp = [...otp]
    paste.split('').forEach((ch, i) => { newOtp[i] = ch })
    setOtp(newOtp)
    if (paste.length === 6) {
      handleVerify(paste)
    } else {
      inputRefs.current[Math.min(paste.length, 5)]?.focus()
    }
  }

  const handleResend = async () => {
    setError('')
    setLoading(true)
    try {
      const data = await sendOTP(phoneNumber.trim(), room.slug)
      setDemoCode(data.otp_code || '')
      setCountdown(data.expires_in || 300)
      setOtp(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatCountdown = (s) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  if (step === 'verified') {
    return (
      <div className="otp-gate">
        <div className="otp-card otp-verified-card">
          <div className="otp-verified-icon">
            <ShieldCheck size={40} />
          </div>
          <h2>Verified!</h2>
          <p>Entering {room.name}…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="otp-gate">
      <div className="otp-card">
        <div className="otp-lock-icon">
          <Lock size={24} />
        </div>
        <h2>
          {step === 'phone' ? 'Protected Room' : 'Enter Verification Code'}
        </h2>
        <p className="otp-room-name">{room.name}</p>

        {step === 'phone' ? (
          <>
            <p className="otp-desc">
              This room requires phone number verification. Enter the registered phone number to receive a one-time code.
            </p>
            <form onSubmit={handleSendOTP} className="otp-phone-form">
              <div className="otp-input-group">
                <Phone size={18} className="otp-input-icon" />
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={e => setPhoneNumber(e.target.value)}
                  placeholder="+1234567890"
                  maxLength={20}
                  required
                  autoFocus
                  id="otp-phone-input"
                />
              </div>
              <button
                type="submit"
                className="otp-submit-btn"
                disabled={loading}
                id="otp-send-btn"
              >
                {loading ? (
                  <><Loader size={18} className="spin" /> Sending…</>
                ) : (
                  <><ArrowRight size={18} /> Send Code</>
                )}
              </button>
            </form>
          </>
        ) : (
          <>
            <p className="otp-desc">
              We sent a 6-digit code to <strong>{phoneNumber}</strong>
            </p>

            {demoCode && (
              <div className="otp-demo-banner">
                <ShieldCheck size={16} />
                <span>Demo code: <strong>{demoCode}</strong></span>
              </div>
            )}

            <div className="otp-digits" onPaste={handlePaste}>
              {otp.map((digit, i) => (
                <input
                  key={i}
                  ref={el => inputRefs.current[i] = el}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleOtpChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  className={`otp-digit ${digit ? 'filled' : ''}`}
                  id={`otp-digit-${i}`}
                  autoFocus={i === 0}
                />
              ))}
            </div>

            <div className="otp-meta">
              {countdown > 0 && (
                <span className="otp-countdown">
                  Expires in {formatCountdown(countdown)}
                </span>
              )}
              <button
                type="button"
                className="otp-resend-btn"
                onClick={handleResend}
                disabled={loading || countdown > 240}
                id="otp-resend-btn"
              >
                <RefreshCw size={14} /> Resend Code
              </button>
            </div>

            <button
              className="otp-back-btn"
              onClick={() => { setStep('phone'); setOtp(['','','','','','']); setError('') }}
              type="button"
            >
              ← Change number
            </button>
          </>
        )}

        {error && <p className="otp-error">{error}</p>}
      </div>
    </div>
  )
}
