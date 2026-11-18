# Functions, signatures, and flow

This reference explains TypeScript mechanisms for function signature typing, type inference, exhaustive union handling, and async return typing. General functional decomposition, API-shape decisions, and error policy are owned by `pragmatic-functional-programming`, while ECMAScript runtime behavior (such as `??` vs `||`, `Error.cause`, and `return await` unwinding) is owned by the `javascript` skill (`values-and-validation`, `functions-and-errors`, and `async-and-lifecycle`).

## Signature typing and local inference

- **Exported boundaries**: Explicit parameter and return types on exported functions, methods, and public interfaces document contracts clearly and prevent unintentional API changes from altered local inference.
- **Local variables and internal helpers**: Simple local variables and internal helpers can rely on TypeScript's local type inference, avoiding redundant type annotations.

## Parameter objects for ambiguous options

When `pragmatic-functional-programming` favors a parameter object for several optional parameters, flags, or configuration values, model the contract with an explicit interface (following `javascript` `functions-and-errors` for destructuring defaults):

```ts
interface UserSearchOptions {
  query: string;
  limit?: number;
  includeInactive?: boolean;
}

function searchUsers(options: UserSearchOptions): User[] {
  // Named properties prevent confusing positional booleans at call sites
  return [];
}
```

## Guard clauses and control-flow narrowing

Using early return guard clauses simplifies function flow and allows TypeScript's type checker to narrow parameter types early in execution:

```ts
function processUser(user: User | null): string {
  if (!user) {
    return 'Guest';
  }
  // TypeScript narrows user to User here without additional type assertions
  return user.name;
}
```

## Nullish coalescing (??) with optional types

ECMAScript `??` vs `||` semantics are governed by the `javascript` skill (`values-and-validation`). In TypeScript, `??` narrows `T | null | undefined` to `T` while preserving valid falsy values (`0`, `""`, `false`):

```ts
function formatTitle(title?: string): string {
  // Narrows `string | undefined` to `string` without discarding `""`
  return title ?? 'Untitled';
}
```

## Error handling and caught-value typing

Error-wrapping mechanics (`new Error(..., { cause })`, `AggregateError`) and avoiding catch-and-rethrow are governed by the `javascript` skill (`functions-and-errors`). In TypeScript, `useUnknownInCatchVariables` (enabled by `strict: true`) types caught values as `unknown`, requiring narrowing before accessing properties such as `message` or `cause`.

## Result-style unions for expected failures

When a project consistently represents expected business or domain failures as values rather than throwing exceptions, TypeScript discriminated unions model success and failure clearly:

```ts
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

Use `Result`-style unions when the project convention consistently adopts them for expected operational outcomes; do not force them into every function or replace idiomatic error handling without project convention.

## Exhaustive union handling with never

Using the `never` type in the `default` case of a `switch` statement or conditional chain enables TypeScript's compiler to verify exhaustiveness:

```ts
type Notification =
  | { kind: 'email'; recipient: string }
  | { kind: 'sms'; phoneNumber: string }
  | { kind: 'push'; deviceToken: string };

function assertNever(value: never): never {
  throw new Error(`Unhandled union variant: ${JSON.stringify(value)}`);
}

function formatNotification(notification: Notification): string {
  switch (notification.kind) {
    case 'email':
      return `Email to ${notification.recipient}`;
    case 'sms':
      return `SMS to ${notification.phoneNumber}`;
    case 'push':
      return `Push to ${notification.deviceToken}`;
    default:
      return assertNever(notification);
  }
}
```

If a new variant is added to `Notification` and not handled in `formatNotification`, TypeScript reports a compile-time type error because the unhandled variant cannot be assigned to `never`.

## Assertion functions

TypeScript supports assertion signatures (`asserts condition` or `asserts value is Type`) for functions that throw if an invariant is violated:

```ts
function assertString(value: unknown): asserts value is string {
  if (typeof value !== 'string') {
    throw new TypeError(`Expected string, got ${typeof value}`);
  }
}
```

Following a call to `assertString(input)`, TypeScript narrows `input` to `string` in subsequent code.

## Async return typing

Runtime `return await` vs direct-return behavior inside `try/catch` and `try/finally` is governed by the `javascript` skill (`async-and-lifecycle`). In TypeScript, both forms satisfy a `Promise<T>` return signature; avoid redundant `async` wrappers on pure forwarding functions so inferred or explicit `Promise<T>` types remain clean:

```ts
const getUser = (id: string): Promise<User> => {
  return userRepository.findById(id);
};
```
