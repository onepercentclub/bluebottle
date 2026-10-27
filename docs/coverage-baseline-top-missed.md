# Coverage baseline (phase gate)

Generated for the coverage +25% plan. Re-run after each phase:

```bash
export DJANGO_SETTINGS_MODULE=bluebottle.settings.runner
coverage run --parallel-mode manage.py test --parallel 12 --keepdb \
  --settings bluebottle.settings.runner -v1
coverage combine
coverage report --skip-covered --sort=Miss | head -35
```

## Heuristic top missed modules (pre-implementation)

| Priority | Module | Rationale |
|----------|--------|-----------|
| P0 | `bluebottle/fsm/state.py` | Core state machine |
| P0 | `bluebottle/fsm/triggers.py` | Model change triggers |
| P0 | `bluebottle/fsm/effects.py` | Transition effects |
| P0 | `bluebottle/bluebottle_drf2/` | Global JSON:API layer |
| P1 | `bluebottle/activity_links/` | Mounted API + FSM |
| P1 | `bluebottle/geo/permissions.py`, `geo/views.py` | Office list gaps |
| P2 | `bluebottle/auth/password_validation.py` | Auth validators |
| P2 | `bluebottle/webfinger/client.py` | Federation discovery |
| P2 | `bluebottle/files/validators.py` | Upload validation |
| P3 | `bluebottle/utils/permissions.py` | Shared permissions |
| P3 | `bluebottle/activity_pub/adapters.py` | Federation HTTP |

Legacy packages omitted from denominator via `.coveragerc` (see README Testing section).
