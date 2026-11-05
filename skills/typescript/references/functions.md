# Functions, signatures, and flow

This reference explains TypeScript mechanisms for function signature typing, type inference, exhaustive union handling, and async return delegation. General functional decomposition, naming, and error classification are owned by `pragmatic-functional-programming`.

## Signature typing and local inference

- **Exported boundaries**: Explicit parameter and return types on exported functions, methods, and public interfaces document contracts clearly and prevent unintentional API changes from altered local inference.
- **Local variables and internal helpers**: Simple local variables and internal helpers can rely on TypeScript's local type inference, avoiding redundant type annotations.

## Parameter objects for ambiguous options

When a function accepts several optional parameters, flags, or configuration values, using a parameter object interface prevents positional argument errors:

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

## Nullish coalescing (??) versus logical OR (||)

In TypeScript and JavaScript:
- `a ?? b` checks only for `null` and `undefined`.
- `a || b` checks for any falsy value (`null`, `undefined`, `""`, `0`, `false`, `NaN`).

Use `??` when empty strings or zero are valid domain inputs that must be preserved:

```ts
function formatTitle(title?: string): string {
  // Using ?? ensures "" is preserved if passed, rather than replaced by fallback
  return title ?? 'Untitled';
}
```

## Error handling and cause preservation

- **Avoid catching solely to rethrow unchanged**: Do not catch errors solely to rethrow them immediately without adding value. Catching is appropriate when enriching errors with meaningful context via `{ cause: error }`, translating external exceptions into domain errors, performing boundary-owned logging, or guaranteeing resource cleanup.
- **Preserving error cause**: When wrapping errors with additional context, use the standard `cause` option to preserve original diagnostic details:

```ts
try {
  parseConfigFile(filePath);
} catch (error) {
  throw new Error(`Failed to load config from ${filePath}`, { cause: error });
}
```
Preserving `{ cause: error }` retains original stack traces and diagnostic details across abstraction boundaries.

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

## Async return delegation

When a function merely forwards a Promise from another call without intermediate transformations or local error handling, returning the Promise directly avoids redundant `async` and `await` wrapping:

```ts
// Direct delegation
const getUser = (id: string): Promise<User> => {
  return userRepository.findById(id);
};
```

When local error interception is necessary within a `try/catch` block, `return await` ensures rejections are caught locally before returning:

```ts
async function loadUserData(id: string): Promise<User> {
  try {
    return await userRepository.findById(id);
  } catch (error) {
    logger.error('Failed to load user', { id, error });
    throw error;
  }
}
```
Without `await` inside the `try` block, an unhandled rejection would bypass the local `catch` handler and bubble directly to the caller.
