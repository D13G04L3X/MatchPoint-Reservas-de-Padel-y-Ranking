import { useCallback, useEffect, useState } from 'react'
import { getRanking, getPlayers } from '../api/matchpoint'

export default function RankingList() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [playerMap, setPlayerMap] = useState({})

  useEffect(() => {
    getPlayers()
      .then((players) => {
        const map = {}
        for (const p of players) map[p.id] = p.username
        setPlayerMap(map)
      })
      .catch(() => {})
  }, [])

  const loadRanking = useCallback(() => {
    setLoading(true)
    setError('')
    return getRanking()
      .then((data) => setEntries(data.entries ?? []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadRanking()
  }, [loadRanking])

  return (
    <section className="panel panel-wide">
      <div className="panel-head">
        <h2>Ranking</h2>
        <button type="button" className="secondary" onClick={loadRanking} disabled={loading}>
          {loading ? 'Actualizando…' : 'Actualizar'}
        </button>
      </div>

      {loading && entries.length === 0 && <p className="hint">Cargando…</p>}
      {error && <p className="alert error">{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <p className="hint">Aún no hay jugadores en el ranking.</p>
      )}

      {entries.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Nivel</th>
                <th>Victorias</th>
                <th>Derrotas</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, index) => (
                <tr key={entry.player_id}>
                  <td>{index + 1}</td>
                  <td>{playerMap[entry.player_id] ?? entry.player_id}</td>
                  <td>{entry.level}</td>
                  <td>{entry.wins}</td>
                  <td>{entry.losses}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
