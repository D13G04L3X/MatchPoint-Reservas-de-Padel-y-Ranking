import { useCallback, useEffect, useState } from 'react'
import { cancelBooking, getCourts, listBookingsByDate } from '../api/matchpoint'
import { userFacingError } from '../api/errors'
import {
  buildCourtNameMap,
  formatCourtName,
  formatDateTime,
  formatStatus,
  formatTimeRange,
  formatYesNo,
  toDateInputValue,
} from '../utils/format'
import { loadSession, saveSession } from '../utils/session'

function tomorrowDate() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d
}

function BookingCard({ booking, courtNames, onCancel, cancelling }) {
  const isPending = booking.status === 'PENDING'

  return (
    <article className="booking-card">
      <div className="booking-card-head">
        <span className={`status-badge status-${booking.status.toLowerCase()}`}>
          {formatStatus(booking.status)}
        </span>
      </div>

      <dl className="booking-details">
        <dt>ID de reserva</dt>
        <dd className="mono">{booking.id}</dd>

        <dt>Cancha</dt>
        <dd>{formatCourtName(booking.court_id, courtNames)}</dd>

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
  const session = loadSession()
  const [selectedDate, setSelectedDate] = useState(
    () => session.lastBookingDate ?? toDateInputValue(tomorrowDate()),
  )
  const [includeCancelled, setIncludeCancelled] = useState(false)
  const [courtNames, setCourtNames] = useState({})
  const [bookings, setBookings] = useState([])
  const [selectedId, setSelectedId] = useState(session.lastBookingId ?? '')
  const [loading, setLoading] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const selectedBooking = bookings.find((item) => item.id === selectedId) ?? null

  useEffect(() => {
    getCourts()
      .then((courts) => setCourtNames(buildCourtNameMap(courts)))
      .catch(() => {})
  }, [])

  const loadBookings = useCallback(async () => {
    setLoading(true)
    setError('')
    setNotice('')

    try {
      const data = await listBookingsByDate(selectedDate, { includeCancelled })
      const nextBookings = Array.isArray(data) ? data : []
      setBookings(nextBookings)

      setSelectedId((current) => {
        if (nextBookings.some((item) => item.id === current)) {
          return current
        }
        const saved = loadSession().lastBookingId
        if (saved && nextBookings.some((item) => item.id === saved)) {
          return saved
        }
        return nextBookings[0]?.id ?? ''
      })
    } catch (err) {
      setBookings([])
      setSelectedId('')
      setError(userFacingError(err.message))
    } finally {
      setLoading(false)
    }
  }, [selectedDate, includeCancelled])

  useEffect(() => {
    loadBookings()
  }, [loadBookings])

  useEffect(() => {
    if (selectedBooking) {
      saveSession({ lastBookingId: selectedBooking.id })
    }
  }, [selectedBooking])

  async function handleCancel() {
    if (!selectedBooking) return
    if (!window.confirm('¿Quieres cancelar esta reserva?')) return

    setCancelling(true)
    setError('')
    setNotice('')

    try {
      const updated = await cancelBooking(selectedBooking.id, selectedBooking.player_id)
      setBookings((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
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
      <h2>Reservas del día</h2>
      <p className="hint">
        Todas las reservas activas de la fecha elegida. Las canceladas no ocupan horario en la
        cancha.
      </p>

      <div className="form">
        <label>
          Fecha
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </label>

        <label className="checkbox">
          <input
            type="checkbox"
            checked={includeCancelled}
            onChange={(e) => setIncludeCancelled(e.target.checked)}
          />
          Incluir canceladas
        </label>
      </div>

      {loading && <p className="hint">Cargando reservas…</p>}
      {error && <p className="alert error">{error}</p>}
      {notice && <p className="alert success">{notice}</p>}

      {!loading && !error && bookings.length === 0 && (
        <p className="hint">No hay reservas para esta fecha.</p>
      )}

      {bookings.length > 0 && (
        <div className="booking-list">
          <strong>Reservas del día</strong>
          <ul className="booking-checklist">
            {bookings.map((item) => {
              const isSelected = item.id === selectedId
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={isSelected ? 'booking-item selected' : 'booking-item'}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <span className="booking-item-time">
                      {formatTimeRange(item.start_time, item.end_time)}
                    </span>
                    <span className="booking-item-court">
                      Cancha: {formatCourtName(item.court_id, courtNames)}
                    </span>
                    <span className={`status-badge status-${item.status.toLowerCase()}`}>
                      {formatStatus(item.status)}
                    </span>
                    <span className="booking-item-player">
                      Jugador: <span className="mono">{item.player_id}</span>
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {selectedBooking && (
        <BookingCard
          booking={selectedBooking}
          courtNames={courtNames}
          onCancel={handleCancel}
          cancelling={cancelling}
        />
      )}
    </section>
  )
}