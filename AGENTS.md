# Development Rules

## Pragmatic Functional Programming Rules

For every coding task, including new code generation, feature implementation, bug fixes, modifications, optimization, tests, code review, and refactoring, apply pragmatic functional programming in any language.

Before changing, generating, or reviewing code, read the `pragmatic-functional-programming` skill when it is accessible. Consult its reference documents selectively as relevant. If the skill is unavailable, still apply these defaults:

- Distinguish data, deterministic calculations, and actions with side effects.
- Prefer pure domain logic, immutable boundaries, and explicit state transitions when practical.
- Do not mutate caller-owned inputs unexpectedly; keep dependencies explicit and isolate I/O and other effects at understandable boundaries.
- Prefer readable composition, clear domain models, and idiomatic error handling.
- Validate untrusted inputs at boundaries and preserve contracts and observable behavior unless the requested change intentionally updates them.
- Respect existing architecture, framework conventions, performance, concurrency, and operational requirements.
- Allow classes, loops, owned local mutation, and other imperative constructs when clearer or idiomatic.
- Do not introduce FP libraries, unnecessary abstractions, or unrelated refactoring.

Prioritize correctness, project conventions, readability, maintainability, simplicity, and testability over functional purity.

## TypeScript Rules

For every TypeScript and TSX coding task, load and apply `pragmatic-functional-programming` first as foundational guidance, then read and apply the `typescript` skill when it is accessible. Consult its reference documents selectively as relevant.

The `pragmatic-functional-programming` skill has precedence wherever the two skills overlap. If `pragmatic-functional-programming` is unavailable, do not apply either the `typescript` skill or its TypeScript fallback rules.

Apply these mandatory policies:

- Prefer `interface` for named object contracts, especially public and domain-facing objects. An object `type` alias is permitted when an established project convention or TypeScript constraint makes it the clearer representation; do not convert existing code solely for stylistic uniformity.
- Use `type` for unions, tuples, primitive aliases, mapped or conditional types, and shapes that are not naturally expressed as interfaces.
- Avoid deriving domain and API models through `Omit` or chains of utility types. Prefer explicit contracts or genuinely meaningful shared interfaces.
- Permit a narrow utility-type use in a local adapter, generic helper, or third-party integration only when it is clearer than an explicit duplicate contract and does not weaken domain semantics.
- Prefer shallow, cohesive models, but preserve meaningful nested concepts rather than flattening them mechanically.

When `pragmatic-functional-programming` is available but the `typescript` skill is not, apply these fallback rules:

- Do not introduce `any`, TypeScript suppression directives, or weaker compiler or linter settings merely to silence errors.
- Use `unknown`, narrowing, or runtime validation when a value crosses a trust boundary identified by `pragmatic-functional-programming`; do not rely on a TypeScript assertion as runtime validation.
- Do not leave unintended floating promises; use TypeScript-aware tooling and explicit supervision for intentionally detached work.

## Git Safety

  - Git read operations against remotes are allowed when useful, including `git fetch`, `git ls-remote`, and reading remote refs.
  - Git write operations must be local-only unless I explicitly request a remote write.
  - Do not run remote-mutating commands by default, including:
    - `git push`
    - `git push --force`
    - `git push --delete`
    - `git tag` followed by pushing tags
    - `git remote set-url`
    - `git remote add`
    - `git remote remove`
    - `git remote rename`
  - Before any remote git write operation, ask for confirmation and state the exact command.
  - Local write operations are allowed, including:
    - `git checkout -b`
    - `git switch -c`
    - `git branch`
    - `git add`
    - `git commit`
    - `git stash`
    - `git tag` when not pushed
  - Branches should be created locally first and not pushed unless I explicitly ask.

## Jira Safety

  - Treat Jira as assigned-to-me only by default.
  - Every Jira search must include `assignee = currentUser()` unless I explicitly request a broader query.
  - Before reading or mutating a specific Jira issue, verify its assignee is `currentUser()`.
  - Before implementation, fetch the latest ticket data when needed and use it as part of the implementation context.
  - In other cases, a cached ticket version may be used if one is already available.
  - If assignee verification is unavailable or the issue is not assigned to me, ask before proceeding.
  - Never mutate Jira issues not assigned to me unless I explicitly name the issue and request the mutation.

## MongoDB Safety

  - Treat `db` as the workspace-local MongoDB alias for the active project.
  - All MongoDB operations must target only the local database referenced by `db`.
  - Do not read, query, aggregate, export, mutate, or inspect any other MongoDB database, including `admin`, `config`, and `local`, unless I explicitly request it.
  - Before any MongoDB write operation, state the exact target database and collection.

## SCSS Rules

- The main class in a component SCSS file must use the component name in kebab case.
- All child classes must be nested according to the component hierarchy and usage.
- Avoid flat, loosely named selectors when the styles belong to a specific component.
- Always use `rem` units in SCSS, with `1rem = 16px`.

## JSX Rules

- JSX markup ternary operators must not contain nested ternary operators.

## README Guidance

  - README files should stay high-level and summarize the broader information.
  - Do not duplicate detailed content that already exists in other markdown files.
  - When details are needed, link or refer to the source markdown file instead of repeating the information.
  - README files should describe the repository content and purpose, not explain why or how the README was written.
  - README files should not refer to themselves or explain the README content as content.
