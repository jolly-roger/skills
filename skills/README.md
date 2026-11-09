# Agent Skills

Reusable workflows discovered by Codex and Antigravity when installed into a workspace's `.agents/skills/` directory.

## Available Skills

- [`merge-master`](./merge-master/SKILL.md) — pulls the latest base branch and merges it into the current work branch without resolving conflicts automatically.
- [`pragmatic-functional-programming`](./pragmatic-functional-programming/SKILL.md) — guides code design, refactoring, and review around pure calculations, explicit effects, and immutable boundaries. Includes supplemental reference guides:
  - [Foundations and decision examples](./pragmatic-functional-programming/references/foundations.md)
  - [Architecture and boundaries](./pragmatic-functional-programming/references/architecture.md)
  - [Composition and state](./pragmatic-functional-programming/references/composition-and-state.md)
  - [Errors and testing](./pragmatic-functional-programming/references/errors-and-testing.md)
- [`review`](./review/SKILL.md) — performs context-aware code reviews covering changes, surrounding call sites, and touched components.
- [`review-diff`](./review-diff/SKILL.md) — performs targeted diff reviews against the base branch.
- [`typescript`](./typescript/SKILL.md) — specializes type modeling, safety, runtime boundaries, async execution, and tooling for TypeScript and TSX, requiring `pragmatic-functional-programming` as a foundational prerequisite. Includes supplemental reference guides:
  - [Type design](./typescript/references/type-design.md)
  - [Type safety and narrowing](./typescript/references/type-safety.md)
  - [Functions, signatures, and flow](./typescript/references/functions.md)
  - [Domain models and runtime boundaries](./typescript/references/data-modeling.md)
  - [Async, concurrency, and cancellation](./typescript/references/async.md)
  - [Modules and dependency boundaries](./typescript/references/modules.md)
  - [Tooling, tests, and verification](./typescript/references/tooling.md)

## Adding a Skill

1. Create a directory at `skills/<skill-name>/`.
2. Add a `SKILL.md` file with standard YAML frontmatter (`name`, `description`) and markdown instructions. Supplemental guidance may be placed in a `references/` subdirectory.
3. List the new skill in this file and in the root [`README.md`](../README.md).
