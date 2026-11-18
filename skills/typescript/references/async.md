# Async, concurrency, and cancellation

This reference explains TypeScript typing and lint implications for Promise APIs, cancellation tokens, and async control flow. Concurrency policy, execution ordering, concurrency bounds, and resource lifecycle rules are governed by `pragmatic-functional-programming`. ECMAScript runtime semantics for `async`/`await`, Promise combinators, `forEach`, `return await`, `using`, and cancellation are governed by the `javascript` skill (`async-and-lifecycle`). Floating promise prevention is governed canonically by `AGENTS.md` under `## TypeScript Rules`.

## async/await for multi-step operations

Preferring `async`/`await` with `try`/`catch` over deeply nested `.then()`/`.catch()` chains for multi-step asynchronous operations is governed by `pragmatic-functional-programming` (readability) and the `javascript` skill (`async-and-lifecycle`). In TypeScript, `async` functions infer or enforce `Promise<T>` return types directly across linear `await` steps.

## Promise.all and Promise.allSettled typing

Runtime fail-fast, sibling-continuation, and settlement behavior for `Promise.all` and `Promise.allSettled` are governed by the `javascript` skill (`async-and-lifecycle`). TypeScript models their return values statically:

- **`Promise.all` tuple inference**: Preserves a strongly typed tuple matching each input Promise (`[Profile, Permissions]`):

```ts
const [profile, permissions] = await Promise.all([
  fetchProfile(userId),
  fetchPermissions(userId),
]);
```

- **`Promise.allSettled` discriminated results**: Resolves to an array of `PromiseSettledResult<T>` discriminated union members:
  - `{ status: 'fulfilled'; value: T }`
  - `{ status: 'rejected'; reason: any }` (`PromiseRejectedResult.reason` is declared as `any` in TypeScript's standard library; treat or narrow `reason` as `unknown` before reading properties)

```ts
const results = await Promise.allSettled([
  taskA(),
  taskB(),
]);
```

## Floating promises and type-aware detection

In TypeScript, a floating promise refers to a Promise value whose rejection or completion is not handled within the surrounding control flow:

```ts
function recordActivity(userId: string): void {
  // Floating promise: rejection cannot be observed or caught by caller
  auditLog.write({ userId, action: 'view' });
}
```

- **Detection**: Type-aware linters (such as `@typescript-eslint/no-floating-promises`) analyze the AST and type checker to detect unhandled Promises.
- **Syntax representation**: The decision whether an operation should be awaited, returned, or supervised as detached work is owned by `pragmatic-functional-programming` and `AGENTS.md` (under `## TypeScript Rules`). TypeScript expresses these patterns as follows:
  - Awaiting or returning the promise:
    ```ts
    async function recordActivity(userId: string): Promise<void> {
      await auditLog.write({ userId, action: 'view' });
    }
    ```
  - Attaching an explicit rejection handler when an operation is intentionally detached:
    ```ts
    function trackDetached(event: MetricEvent): void {
      metricsClient.send(event).catch(error => {
        logger.warn('Failed to send detached metric', { event, error });
      });
    }
    ```

## Cancellation with AbortSignal

`AbortSignal` represents cancellation signals passed across asynchronous boundaries:

```ts
async function fetchResource(url: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}
```

Passing `signal` down to underlying libraries (such as `fetch` or Node.js APIs) ensures that pending network requests, socket allocations, or abortable workflows terminate when cancelled.

### Timeout typing and compiler compatibility

Runtime differences between `Promise.race` timeouts and cooperative cancellation are governed by the `javascript` skill (`async-and-lifecycle`). In TypeScript, type cancellation parameters explicitly as `signal?: AbortSignal` and verify that static helpers such as `AbortSignal.timeout(ms)` match the project's configured `tsconfig.json` `lib` / `target` baseline. Operational timeout policy, deadlines, and fallback decisions remain governed by `pragmatic-functional-programming`.

## return await and type-aware lint rules

Runtime `return await` behavior inside `try/catch` and `try/finally` is governed by the `javascript` skill (`async-and-lifecycle`). In TypeScript projects using `typescript-eslint`, rules such as `@typescript-eslint/return-await` align with that runtime distinction—requiring `return await` inside `try` blocks so rejections are caught locally and stack frames are preserved, while allowing direct `Promise<T>` returns outside `try` blocks.
