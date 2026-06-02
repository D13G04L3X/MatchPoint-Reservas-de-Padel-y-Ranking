import { useEffect, useState } from 'react'
import { getCourtAvailability } from '../api/matchpoint'
import { userFacingError } from '../api/errors'
import { formatTime, toDatetimeLocal } from '../utils/format'

function isPremiumSlot(startTime) {
  const hour = new Date(startTime).getHours()
  return hour >= 18 && hour < 23
}

export default function CourtAvailability({
  courtId,
  date,
  selectedStart,
  selectedEnd,
  refreshKey = 0,
  onSelectSlot,
  membershipExpired = false,
}) {
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(true)

  useEffect(() => {
    if (!courtId) {
      setSlots([])
      setError('')
      return
    }

    let cancelled = false

    async function loadSlots() {
      setLoading(true)
      setError('')

      try {
        const data = await getCourtAvailability(courtId, date)
        if (!cancelled) {
          setSlots(data.slots ?? [])
          setOpen(true)
        }
      } catch (err) {
        if (!cancelled) {
          setError(userFacingError(err.message))
          setSlots([])
          setOpen(true)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadSlots()

    return () => {
      cancelled = true
    }
  }, [courtId, date, refreshKey])

  useEffect(() => {
    if (slots.length === 0) return

    const matchesSelection = slots.some((slot) => {
      const start = toDatetimeLocal(new Date(slot.start_time))
      const end = toDatetimeLocal(new Date(slot.end_time))
      return start === selectedStart && end === selectedEnd
    })

    if (!matchesSelection) {
      const first = slots[0]
      onSelectSlot({
        startTime: toDatetimeLocal(new Date(first.start_time)),
        endTime: toDatetimeLocal(new Date(first.end_time)),
      })
    }
  }, [slots, selectedStart, selectedEnd, onSelectSlot])

  function handleSelect(slot) {
    onSelectSlot({
      startTime: toDatetimeLocal(new Date(slot.start_time)),
      endTime: toDatetimeLocal(new Date(slot.end_time)),
    })
  }

  function isSelected(slot) {
    if (!selectedStart || !selectedEnd) return false
    const start = toDatetimeLocal(new Date(slot.start_time))
    const end = toDatetimeLocal(new Date(slot.end_time))
    return start === selectedStart && end === selectedEnd
  }

  if (!courtId) {
    return null
  }

  return (
    <div className="availability">
      <div className="availability-head">
        <button
          type="button"
          className="availability-toggle"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
        >
          Horarios disponibles
          <span className="availability-chevron">{open ? '▲' : '▼'}</span>
        </button>
        {loading && <span className="hint">Consultando…</span>}
      </div>

      {open && (
        <div className="availability-body">
          {error && <p className="alert error">{error}</p>}

          {!loading && slots.length === 0 && !error && (
            <p className="hint">No hay horarios libres para esta cancha y fecha.</p>
          )}

          {slots.length > 0 && (
            <div className="slot-grid">
              {slots.map((slot) => {
                const key = `${slot.start_time}-${slot.end_time}`
                const premium = isPremiumSlot(slot.start_time)
                const disabled = premium && membershipExpired
                const classes = ['slot-btn']
                if (isSelected(slot)) classes.push('selected')
                if (premium) classes.push('premium')
                return (
                  <button
                    key={key}
                    type="button"
                    className={classes.join(' ')}
                    disabled={disabled}
                    onClick={() => handleSelect(slot)}
                  >
                    {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                  </button>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
