# bluebottle

Multi-tenant Django platform (GoodUp). Tenants are Postgres schemas via
`tenant_schemas`; activity search runs on Elasticsearch.

## Code style

@docs/CODE_STYLE.md

## Running tests

```bash
python manage.py test <path> --settings=bluebottle.settings.local --keepdb
```

Always pass `--keepdb`. Without it every run rebuilds all tenant schemas, which
takes about 25 minutes. `bluebottle/settings/local.py` connects to the local
`reef` database over the unix socket and sets `KEEPDB = True`.

Suites worth knowing: `bluebottle.time_based` is the largest (~1000 tests,
~13 min). `bluebottle.activities`, `bluebottle.deeds` and `bluebottle.collect`
together are ~435 tests, ~7 min. Don't run two suites concurrently — they share
one test database.

Note `bluebottle/settings/testing.py` calls `logging.disable(logging.CRITICAL)`,
so any assertion about log output passes vacuously unless the test re-enables
logging for its duration.

## Working a Jira ticket

Project BB on onepercentclub.atlassian.net.

- Branch `ticket/BB-xxxxx-short-description`, one per ticket.
- Move the ticket to **Development** on pickup, **Review** when the PR is open.
- Label the PR `agent-generated` when it was written by an AI assistant.
- Comment on the ticket with what was fixed **and what was not** — acceptance
  criteria needing production access are called out, never quietly dropped.
- Don't merge. PRs are reviewed by a person.

Check which branch you are on immediately before and after committing. Commits
have landed on `master` here after an apparently successful `git checkout -b`.
