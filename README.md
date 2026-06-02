# MatchPoint — Sistema de Reservas de Pádel

Plataforma de microservicios para gestión de reservas, ranking competitivo y penalizaciones por cancelación tardía.

***

## Arquitectura del Sistema

```
                        ┌─────────────────────────────────────────┐
                        │           Jugador (Cliente)             │
                        └──────────────────┬──────────────────────┘
                                           │ HTTP
                        ┌──────────────────▼──────────────────────┐
                        │         Nginx  (API Gateway)            │
                        │           http://localhost              │
                        └──┬───────────────┬─────────────────┬────┘
                           │               │                 │
               ┌───────────▼──────┐  ┌─────▼──────┐  ┌───────▼─────────┐
               │ MS-BookingManager│  │ MS-Identity│  │ MS-PenaltyRank  │
               │   (Core · REST)  │  │ (Síncrono) │  │  (Asíncrono)    │
               │   FastAPI        │  │  FastAPI   │  │  FastAPI        │
               │   :8081          │  │  :8082     │  │  :8083          │
               └────────┬─────────┘  └──────┬─────┘  └────────┬────────┘
                        │                   │                 │
               ┌────────▼──────┐   ┌────────▼──────┐   ┌──────▼────────┐
               │  PostgreSQL   │   │     MySQL     │   │   MongoDB     │
               │  (bookingdb)  │   │  (identitydb) │   │ (penaltyrank) │
               └───────────────┘   └───────────────┘   └───────────────┘
                        │                                         │
                        └───────────────────┬─────────────────────┘
                                            │
                        ┌───────────────────▼─────────────────────┐
                        │                RabbitMQ                 │
                        │      Eventos de cancelación tardía      │
                        └─────────────────────────────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────┐
               │                            │                        │
      ┌────────▼──────┐          ┌──────────▼────────┐      ┌────────▼───────┐
      │  Prometheus   │          │      Grafana      │      │     Jaeger     │
      │  :9090        │◄──────── │      :3000        │      │    :16686      │
      │  Métricas     │          │   Dashboards      │      │ Trazas distrib.│
      └───────────────┘          └───────────────────┘      └────────────────┘
```

***

## Reglas de Negocio

| # | Regla | Tipo | Servicio |
|---|-------|------|----------|
| 1 | Reserva Premium (18–22 h) requiere membresía activa | Síncrono | MS-Identity |
| 2 | Cancelación < 2 h genera penalización "Baja Confiabilidad" | Asíncrono | MS-PenaltyRank |
| 3 | Reserva Ranked rechazada si diferencia de nivel > 2.0 | Síncrono | MS-PenaltyRank |

***

## Requisitos

- Docker & Docker Compose
- Python 3.12 _(solo desarrollo local)_

***

## Despliegue

```bash
# 1. Configurar variables de entorno
cp .env.example .env

# 2. Levantar todos los servicios
docker compose up --build -d

# 3. Verificar estado
docker compose ps
```

***

## Servicios Disponibles

| Servicio | URL | Descripción |
|----------|-----|-------------|
| API Gateway | http://localhost | Punto único de entrada |
| MS-BookingManager | http://localhost/docs | Swagger — Core |
| MS-PenaltyRank | http://localhost/penalty/docs | Swagger — Ranking |
| RabbitMQ Management | http://localhost:15672 | Usuario: `matchpoint` |
| Jaeger UI | http://localhost:16686 | Trazas distribuidas |
| Grafana | http://localhost:3000 | Dashboards (`admin / admin`) |
| Prometheus | http://localhost:9090 | Métricas |

***

## Observabilidad

### Grafana — Dashboard MatchPoint

Tras levantar Docker Compose, abre Grafana en http://localhost:3000 (`admin` / valor de `GF_SECURITY_ADMIN_PASSWORD` en `.env`, por defecto `admin`).

El dashboard **MatchPoint - Observabilidad** se carga automáticamente desde `monitoring/grafana/dashboards/`. Incluye:

- Tasa de peticiones HTTP y latencia p95 por microservicio
- Errores 4xx / 5xx
- Métricas de negocio: reservas creadas, cancelaciones tardías, penalizaciones, fallos premium/ranked, validaciones de membresía

Para generar datos en el dashboard:

```bash
python scripts/smoke_test.py
```

### Jaeger — Trazas distribuidas

http://localhost:16686 — cada microservicio exporta trazas OpenTelemetry al iniciar.

### Prometheus — Scraping

Los tres MS exponen `/metrics`. Prometheus los scrapea según `monitoring/prometheus.yml`.

***

## Seeders (Auto-Seed al Arrancar)

Los tres microservicios siembran datos de prueba automáticamente al iniciar el contenedor. No hace falta ejecutar nada manual.

| Microservicio | Datos que siembra |
|---------------|-------------------|
| MS-Identity | 6 jugadores con membresías (`seed_players.py`) |
| MS-BookingManager | 3 canchas (`seed_courts.py`) |
| MS-PenaltyRank | Niveles de ranking para los 6 jugadores (`seed_ranks.py`) |

Los UUIDs son **deterministas** y coinciden con los valores por defecto del smoke test:

| Jugador | UUID | Nivel | Membresía |
|---------|------|-------|-----------|
| carlos_andrade | `258eddc0-881a-4a95-a89d-fb369d526ff3` | 5.0 | PREMIUM |
| ana_garcia | `365a0b54-0c23-4c4a-8c08-0bf13a23c202` | 4.5 | PREMIUM |
| pedro_ruiz | `7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d` | 4.8 | PREMIUM |
| laura_mendez | `5caea60a-3582-40ae-a9e0-d83def672f4d` | 3.0 | BASIC |
| mario_vega | `82d54dde-e2ff-4732-9e20-9d724fe47005` | 6.2 | EXPIRED |
| sofia_torres | `4dd9cff3-bb91-4b43-93c8-1b221a7669ab` | 4.0 | PREMIUM |

Si necesitas reseed manual (ej. tras limpiar la base):

```bash
docker compose exec ms-identity python scripts/seed_players.py
docker compose exec ms-penalty-rank python scripts/seed_ranks.py
```

### Smoke test

```bash
pip install httpx
python scripts/smoke_test.py
```

> Los UUIDs coinciden con los defaults del smoke test, así que no requiere variables de entorno.

***

## Variables de Entorno (`.env` raíz)

```env
# ── PostgreSQL ────────────────────────────────────────────────────
POSTGRES_USER=matchpoint
POSTGRES_PASSWORD=matchpoint
POSTGRES_DB=bookingdb
BOOKING_DATABASE_URL=postgresql+asyncpg://matchpoint:matchpoint@postgres:5432/bookingdb

# ── MySQL ─────────────────────────────────────────────────────────
MYSQL_USER=matchpoint
MYSQL_PASSWORD=matchpoint
MYSQL_ROOT_PASSWORD=matchpointroot
MYSQL_DATABASE=identitydb
IDENTITY_DATABASE_URL=mysql+aiomysql://matchpoint:matchpoint@mysql:3306/identitydb

# ── MongoDB ───────────────────────────────────────────────────────
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB=penaltyrank

# ── RabbitMQ ──────────────────────────────────────────────────────
RABBITMQ_DEFAULT_USER=matchpoint
RABBITMQ_DEFAULT_PASS=matchpoint
RABBITMQ_URL=amqp://matchpoint:matchpoint@rabbitmq:5672/

# ── Microservicios ────────────────────────────────────────────────
IDENTITY_SERVICE_URL=http://ms-identity:8082
PENALTY_SERVICE_URL=http://ms-penalty-rank:8083

# ── Observabilidad ────────────────────────────────────────────────
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
GF_SECURITY_ADMIN_PASSWORD=admin
```

***

## Estructura del Proyecto

```
matchpoint/
│
├── ms_booking_manager/         # Core — FastAPI + PostgreSQL
│   ├── domain/                 #   Entidades y puertos (Hexagonal)
│   ├── application/            #   Casos de uso
│   ├── infrastructure/         #   Adaptadores (DB, HTTP, MQ)
│   ├── scripts/
│   │   └── seed_courts.py
│   └── main.py
│
├── ms_identity/                # Síncrono — FastAPI + MySQL
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── main.py
│
├── ms_penalty_rank/            # Asíncrono — FastAPI + MongoDB
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── scripts/
│   │   └── seed_ranks.py
│   └── main.py
│
├── nginx/                      # API Gateway — nginx.conf
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── scripts/
│   └── smoke_test.py
│
├── docker-compose.yml
└── .env.example
```

***

## Decisiones Arquitectónicas

| Decisión | Justificación |
|----------|---------------|
| **REST síncrono** hacia MS-Identity y MS-PenaltyRank | Validaciones críticas previas a la reserva requieren respuesta inmediata |
| **RabbitMQ asíncrono** para cancelaciones tardías | No bloquea la respuesta al usuario; el evento se procesa en segundo plano |
| **Persistencia políglota** (PostgreSQL · MySQL · MongoDB) | PostgreSQL para transacciones, MySQL para identidad relacional simple, MongoDB para documentos de auditoría |
| **Arquitectura Hexagonal** por microservicio | Dominio sin dependencias de frameworks; facilita pruebas unitarias y sustitución de adaptadores |
