# Review standards

Every rule below exists because something broke it. Cite rules by id in review comments ("S-1").
Rules marked ⚠ were exploitable or silently wrong, not just untidy.

## Pass 1 — mechanical checks

Run these before reading the diff.

```bash
python manage.py makemigrations --check --dry-run   # models match migrations
python manage.py test                               # and read the WARNINGS, not just the result

# docstrings longer than one line
grep -rn -A3 '"""' '--include=*.py' . | grep -B1 -A2 '^\S*-\s*$'
# serializers that never declare what is read-only
grep -rL "read_only_fields" $(grep -rl "ModelSerializer" '--include=*.py' .)
```

## C — Comments and docstrings

- **C-1** A docstring is one line saying what the thing does. Then stop. No second paragraph: no design rationale,
  framework mechanics or performance notes.
- **C-2** Rationale belongs in the commit message or the PR description.
- **C-3** Comments never narrate history: no "rather than", "used to" or "the point of this". This applies to test
  docstrings too.

## M — Models

- **M-1** Don't store what you can derive (e.g. a `type`, `max_score` or `question_count` column).
- **M-2** An event carries its timestamp, not a status column. Use `started_at` / `submitted_at` / `graded_at`, and make
  status a property. If a state can't be derived, an event timestamp is missing.
- **M-3** ⚠ Every derived property prefers an annotation: `getattr(self, '_max_score', None)` first, then fall back to
  the query. Without this, a serializer causes an N+1.
- **M-4** Never override `save()` to call `full_clean()`. `bulk_create`, `update()` and migrations skip it, and it
  raises a Django `ValidationError` that DRF turns into a 500.
- **M-5** Anything the database can express is a `CheckConstraint`. `clean()` keeps only what spans columns.
- **M-6** Use the real column type: `ArrayField(PositiveIntegerField())` over `JSONField` for a list of ints.
- **M-7** A many-to-many with attributes needs a `through` model.
- **M-8** Use `on_delete=PROTECT` for a shared library row that something is using.
- **M-9** Use `Meta.ordering` only when the order is part of what the data means. An order that a screen chooses goes on
  the viewset with `OrderingFilter`.
- **M-10** One name per concept across the whole schema.
- **M-11** Reference fields as `Model.fields.x`, never as a bare string. It validates at import.

## S — Serializers

- **S-1** ⚠ Declare `read_only_fields`. A `ModelSerializer` makes every field writable by default.
- **S-2** ⚠ Authorise with the field's queryset, not with a hand-written check. Scope
  `PrimaryKeyRelatedField(queryset=…)` to what the caller may reach, and default it to `.none()` so it fails closed.
- **S-3** One serializer per resource, split by `read_only` / `write_only`. Don't add a separate `XRequestSerializer`.
- **S-4** Always write `data = super().validate(data)` and use the return value.
- **S-5** No `SerializerMethodField` where a model property or an annotation will do.
- **S-6** Split out a Basic serializer for lists that don't need the nested children.
- **S-7** Validation lives in the serializer (a 400 with a field key) and in the DB constraint. Both, deliberately.
  Never in `model.save()`.

## V — Views

- **V-1** Use DRF's hooks (`perform_create` and the rest). When you replace a hook, don't call `super()`.
- **V-2** Never pass `context={...}` wholesale. Use `self.get_serializer_context()`, and pass extras as explicit
  `__init__` kwargs.
- **V-3** ⚠ Every paginated viewset declares `ordering`. Watch for `UnorderedObjectListWarning`.
- **V-4** ⚠ Re-read the instance after a write that went round it.
- **V-5** Permissions come from the shared module. No per-app class that reimplements one.
- **V-6** Mixins stay plain classes unless the framework requires the base. A serializer mixin calling
  `super().validate` extends `Serializer`. A filter mixin declaring filters extends `FilterSet`.

## Q — Queries

- **Q-1** ⚠ Aggregate with correlated subqueries, never over a join. A join multiplies `Count`/`Sum`.
- **Q-2** ⚠ Use `Exists()`, not a join, for existence filters.
- **Q-3** ⚠ A nested object that needs annotations requires `Prefetch`, not `select_related`.
- **Q-4** ⚠ Every paginated list must be query-flat. Prove it with a test: count queries at 1 row and at 5 rows, and
  assert they're equal.

## T — Tests

- **T-1** A test file mirrors one source file: model tests go in `test_models`, view tests in `test_views`.
- **T-2** Test at the layer that enforces the rule. A constraint gets an `IntegrityError` test. A serializer rule gets a
  400 with a field key.
- **T-3** Every review finding lands with a regression test in the same commit.
- **T-4** Delete tests for behaviour that no longer exists. Don't adapt them until they pass.

## P — How to review

- **P-1** Verify framework behaviour by running a throwaway probe, not by reasoning about it.
- **P-2** When a rule appears in two places, ask which one actually runs.
- **P-3** The frontend is part of an API change. Diff the serializer's output fields against the TS interfaces, and
  every URL the client builds against the router.
- **P-4** Green tests are not the bar. Read the warnings the run prints.
