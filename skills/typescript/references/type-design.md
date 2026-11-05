# Type design

This reference provides TypeScript mechanisms, explanations, and examples that support the mandatory type modeling policies defined canonically in `AGENTS.md` under `## TypeScript Rules`. Foundational domain modeling principles are governed by `pragmatic-functional-programming`.

## Interface and type mechanisms

TypeScript provides two core ways to name types:
- `interface`: Declares an object shape with support for compiler error reporting, property inheritance via `extends`, and declaration merging. It represents named object contracts in TypeScript.
- `type`: Defines an alias for any type expression, including unions, tuples, primitive aliases, and mapped or conditional types.

The canonical choice between interfaces, type aliases, explicit contracts, and utility types is defined in `AGENTS.md` under `## TypeScript Rules`, which prefers `interface` for named object contracts while permitting object `type` aliases when established project conventions or TypeScript constraints make them the clearer choice.

## Discriminated unions

TypeScript control-flow analysis narrows distinct object shapes when they share a literal discriminator field (such as `status` or `kind`). This allows the type system to represent mutually exclusive variants cleanly:

```ts
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };
```

Checking `state.status === 'success'` narrows `state` to the success variant and makes `state.data` accessible without type assertions.

## Non-mutating parameter contracts

In TypeScript, `readonly T[]` and `ReadonlyArray<T>` express at compile time that a function will not mutate caller-supplied collections:

```ts
function sortedNames(users: readonly { name: string }[]): string[] {
  // If supported by project runtime target (ES2023+), users.toSorted(...) is an option.
  return [...users]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(user => user.name);
}
```

Attempting mutating array operations (such as `.push()` or in-place `.sort()`) on a `readonly` array triggers a TypeScript compiler error.

## Generics and type relationships

Generics capture real relationships between parameter types and return types across multiple positions:

```ts
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}
```

Avoid unconstrained generic parameters that do not connect multiple positions or merely allow callers to assert unvalidated return types:

```ts
// Unsound: caller can assert any return type without verification
function parseJson<T>(raw: string): T {
  return JSON.parse(raw) as T;
}
```

Prefer `unknown` and narrow or validate the return value at the boundary.

## Domain contracts vs utility derivation

Contrasting utility-type derivation with explicit modeling:

```ts
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Couplings: CreateUserRequest changes if User gains unrelated persistence fields
type CreateUserRequest = Omit<User, 'id' | 'createdAt'>;
```

Illustrating explicit modeling with shared semantics:

```ts
interface UserDetails {
  name: string;
  email: string;
}

interface User extends UserDetails {
  id: string;
  createdAt: Date;
}
```

Do not introduce an empty interface extension (`interface CreateUserRequest extends UserDetails {}`) when the shared interface already has the correct public meaning; use `UserDetails` directly as the parameter or request type. When a request model has distinct fields, validation, or lifecycle semantics, define its fields explicitly rather than extending.

## Decision test

Before using a complex type expression, ask:
- Does it express a real invariant?
- Will readers understand it without mentally evaluating a type-level program?
- Could a short named contract communicate intent better?
