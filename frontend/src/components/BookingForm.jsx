import { useCallback, useEffect, useState } from 'react'
import { createBooking, getCourtsAvailability } from '../api/matchpoint'
import { userFacingError } from '../api/errors'
import CourtAvailability from './CourtAvailability'
import {
  formatDateTime,
  formatStatus,
  formatYesNo,
  shiftDatetimeLocalToDate,
  toDateInputValue,
  toDatetimeLocal,
} from '../utils/format'
import { loadSession, saveSession } from '../utils/session'

function tomorrowAt(hour) {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  d.setHours(hour, 0, 0, 0)
  return d
}

function parseGuestIds(raw) {
  return raw
    .split(',')
    .map((id) => id.trim())
    .filter(Boolean)
}

function normalizeGuestIds(raw, mainPlayerId) {
  const seen = new Set()
  const ids = []

  for (const id of parseGuestIds(raw)) {
    if (id === mainPlayerId.trim()) continue
    if (seen.has(id)) continue
    seen.add(id)
    ids.push(id)
  }

  return ids
}

export default function BookingForm({ onViewBooking }) {
  const session = loadSession()
  const startDefault = tomorrowAt(10)
  const endDefault = tomorrowAt(11)
  const dateDefault = tomorrowAt(0)

  const [courtId, setCourtId] = useState(() => session.courtId ?? '')
  const [playerId, setPlayerId] = useState(() => session.playerId ?? crypto.randomUUID())
  const [availabilityDate, setAvailabilityDate] = useState(toDateInputValue(dateDefault))
  const [courts, setCourts] = useState([])
  const [courtsLoading, setCourtsLoading] = useState(false)
  const [courtsError, setCourtsError] = useState('')
  const [startTime, setStartTime] = useState(toDatetimeLocal(startDefault))
  const [endTime, setEndTime] = useState(toDatetimeLocal(endDefault))
  const [guestIdsRaw, setGuestIdsRaw] = useState('')
  const [isRanked, setIsRanked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [slotsRefresh, setSlotsRefresh] = useState(0)

  useEffect(() => {
    saveSession({ courtId, playerId })
  }, [courtId, playerId])

  useEffect(() => {
    setStartTime((current) => shiftDatetimeLocalToDate(current, availabilityDate))
    setEndTime((current) => shiftDatetimeLocalToDate(current, availabilityDate))
  }, [availabilityDate])

  const loadCourts = useCallback(async ({ preserveSelection = false } = {}) => {
    setCourtsLoading(true)
    setCourtsError('')

    if (!preserveSelection) {
      setCourtId('')
    }

    try {
      const data = await getCourtsAvailability(availabilityDate)
      const nextCourts = data.courts ?? []
      setCourts(nextCourts)

      if (nextCourts.length === 0) {
        setCourtId('')
        return
      }

      setCourtId((current) => {
        if (preserveSelection && nextCourts.some((court) => court.id === current)) {
          return current
        }
        const savedCourt = loadSession().courtId
        if (nextCourts.some((court) => court.id === savedCourt)) {
          return savedCourt
        }
        return nextCourts[0].id
      })
    } catch (err) {
      setCourts([])
      setCourtId('')
      setCourtsError(userFacingError(err.message))
    } finally {
      setCourtsLoading(false)
    }
  }, [availabilityDate])

  useEffect(() => {
    loadCourts()
  }, [loadCourts])

  async function handleSubmit(event) {
    event.preventDefault()

    if (!courtId) {
      setError('Elige una cancha con horarios disponibles.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    setCopied(false)

    try {
      const guestPlayerIds = normalizeGuestIds(guestIdsRaw, playerId)

      if (isRanked && guestPlayerIds.length > 3) {
        setError('Máximo 3 compañeros por reserva (sin contar al jugador principal).')
        return
      }

      const booking = await createBooking({
        court_id: courtId,
        player_id: playerId,
        guest_player_ids: guestPlayerIds,
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        is_ranked: isRanked,
      })
      setResult(booking)
      saveSession({
        courtId,
        playerId,
        lastBookingId: booking.id,
        lastBookingDate: availabilityDate,
      })
      await loadCourts({ preserveSelection: true })
      setSlotsRefresh((value) => value + 1)
    } catch (err) {
      setError(userFacingError(err.message))
    } finally {
      setLoading(false)
    }
  }

  function setPremiumPreset() {
    const day = tomorrowAt(0)
    setAvailabilityDate(toDateInputValue(day))
    setStartTime(toDatetimeLocal(tomorrowAt(19)))
    setEndTime(toDatetimeLocal(tomorrowAt(20)))
  }

  function handleSlotSelect({ startTime: start, endTime: end }) {
    setStartTime(start)
    setEndTime(end)
  }

  async function copyBookingId() {
    if (!result?.id) return
    await navigator.clipboard.writeText(result.id)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section className="panel">
      <h2>Nueva reserva</h2>
      <p className="hint">
        Horario premium: 6:00 p.m. – 10:00 p.m. Recuerda tener una membresía activa.
      </p>

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Fecha
          <input
            type="date"
            value={availabilityDate}
            onChange={(e) => setAvailabilityDate(e.target.value)}
            required
          />
        </label>

        <div className="court-picker">
          <div className="court-picker-head">
            <strong>Canchas</strong>
            {courtsLoading && <span className="hint">Buscando disponibilidad…</span>}
          </div>

          {courtsError && <p className="alert error">{courtsError}</p>}

          {!courtsLoading && courts.length === 0 && !courtsError && (
            <p className="hint">Ninguna cancha tiene horarios libres para esta fecha.</p>
          )}
          {courts.length > 0 && (
            <div className="court-grid">
              {courts.map((court) => {
                const isSelected = court.id === courtId
                return (
                  <button
                    key={court.id}
                    type="button"
                    className={isSelected ? 'court-btn selected' : 'court-btn'}
                    onClick={() => setCourtId(court.id)}
                  >
                    <span className="court-btn-name">{court.name}</span>
                    <span className="court-btn-meta">{court.description}</span>
                    <span className="court-btn-slots">
                      {court.available_slots} horario(s) libre(s)
                    </span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <CourtAvailability
          courtId={courtId}
          date={availabilityDate}
          selectedStart={startTime}
          selectedEnd={endTime}
          refreshKey={slotsRefresh}
          onSelectSlot={handleSlotSelect}
        />

        <p className="hint inline">
          Elige un horario de la grilla. Los cancelados no bloquean cupos; solo las reservas
          activas ocupan la cancha.
        </p>

        <label>
          Jugador
          <div className="row">
            <input
              type="text"
              value={playerId}
              onChange={(e) => setPlayerId(e.target.value)}
              required
            />
            <button type="button" className="secondary" onClick={() => setPlayerId(crypto.randomUUID())}>
              Nuevo
            </button>
          </div>
        </label>

        <label>
          Inicio
          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </label>

        <label>
          Fin
          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
          />
        </label>

        {isRanked && (
          <label>
            Compañeros
            <input
              type="text"
              value={guestIdsRaw}
              onChange={(e) => setGuestIdsRaw(e.target.value)}
              placeholder="IDs separados por coma"
            />
            <span className="hint inline">
              Hasta 3 compañeros. No incluyas tu propio ID de jugador.
            </span>
          </label>
        )}

        <label className="checkbox">
          <input
            type="checkbox"
            checked={isRanked}
            onChange={(e) => setIsRanked(e.target.checked)}
          />
          Partido por ranking
        </label>

        <div className="actions">
          <button type="button" className="secondary" onClick={setPremiumPreset}>
            Horario premium (7:00 p.m.)
          </button>
          <button type="submit" disabled={loading || !courtId}>
            {loading ? 'Reservando…' : 'Crear reserva'}
          </button>
        </div>
      </form>

      {error && <p className="alert error">{error}</p>}

      {result && (
        <div className="alert success">
          <div className="success-head">
            <strong>Reserva creada</strong>
            <div className="actions compact">
              <button type="button" className="secondary" onClick={copyBookingId}>
                {copied ? 'Copiado' : 'Copiar ID'}
              </button>
              {onViewBooking && (
                <button type="button" className="secondary" onClick={onViewBooking}>
                  Ver reserva
                </button>
              )}
            </div>
          </div>
          <dl className="booking-details compact">
            <dt>ID de reserva</dt>
            <dd className="mono">{result.id}</dd>
            <dt>Estado</dt>
            <dd>{formatStatus(result.status)}</dd>
            <dt>Inicio</dt>
            <dd>{formatDateTime(result.start_time)}</dd>
            <dt>Fin</dt>
            <dd>{formatDateTime(result.end_time)}</dd>
            <dt>Premium</dt>
            <dd>{formatYesNo(result.is_premium)}</dd>
            <dt>Por ranking</dt>
            <dd>{formatYesNo(result.is_ranked)}</dd>
          </dl>
        </div>
      )}
    </section>
  )
}