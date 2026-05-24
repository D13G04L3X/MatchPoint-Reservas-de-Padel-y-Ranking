import { useState } from 'react'
import { cancelBooking, getBooking } from '../api/matchpoint'
import { userFacingError } from '../api/errors'
import { formatDateTime, formatStatus, formatYesNo } from '../utils/format'

function BookingCard({ booking, onCancel, cancelling }) {
  const isPending = booking.status === 'PENDING'

  return (
    <article className="booking-card">
      <div className="booking-card-head">
        <span className={`status-badge status-${booking.status.toLowerCase()}`}>
          {formatStatus(booking.status)}
        </span>
      </div>

      <dl className="booking-details">
        <dt>Reserva</dt>
        <dd className="mono">{booking.id}</dd>

        <dt>Cancha</dt>
        <dd className="mono">{booking.court_id}</dd>

        <dt>Jugador</dt>
        <dd className="mono">{booking.player_id}</dd>

        <dt>Inicio</dt>
        <dd>{formatDateTime(booking.start_time)}</dd>

        <dt>Fin</dt>
        <dd>{formatDateTime(booking.end_time)}</dd>

        <dt>Premium</dt>
        <dd>{formatYesNo(booking.is_premium)}</dd>

        <dt>Por ranking</dt>
        <dd>{formatYesNo(booking.is_ranked)}</dd>
      </dl>

      {isPending && (
        <div className="actions">
          <button type="button" className="danger" onClick={onCancel} disabled={cancelling}>
            {cancelling ? 'Cancelando…' : 'Cancelar reserva'}
          </button>
        </div>
      )}
    </article>
  )
}

export default function BookingDetail() {
  const [bookingId, setBookingId] = useState('')
  const [playerId, setPlayerId] = useState('')
  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function handleSearch(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setNotice('')
    setBooking(null)

    try {
      const data = await getBooking(bookingId.trim())
      setBooking(data)
    } catch (err) {
      setError(userFacingError(err.message))
    } finally {
      setLoading(false)
    }
  }

  async function handleCancel() {
    if (!booking) return
    if (!window.confirm('¿Quieres cancelar esta reserva?')) return

    setCancelling(true)
    setError('')
    setNotice('')

    try {
      const updated = await cancelBooking(booking.id, playerId.trim())
      setBooking(updated)
      setNotice(
        updated.status === 'CANCELLED_LATE'
          ? 'Reserva cancelada. Cancelaste con poco tiempo de anticipación.'
          : 'Reserva cancelada correctamente.',
      )
    } catch (err) {
      setError(userFacingError(err.message))
    } finally {
      setCancelling(false)
    }
  }

  return (
    <section className="panel">
      <h2>Mis reservas</h2>

      <form className="form" onSubmit={handleSearch}>
        <label>
          ID de reserva
          <input
            type="text"
            value={bookingId}
            onChange={(e) => setBookingId(e.target.value)}
            placeholder="Pega el ID de tu reserva"
            required
          />
        </label>

        <label>
          ID de jugador
          <input
            type="text"
            value={playerId}
            onChange={(e) => setPlayerId(e.target.value)}
            placeholder="Tu ID de jugador"
            required
          />
        </label>

        <div className="actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Buscando…' : 'Buscar reserva'}
          </button>
        </div>
      </form>

      {error && <p className="alert error">{error}</p>}
      {notice && <p className="alert success">{notice}</p>}

      {booking && (
        <BookingCard booking={booking} onCancel={handleCancel} cancelling={cancelling} />
      )}
    </section>
  )
}
