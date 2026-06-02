import { useCallback, useEffect, useState } from 'react'
import {
  createBooking,
  getCourtsAvailability,
  getPlayerRank,
  getPlayerBookings,
  getPlayerPenalties,
} from '../api/matchpoint'
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

const MEMBERSHIP_LABELS = {
  ACTIVE: 'Activa',
  EXPIRED: 'Vencida',
  SUSPENDED: 'Suspendida',
}

export default function BookingForm({ players, activeUserId, onViewBooking }) {
  const session = loadSession()
  const startDefault = tomorrowAt(10)
  const endDefault = tomorrowAt(11)
  const dateDefault = tomorrowAt(0)

  const [courtId, setCourtId] = useState(() => session.courtId ?? '')
  const [availabilityDate, setAvailabilityDate] = useState(toDateInputValue(dateDefault))
  const [courts, setCourts] = useState([])
  const [courtsLoading, setCourtsLoading] = useState(false)
  const [courtsError, setCourtsError] = useState('')
  const [startTime, setStartTime] = useState(toDatetimeLocal(startDefault))
  const [endTime, setEndTime] = useState(toDatetimeLocal(endDefault))
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [slotsRefresh, setSlotsRefresh] = useState(0)

  const [localPartnerId, setLocalPartnerId] = useState('')
  const [visitPlayer1Id, setVisitPlayer1Id] = useState('')
  const [visitPlayer2Id, setVisitPlayer2Id] = useState('')
  const [matchType, setMatchType] = useState('CASUAL')

  const [organizerLevel, setOrganizerLevel] = useState(null)
  const [organizerBookings, setOrganizerBookings] = useState(null)
  const [organizerPenalties, setOrganizerPenalties] = useState([])
  const [organizerInfoLoading, setOrganizerInfoLoading] = useState(false)

  const [playerLevels, setPlayerLevels] = useState({})
  const [levelDiffError, setLevelDiffError] = useState('')

  useEffect(() => {
    saveSession({ playerId: activeUserId })
  }, [activeUserId])

  useEffect(() => {
    if (!activeUserId) return
    setOrganizerInfoLoading(true)
    setOrganizerLevel(null)
    setOrganizerBookings(null)
    setOrganizerPenalties([])
    Promise.all([
      getPlayerRank(activeUserId).catch(() => null),
      getPlayerBookings(activeUserId).catch(() => null),
      getPlayerPenalties(activeUserId).catch(() => []),
    ])
      .then(([rank, bookings, penalties]) => {
        setOrganizerLevel(rank?.level ?? null)
        setOrganizerBookings(bookings)
        setOrganizerPenalties(penalties)
      })
      .finally(() => setOrganizerInfoLoading(false))
  }, [activeUserId])

  useEffect(() => {
    if (matchType !== 'RANKED') {
      setLevelDiffError('')
      return
    }
    const ids = [activeUserId, localPartnerId, visitPlayer1Id, visitPlayer2Id].filter(Boolean)
    if (ids.length < 4) {
      setLevelDiffError('')
      return
    }
    const missing = ids.filter((id) => !(id in playerLevels))
    if (missing.length > 0) {
      Promise.all(
        missing.map((id) =>
          getPlayerRank(id)
            .then((r) => ({ id, level: r.level }))
            .catch(() => null),
        ),
      ).then((results) => {
        const updates = {}
        for (const r of results) {
          if (r) updates[r.id] = r.level
        }
        setPlayerLevels((prev) => ({ ...prev, ...updates }))
      })
      return
    }
    const levels = ids.map((id) => playerLevels[id])
    const min = Math.min(...levels)
    const max = Math.max(...levels)
    if (max - min > 2.0) {
      setLevelDiffError(`Diferencia de nivel (${(max - min).toFixed(1)}) supera 2.0. No se puede crear partido ranking.`)
    } else {
      setLevelDiffError('')
    }
  }, [matchType, activeUserId, localPartnerId, visitPlayer1Id, visitPlayer2Id, playerLevels])

  useEffect(() => {
    saveSession({ courtId, playerId: activeUserId })
  }, [courtId, activeUserId])

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

  const isRanked = matchType === 'RANKED'
  const submitDisabled = loading || !courtId || (isRanked && !!levelDiffError)

  const partnerOptions = players.filter((p) => p.id !== activeUserId)
  const visitOptions = players.filter(
    (p) => p.id !== activeUserId && p.id !== localPartnerId,
  )
  const visit2Options = players.filter(
    (p) => p.id !== activeUserId && p.id !== localPartnerId && p.id !== visitPlayer1Id,
  )

  const activePlayer = players.find((p) => p.id === activeUserId)
  const organizerName = activePlayer?.username ?? activeUserId
  const membershipStatus = activePlayer?.membership_status ?? ''
  const restrictionActive = activePlayer?.restriction_active ?? false
  const restrictionUntil = activePlayer?.restriction_until ?? null

  let penaltyDaysRemaining = null
  if (restrictionActive && restrictionUntil) {
    const now = new Date()
    const until = new Date(restrictionUntil)
    const diffMs = until - now
    if (diffMs > 0) {
      penaltyDaysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
    }
  }

  const totalBookings = Array.isArray(organizerBookings) ? organizerBookings.length : null
  const completedBookings = Array.isArray(organizerBookings)
    ? organizerBookings.filter((b) => b.status !== 'CANCELLED_EARLY' && b.status !== 'CANCELLED_LATE').length
    : null
  const attendancePct = totalBookings > 0 ? Math.round((completedBookings / totalBookings) * 100) : null

  async function handleSubmit(event) {
    event.preventDefault()
    if (!courtId) {
      setError('Elige una cancha con horarios disponibles.')
      return
    }
    if (isRanked && levelDiffError) {
      setError(levelDiffError)
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    setCopied(false)

    try {
      const teamLocalIds = [activeUserId, localPartnerId]
      let teamVisitIds = null
      if (isRanked) {
        teamVisitIds = [visitPlayer1Id, visitPlayer2Id]
      }
      const booking = await createBooking(
        {
          court_id: courtId,
          player_id: activeUserId,
          team_local_ids: teamLocalIds,
          team_visit_ids: teamVisitIds,
          start_time: new Date(startTime).toISOString(),
          end_time: new Date(endTime).toISOString(),
          is_ranked: isRanked,
        },
        activeUserId,
      )
      setResult(booking)
      saveSession({
        courtId,
        playerId: activeUserId,
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

  function membershipBadgeClass(status) {
    if (status === 'ACTIVE') return 'badge badge-active'
    if (status === 'EXPIRED') return 'badge badge-expired'
    if (status === 'SUSPENDED') return 'badge badge-suspended'
    return 'badge badge-unknown'
  }

  function reliabilityBadgeClass(restricted) {
    return restricted ? 'badge badge-low' : 'badge badge-high'
  }

  return (
    <section className="panel">
      <h2>Nueva reserva</h2>
      <p className="hint">
        Horario premium: 6:00 p.m. – 10:00 p.m. Recuerda tener una membresía activa.
      </p>

      {activeUserId && (
        <div className="organizer-card">
          <div className="organizer-card-head">
            <strong>{organizerName}</strong>
            {organizerInfoLoading && <span className="hint">Cargando info…</span>}
          </div>
          <div className="organizer-card-body">
            <div className="organizer-field">
              <span className="organizer-label">Membresía</span>
              <span className={membershipBadgeClass(membershipStatus)}>
                {MEMBERSHIP_LABELS[membershipStatus] ?? membershipStatus}
              </span>
            </div>
            <div className="organizer-field">
              <span className="organizer-label">Confiabilidad</span>
              <span className={reliabilityBadgeClass(restrictionActive)}>
                {restrictionActive ? 'Baja' : 'Alta'}
              </span>
            </div>
            <div className="organizer-field">
              <span className="organizer-label">Nivel</span>
              <span>{organizerLevel != null ? organizerLevel.toFixed(1) : '—'}</span>
            </div>
            <div className="organizer-field">
              <span className="organizer-label">Reservas</span>
              <span>{totalBookings != null ? totalBookings : '—'}</span>
            </div>
            <div className="organizer-field">
              <span className="organizer-label">Asistencia</span>
              <span>{attendancePct != null ? `${attendancePct}%` : '—'}</span>
            </div>
            {penaltyDaysRemaining != null && (
              <div className="organizer-field organizer-penalty">
                <span className="organizer-label">Penalización</span>
                <span>
                  {penaltyDaysRemaining > 0
                    ? `${penaltyDaysRemaining} día(s) restante(s)`
                    : 'Hoy vence'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Fecha
          <input
            type="date"
            value={availabilityDate}
            min={toDateInputValue(new Date())}
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
          membershipExpired={membershipStatus === 'EXPIRED'}
        />

        <p className="hint inline">
          Elige un horario de la grilla. Los cancelados no bloquean cupos; solo las reservas
          activas ocupan la cancha.
        </p>

        <label>
          Organizador
          <input type="text" value={organizerName} readOnly disabled />
        </label>

        <label>
          Inicio
          <input type="datetime-local" value={startTime} disabled required />
        </label>

        <label>
          Fin
          <input type="datetime-local" value={endTime} disabled required />
        </label>

        <label>
          Tipo de partido
          <select value={matchType} onChange={(e) => setMatchType(e.target.value)}>
            <option value="CASUAL">Casual</option>
            <option value="RANKED">Ranking</option>
          </select>
        </label>

        <label>
          Compañero equipo local
          {partnerOptions.length > 0 ? (
            <select
              value={localPartnerId}
              onChange={(e) => setLocalPartnerId(e.target.value)}
              required
            >
              <option value="">Selecciona un jugador</option>
              {partnerOptions.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.username}
                </option>
              ))}
            </select>
          ) : (
            <input type="text" readOnly disabled value="No hay jugadores disponibles" />
          )}
          <span className="hint inline">
            El organizador siempre pertenece al equipo local.
          </span>
        </label>

        {isRanked && (
          <>
            <label>
              Jugador visita 1
              {visitOptions.length > 0 ? (
                <select
                  value={visitPlayer1Id}
                  onChange={(e) => setVisitPlayer1Id(e.target.value)}
                  required
                >
                  <option value="">Selecciona un jugador</option>
                  {visitOptions.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.username}
                    </option>
                  ))}
                </select>
              ) : (
                <input type="text" readOnly disabled value="No hay jugadores disponibles" />
              )}
            </label>
            <label>
              Jugador visita 2
              {visit2Options.length > 0 ? (
                <select
                  value={visitPlayer2Id}
                  onChange={(e) => setVisitPlayer2Id(e.target.value)}
                  required
                >
                  <option value="">Selecciona un jugador</option>
                  {visit2Options.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.username}
                    </option>
                  ))}
                </select>
              ) : (
                <input type="text" readOnly disabled value="No hay jugadores disponibles" />
              )}
            </label>
          </>
        )}

        {levelDiffError && (
          <p className="alert error">{levelDiffError}</p>
        )}

        <div className="actions">
          <button type="submit" disabled={submitDisabled}>
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
