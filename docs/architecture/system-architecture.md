# Wasel Palestine Architecture Diagram

```mermaid
flowchart LR
    Client["API Clients\n(Web/Mobile/Admin Tools)"] --> API["FastAPI API Layer\n/api/v1 endpoints"]
    API --> Service["Service Layer\nBusiness rules & orchestration"]
    Service --> Repository["Repository Layer\nORM + selective raw SQL"]
    Repository --> DB[("PostgreSQL Database")]

    Service --> Auth["Security Components\nJWT + RBAC + Dependencies"]
    Service --> Cache["TTL Cache Service"]
    Service --> Audit["Audit Logging Service"]

    Service --> Routing["Routing Provider\n(OSRM/Nominatim via httpx)"]
    Service --> Weather["Weather Provider\n(OpenWeather via httpx)"]

    Service --> AlertFanout["Alert Fan-out\nSubscriptions -> Deliveries"]

    Audit --> DB
    Cache --> Service
    Auth --> API
    AlertFanout --> DB
```

## Layer Notes
- API routers stay thin and delegate all business decisions to services.
- Services enforce moderation, deduplication, verification, alert generation, and audit logging.
- Repository/database access remains isolated from endpoint code.
- External providers are accessed through integration clients with timeout, retry, throttle, and cache controls.
