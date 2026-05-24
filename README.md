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

## Health Checks

```bash
curl http://localhost/health      # BookingManager
curl http://localhost:8082/health # Identity
curl http://localhost:8083/health # PenaltyRank
```

***

## Smoke Test

```bash
pip install httpx
python scripts/smoke_test.py
```

Para habilitar el test de reserva Ranked:

```bash
# 1. Seed de datos de ranking
docker compose exec ms-penalty-rank python scripts/seed_ranks.py

# 2. Exportar los IDs generados y correr el test
$env:RANK_HIGH_PLAYER_ID="<id-high>"
$env:RANK_LOW_PLAYER_ID="<id-low>"
python scripts/smoke_test.py
```

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
