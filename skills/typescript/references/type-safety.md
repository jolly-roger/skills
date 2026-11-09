# Type safety and narrowing

This reference explains TypeScript mechanisms for narrowing, guards, and type assertions. Safety boundaries and compiler suppression rules are governed canonically by `AGENTS.md` under `## TypeScript Rules` and `pragmatic-functional-programming`.

## The unknown type and narrowing

In TypeScript, `unknown` represents values whose shape cannot be statically verified at compile time. Unlike `any`, the compiler prevents accessing properties, methods, or calling an `unknown` value until it is narrowed:

```ts
// Unsound: type assertion overrides compiler without runtime verification
const payload = JSON.parse(raw) as { email: string };
sendEmail(payload.email);
```

Using `unknown` paired with control-flow analysis or user-defined type guards ensures type safety:

```ts
function isEmailPayload(value: unknown): value is { email: string } {
  if (typeof value !== 'object' || value === null) return false;
  if (!('email' in value)) return false;
  return typeof (value as { email: unknown }).email === 'string';
}

const parsed: unknown = JSON.parse(raw);
if (!isEmailPayload(parsed)) {
  throw new Error('Invalid email payload');
}
sendEmail(parsed.email);
```

A user-defined type guard (`value is T`) asserts only what is explicitly checked in its implementation.

## Replacing non-null assertions

Non-null assertions (`!`) suppress compiler checks without verifying the presence of a value at runtime:

```ts
// Fragile: triggers runtime TypeError if not found
const user = users.find(u => u.id === id)!;
return user.email;
```

Control-flow analysis naturally narrows types when explicit checks or guards are used:

```ts
const user = users.find(u => u.id === id);
if (!user) {
  throw new Error(`User ${id} not found`);
}
return user.email;
```

## The satisfies operator

The `satisfies` operator checks that an expression conforms to a type contract while preserving the expression's specific inferred literal types:

```ts
const retryPolicy = {
  attempts: 3,
  strategy: 'exponential',
} satisfies { attempts: number; strategy: 'fixed' | 'exponential' };

// retryPolicy.strategy retains the literal type 'exponential' rather than widening to 'fixed' | 'exponential'
```

## The as const assertion

Applying `as const` instructs TypeScript to infer the narrowest possible literal types for expressions and recursively marks all object properties and array elements as `readonly`:

```ts
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE'] as const;
// Inferred type: readonly ['GET', 'POST', 'PUT', 'DELETE']
// Element union: (typeof HTTP_METHODS)[number] => 'GET' | 'POST' | 'PUT' | 'DELETE'

const config = {
  endpoint: 'https://api.example.com',
  timeoutMs: 5000,
} as const;
// Inferred type: { readonly endpoint: 'https://api.example.com'; readonly timeoutMs: 5000 }
```

- **Literal inference**: Preserves specific string, number, or boolean literals instead of widening them to `string`, `number`, or `boolean`. This is useful for deriving union types from constant data tables.
- **Deep-readonly consequence**: Inferred structures become deeply immutable (`readonly`). Attempting in-place mutation triggers compile errors, and values cannot be passed directly to APIs expecting mutable arguments.

## Nullability and absence

TypeScript distinguishes `undefined` from `null`. By convention:
- `undefined` represents absence (an unassigned variable or omitted optional property).
- `null` represents an intentional empty value.

## Unavoidable library assertions

When interacting with poorly typed external libraries or dynamic framework boundaries where TypeScript cannot infer the correct type, isolate the type assertion (`as Type`) to the immediate boundary and pair it with an explicit runtime invariant check or guard.

## Type erasure

TypeScript types exist exclusively at compile time. Structural type declarations, interfaces, and type aliases are completely removed during compilation and do not validate runtime data structures.
