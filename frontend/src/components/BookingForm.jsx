import { useState } from 'react'
import { createBooking } from '../api/matchpoint'
import { userFacingError } from '../api/errors'
import { formatDateTime, formatStatus, formatYesNo } from '../utils/format'

function tomorrowAt(hour) {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  d.setHours(hour, 0, 0, 0)
  return d
}

function toDatetimeLocal(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function BookingForm() {
  const startDefault = tomorrowAt(10)
  const endDefault = tomorrowAt(11)

  const [courtId, setCourtId] = useState(() => crypto.randomUUID())
  const [playerId, setPlayerId] = useState(() => crypto.randomUUID())
  const [startTime, setStartTime] = useState(toDatetimeLocal(startDefault))
  const [endTime, setEndTime] = useState(toDatetimeLocal(endDefault))
  const [isRanked, setIsRanked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const booking = await createBooking({
        court_id: courtId,
        player_id: playerId,
        guest_player_ids: [],
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        is_ranked: isRanked,
      })
      setResult(booking)
    } catch (err) {
      setError(userFacingError(err.message))
    } finally {
      setLoading(false)
    }
  }

  function setPremiumPreset() {
    setStartTime(toDatetimeLocal(tomorrowAt(19)))
    setEndTime(toDatetimeLocal(tomorrowAt(20)))
  }

  return (
    <section className="panel">
      <h2>Nueva reserva</h2>
      <p className="hint">
        Horario premium: 6:00 p.m. – 10:00 p.m. Recuerda tener una membresía activa.
      </p>

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Cancha (UUID)
          <div className="row">
            <input value={courtId} onChange={(e) => setCourtId(e.target.value)} required />
            <button type="button" className="secondary" onClick={() => setCourtId(crypto.randomUUID())}>
              Nuevo
            </button>
          </div>
        </label>

        <label>
          Jugador (UUID)
          <div className="row">
            <input value={playerId} onChange={(e) => setPlayerId(e.target.value)} required />
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
          <button type="submit" disabled={loading}>
            {loading ? 'Reservando…' : 'Crear reserva'}
          </button>
        </div>
      </form>

      {error && <p className="alert error">{error}</p>}

      {result && (
        <div className="alert success">
          <strong>Reserva creada</strong>
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
