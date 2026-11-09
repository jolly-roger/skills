# Domain models and runtime boundaries

This reference explains TypeScript mechanisms for parsing external data into domain types, handling type erasure, and modeling domain concepts. The determination of trust boundaries and persistence guarantees is owned by `pragmatic-functional-programming`.

## Domain concepts: time, currency, identifiers, and optionality

Whenever domain correctness depends on specific value semantics (for internal domain models and boundary contracts alike):
- **Time**: Model temporal data explicitly using parsed `Date` objects, timestamp numbers, or ISO string aliases depending on whether computation or transport is required.
- **Currency**: Model monetary amounts explicitly with precision-safe representations suited to domain requirements and project conventions (such as scale, range, arithmetic, serialization, and interoperability). Options include integer minor units (e.g. `totalCents`), fixed-scale decimal representations, arbitrary-precision decimal libraries, or dedicated value objects, rather than ambiguous floating-point numbers.
- **Identifiers**: Model entities with explicit, semantic identifier types and naming rather than generic untyped values throughout the domain.
- **Semantic types**: Use meaningful domain interfaces and cohesive nested concepts rather than generic `Record<string, unknown>`.

## Trust boundaries and validation in TypeScript

As established by `pragmatic-functional-programming`, inputs crossing an untrusted boundary (such as external HTTP requests, webhooks, or unvalidated files) must be validated before being treated as domain types. Conversely, values covered by trusted persistence guarantees or strong internal schemas do not require redundant runtime validation merely because they originate from storage.

When values cross an untrusted boundary:
- Type the incoming value as `unknown` rather than using `any` or an unchecked type assertion.
- Parse or narrow the `unknown` payload into explicit TypeScript domain interfaces.
- Use explicit mapping functions when external field formats, naming conventions, dates, or constraints differ from internal domain contracts.
- Use runtime schema libraries (e.g. Zod, Valibot, ArkType) when already adopted by the project; simple local guards are sufficient when external dependencies are not warranted.

## Example: parsing untrusted payloads into domain interfaces

Avoid casting unvalidated boundary data directly to domain types:

```ts
interface Order {
  id: string;
  totalCents: number;
  createdAt: Date;
}

// Unsound: response payload is not validated at runtime
const order = (await response.json()) as Order;
```

Type untrusted input as `unknown` and validate fields before constructing the domain object:

```ts
interface Order {
  id: string;
  totalCents: number;
  createdAt: Date;
}

function parseOrder(value: unknown): Order {
  if (typeof value !== 'object' || value === null) {
    throw new Error('Invalid order payload: expected object');
  }
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.id !== 'string') {
    throw new Error('Invalid order: missing or invalid id');
  }
  if (typeof candidate.totalCents !== 'number' || !Number.isSafeInteger(candidate.totalCents) || candidate.totalCents < 0) {
    throw new Error('Invalid order: invalid totalCents');
  }
  if (typeof candidate.createdAt !== 'string') {
    throw new Error('Invalid order: missing createdAt timestamp');
  }
  const createdAt = new Date(candidate.createdAt);
  if (Number.isNaN(createdAt.getTime())) {
    throw new Error('Invalid order: createdAt is not a valid date');
  }
  return { id: candidate.id, totalCents: candidate.totalCents, createdAt };
}

const rawPayload: unknown = await response.json();
const order: Order = parseOrder(rawPayload);
```

## Optional property semantics and exactOptionalPropertyTypes

In TypeScript:
- An optional property `displayName?: string` allows the property to be omitted or set to `undefined`.
- An explicit nullable property `displayName: string | null` requires the key to be present with either a string or `null`.

```ts
interface UpdateProfileRequest {
  // Absent: leave unchanged; null: clear display name; string: set new name
  displayName?: string | null;
}
```

When `exactOptionalPropertyTypes: true` is enabled in `tsconfig.json`, TypeScript distinguishes omitting a property from explicitly passing `undefined`:
```ts
const req: UpdateProfileRequest = {}; // valid
req.displayName = undefined;           // error under exactOptionalPropertyTypes
req.displayName = null;                // valid
```
Ensure boundary parsers and domain types model optionality and absence consistently with project compiler settings.
