# Observabilidad MatchPoint — Grafana + Prometheus

Este documento explica qué se corrigió para que el dashboard de Grafana funcione en Docker y cómo encaja con Prometheus y Jaeger.

---

## Problema inicial

1. **Grafana no mostraba el dashboard** — al entrar en http://localhost:3000 la carpeta de dashboards aparecía vacía.
2. **Aviso de contraseña por defecto** — Grafana alertaba por usar `admin` / `admin`.
3. **Falta de evidencia en la sustentación** — Prometheus recibía métricas, pero no había un panel provisionado visible para HTTP, negocio y trazabilidad.

---

## Arquitectura de observabilidad

```
┌─────────────┐     scrape /metrics      ┌─────────────┐     PromQL      ┌─────────────┐
│ MS-Booking  │ ────────────────────────► │ Prometheus  │ ─────────────► │   Grafana   │
│ MS-Identity │      cada 15s            │   :9090     │                │   :3000     │
│ MS-Penalty  │                          └─────────────┘                └─────────────┘
└─────────────┘
       │
       │ OpenTelemetry (OTLP)
       ▼
┌─────────────┐
│   Jaeger    │  ← Trazas distribuidas (no métricas): http://localhost:16686
└─────────────┘
```

| Herramienta | Rol |
|-------------|-----|
| **Prometheus** | Recolecta y almacena métricas numéricas (contadores, histogramas). |
| **Grafana** | Visualiza métricas con queries PromQL en dashboards. |
| **Jaeger** | Trazabilidad: seguir una petición entre microservicios. |

---

## Qué métricas expone cada microservicio

Cada MS monta `GET /metrics` y un middleware HTTP (`infrastructure/observability/metrics.py`).

### HTTP (los tres MS)

| Métrica | Tipo | Uso en dashboard |
|---------|------|------------------|
| `http_requests_total` | Counter | Tasa de peticiones, errores 4xx/5xx |
| `http_request_duration_seconds` | Histogram | Latencia p95 |

### Negocio — MS-BookingManager

| Métrica | Cuándo incrementa |
|---------|-------------------|
| `bookings_created_total` | Reserva creada con éxito |
| `bookings_cancelled_late_total` | Cancelación con menos de 2 h de anticipación |
| `premium_validation_failures_total` | Premium sin membresía o con restricción |
| `ranked_validation_failures_total` | Diferencia de nivel > 2.0 |

### Negocio — MS-PenaltyRank

| Métrica | Cuándo incrementa |
|---------|-------------------|
| `penalties_applied_total` | Consumer aplica penalización por cancelación tardía |

### Negocio — MS-Identity

| Métrica | Cuándo incrementa |
|---------|-------------------|
| `membership_validations_total` | Validación de membresía |
| `restriction_checks_total` | Consulta de restricción del jugador |

---

## Cambios realizados (por archivo)

### 1. `monitoring/grafana/provisioning/dashboards/dashboards.yml`

**Antes (incorrecto):**
```yaml
dashboards:    # ← clave inválida en Grafana 10
  - name: matchpoint-dashboards
```

**Después (correcto):**
```yaml
providers:       # ← clave que Grafana 10 espera
  - name: matchpoint-dashboards
    folder: MatchPoint
    options:
      path: /var/lib/grafana/dashboards
```

**Por qué:** Grafana 10 solo provisiona dashboards desde archivos JSON si la configuración usa `providers`, no `dashboards`. Por eso el JSON existía pero nunca aparecía en la UI.

---

### 2. `monitoring/grafana/provisioning/datasources/datasources.yml`

Se añadieron **UID fijos** para los datasources:

| Nombre | UID | URL interna Docker |
|--------|-----|-------------------|
| Prometheus | `prometheus` | `http://prometheus:9090` |
| Jaeger | `jaeger` | `http://jaeger:16686` |

**Por qué:** Los paneles del dashboard deben referenciar el datasource por `uid`. Sin UID estable, Grafana no resuelve las queries tras el provisioning.

---

### 3. `monitoring/grafana/dashboards/matchpoint-overview.json`

- Todas las referencias `"datasource": "Prometheus"` se cambiaron a:
  ```json
  "datasource": { "type": "prometheus", "uid": "prometheus" }
  ```
- Se añadieron paneles:
  - **Targets Prometheus** — `up{job=~"ms-.*"}` (salud del scrape).
  - **MS-Identity — actividad** — tasas de validación y restricción.
  - **Guía Jaeger** — texto con enlace a la UI de trazas.

**Queries principales del dashboard:**

```promql
# Tasa HTTP por microservicio
sum(rate(http_requests_total[5m])) by (job)

# Latencia p95
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))

# Contadores de negocio
bookings_created_total{job="ms-booking-manager"}
penalties_applied_total{job="ms-penalty-rank"}
membership_validations_total{job="ms-identity"}
```

---

### 4. `monitoring/prometheus.yml` (sin cambios — ya estaba bien)

Prometheus scrapea cada 15 s:

| Job | Target |
|-----|--------|
| `ms-booking-manager` | `ms-booking-manager:8081/metrics` |
| `ms-identity` | `ms-identity:8082/metrics` |
| `ms-penalty-rank` | `ms-penalty-rank:8083/metrics` |

---

### 5. Contraseña Grafana (`.env` — no se sube a Git)

- `.env` está en `.gitignore`.
- Se cambió `GF_SECURITY_ADMIN_PASSWORD` de `admin` a una contraseña segura.
- `.env.example` documenta la variable sin exponer la clave real del equipo.

---

## Cómo levantar y verificar

```bash
docker compose up -d
python scripts/smoke_test.py
```

| URL | Credenciales / notas |
|-----|----------------------|
| http://localhost:3000 | `admin` + contraseña del `.env` |
| Dashboard | **Dashboards → MatchPoint → MatchPoint - Observabilidad** |
| http://localhost:9090/targets | Los 3 jobs deben estar **UP** |
| http://localhost:16686 | Jaeger — trazas por servicio |

---

## Cómo explicarlo en la sustentación (30 s)

> *"Cada microservicio expone métricas Prometheus en `/metrics`. Un middleware registra cada petición HTTP y los casos de uso incrementan métricas de negocio. Prometheus hace scrape cada 15 segundos; Grafana, provisionado por archivos en `monitoring/grafana`, ejecuta queries PromQL y muestra el dashboard. Para trazabilidad, OpenTelemetry envía spans a Jaeger, donde vemos el flujo entre Booking, Identity y PenaltyRank."*

---

## Docker Compose — volúmenes relevantes

```yaml
grafana:
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
```

Tras cambiar provisioning o el JSON del dashboard:

```bash
docker compose up -d --force-recreate grafana
```
