# Wasel Palestine ERD (Core Tables)

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned_to
    USERS ||--o{ REFRESH_TOKENS : owns

    USERS ||--o{ INCIDENTS : creates
    USERS ||--o{ INCIDENTS : verifies
    USERS ||--o{ INCIDENTS : closes
    INCIDENT_CATEGORIES ||--o{ INCIDENTS : categorizes
    CHECKPOINTS ||--o{ INCIDENTS : references

    CHECKPOINTS ||--o{ CHECKPOINT_STATUS_HISTORY : tracks
    USERS ||--o{ CHECKPOINT_STATUS_HISTORY : updates

    INCIDENTS ||--o{ INCIDENT_VERIFICATION_EVENTS : has
    USERS ||--o{ INCIDENT_VERIFICATION_EVENTS : performs

    USERS ||--o{ REPORTS : submits
    INCIDENT_CATEGORIES ||--o{ REPORTS : categorizes
    CHECKPOINTS ||--o{ REPORTS : references
    REPORTS ||--o{ REPORT_VOTES : receives
    USERS ||--o{ REPORT_VOTES : casts
    REPORTS ||--o{ REPORT_MODERATION_ACTIONS : reviewed_by
    USERS ||--o{ REPORT_MODERATION_ACTIONS : performs

    USERS ||--o{ ALERT_SUBSCRIPTIONS : configures
    INCIDENT_CATEGORIES ||--o{ ALERT_SUBSCRIPTIONS : filters
    INCIDENTS ||--o{ ALERTS : triggers
    ALERTS ||--o{ ALERT_DELIVERIES : fans_out
    ALERT_SUBSCRIPTIONS ||--o{ ALERT_DELIVERIES : receives
    USERS ||--o{ ALERT_DELIVERIES : delivered_to

    USERS ||--o{ ROUTE_REQUESTS : requests
    USERS ||--o{ AUDIT_LOGS : acts_in
```

## Scope
- This ERD focuses on logical relationships needed for course deliverables.
- Exact field types and constraints remain source-of-truth in SQLAlchemy models and Alembic migration files.
