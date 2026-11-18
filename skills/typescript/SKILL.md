---
name: typescript
description: >
  Apply pragmatic, maintainable TypeScript practices for type modeling,
  safety, runtime boundaries, async execution, modules, and tooling. Requires
  the pragmatic-functional-programming and javascript skills as foundations and
  is not intended for standalone use.
---
# Pragmatic TypeScript

Apply this guidance to TypeScript and TSX code, including new code, modifications, bug fixes, type definitions, and code reviews. This skill is a Tier 3 static type-system specialization; it supplies TypeScript-specific mechanisms, explanations, and tooling that build on `pragmatic-functional-programming` (Tier 1) and `javascript` (Tier 2).

## Prerequisite and precedence

1. **Prerequisites**: For every TypeScript or TSX coding task, load and apply `pragmatic-functional-programming` first (general engineering decisions) and `javascript` second (canonical ECMAScript runtime semantics and mechanisms) before applying `typescript`.
2. **Precedence**: `pragmatic-functional-programming` has higher priority over `javascript` on general engineering decisions, and `javascript` has higher priority over `typescript` for ECMAScript runtime semantics. `typescript` is authoritative for static type-system modeling, compile-time narrowing, `import type`, compiler strictness, and type-aware tooling.
3. **Missing prerequisites**:
   - If `pragmatic-functional-programming` cannot be loaded, report that the required Tier 1 foundation is unavailable and do not apply or claim to have applied `javascript`, `typescript`, or their fallback rules.
   - If `javascript` cannot be loaded, report that the required Tier 2 ECMAScript foundation is unavailable and do not apply or claim to have applied the dependent `typescript` skill, while retaining the mandatory `AGENTS.md` TypeScript modeling policies and fallback safety rules.

## Policy alignment

Mandatory policies for interfaces, type aliases, `Omit`, utility types, trust boundaries, and floating promises are canonically owned by `AGENTS.md` under `## TypeScript Rules`. This skill provides TypeScript-specific explanations, mechanisms, permitted exceptions, and examples that support those policies.

## TypeScript workflow

1. Inspect `tsconfig.json`, package scripts, module settings, and project lint/typecheck configuration.
2. Identify type contracts: exported API surfaces, public interfaces, trust boundaries identified by the foundational skill, and runtime compatibility constraints.
3. Choose the least complex type-safe design in alignment with `AGENTS.md` policy and the references below.
4. Read only the references pertinent to the task.
5. Implement focused changes: rely on local inference, type public boundaries explicitly, and avoid unnecessary type-level machinery.
6. Run available typecheck (`tsc --noEmit`) or lint commands. Disclose what was not run and why if commands are unavailable.
7. Review changes using the checklist below.

## Reference selection

Read only the references relevant to the task:

- [Type design](references/type-design.md) — TypeScript mechanisms for interfaces, type aliases, discriminated unions, utility types, readonly collections, and generics.
- [Type safety and narrowing](references/type-safety.md) — TypeScript narrowing mechanisms, `unknown`, user-defined type guards, avoiding assertions, `satisfies`, and `as const`.
- [Functions, signatures, and flow](references/functions.md) — signature typing, return inference, exhaustive union handling with `never`, and async returns.
- [Domain models and runtime boundaries](references/data-modeling.md) — runtime type erasure, parsing `unknown` payloads, schema validation, and optional-property semantics.
- [Async, concurrency, and cancellation](references/async.md) — observable semantics of `Promise.all` and `Promise.allSettled`, floating promise detection, `AbortSignal`, and `return await`.
- [Modules and dependency boundaries](references/modules.md) — `import type`, module-resolution conventions, barrel exports, and minimal public type surface.
- [Tooling, tests, and verification](references/tooling.md) — compiler strictness options, type-aware linting, compile-time type tests, and script discovery.

## Completion checklist

- [ ] Interfaces, type aliases, `Omit`, and model composition follow canonical `AGENTS.md` policy under `## TypeScript Rules`.
- [ ] Trust boundary values, compiler suppressions, and floating promises comply with `AGENTS.md` safety and fallback rules under `## TypeScript Rules`.
- [ ] Type design applies TypeScript mechanisms (discriminated unions, `never`, `readonly`) without unnecessary type machinery.
- [ ] Non-null assertions (`!`) and type assertions (`as`) are avoided or justified at unavoidable boundaries.
- [ ] Available typecheck (`tsc --noEmit`) and lint commands were executed, or limitations disclosed.
