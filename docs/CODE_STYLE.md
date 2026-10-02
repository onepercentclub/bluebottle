# Code style

Conventions for the bluebottle codebase. Applies to people and to AI assistants
(Claude Code, Cursor) alike — see [CLAUDE.md](../CLAUDE.md) and
`.cursor/rules/bluebottle.mdc`, which both point here.

This is a starting set. Add to it when a review comment turns out to be
something we'd say more than once.

## Formatting and linting

[ruff](https://docs.astral.sh/ruff/) handles both. Configuration lives in
`.ruff.toml`; it mirrors the flake8 rules it replaced, so the switch was not
also a rule change.

```bash
ruff check .          # lint
ruff format .         # format
```

- Line length 120.
- Single quotes (`quote-style = "single"`), matching the existing majority.
- Don't hand-format what ruff formats. If you disagree with the output,
  change the config, not the file.

`ruff check .` runs in CI (the Linting job in
`.github/workflows/quality_checks.yml`) and on commit via pre-commit. `ruff`
is in the `dev` extra, so `pip install -e ".[dev]"` gets you the same version
CI uses.

> **Not yet applied repo-wide.** `ruff format` currently reports ~728 of 1072
> files as unformatted. The one-off reformat is deliberately pending so it
> doesn't collide with open branches, and `ruff-format` is commented out in
> `.pre-commit-config.yaml` until then — otherwise every PR carries reformat
> noise for whichever files it happens to touch.
>
> Until it lands: write new code in the house style, but don't run
> `ruff format` across files you're only editing in passing. `ruff check` is
> enforced on commit and passes cleanly today.

## Comments

Keep them sparse.

- Don't explain what a bug *was*. That belongs in the Jira ticket and the PR,
  where it stays next to the discussion. In the code it goes stale.
- **Never reference a ticket key in code.** `BB-30249` means nothing to someone
  reading the file in a year.
- Comment on intent where the code is genuinely surprising — what it does and
  why, not which incident caused it.

```python
# No:
# BB-30249: wiping validators also dropped MaxLengthValidator, so an over-long
# title reached Postgres as a DataError instead of a 400.
field.validators = [v for v in field.validators if isinstance(v, MaxLengthValidator)]

# Yes — or no comment at all:
# Drafts may be incomplete, but a value that is present must still fit.
field.validators = [v for v in field.validators if isinstance(v, MaxLengthValidator)]
```

The same applies to commit messages in reverse: those *should* explain the
cause, because that's where the history belongs.

## Tests

- A test docstring describes the scenario under test, in one line. No ticket
  keys, no pasted tracebacks, no history of the bug it came from.
- Prefer a test name that carries the meaning, so the docstring is a bonus
  rather than a necessity.
- A regression test should fail against the unfixed code. Check that it does —
  a test written to a fix that never reproduced the bug proves nothing.

Running tests (see also `README.rst`):

```bash
python manage.py test <path> --settings=bluebottle.settings.local --keepdb
```

`--keepdb` matters: a cold run rebuilds every tenant schema and takes ~25
minutes.

## Django and DRF

- Don't use `.get()` on a field without a unique constraint. Check the model,
  not the field name — `slug` is unique on some models here and not others.
- A value that reaches the database unvalidated is a 500 waiting to happen.
  Length limits, null-ability and uniqueness should be enforced at the
  serializer or form, so the user gets a 4xx with a usable message.
- Attribute access on Elasticsearch documents (`AttrDict`) must tolerate
  missing keys — indexed documents are not guaranteed to carry every field.

## Pull requests

- One branch per ticket: `ticket/BB-xxxxx-short-description`.
- Say in the PR what you did *not* do. Acceptance criteria that need
  production access (reindexing, replaying a request, cleaning up tenant rows)
  should be called out, not silently dropped.
- Move the ticket to **Development** when you pick it up and **Review** when
  the PR is open.
