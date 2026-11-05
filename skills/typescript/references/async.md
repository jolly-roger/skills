# Async, concurrency, and cancellation

This reference explains the observable behavior and mechanics of TypeScript Promise APIs, cancellation tokens, and async control flow. Concurrency policy, execution ordering, concurrency bounds, and resource lifecycle rules are governed by `pragmatic-functional-programming`. Floating promise prevention is governed canonically by `AGENTS.md` under `## TypeScript Rules`.

## async/await for multi-step operations

Using `async`/`await` syntax for multi-step asynchronous operations and error handling provides linear, readable control flow and clear exception handling via `try/catch`, avoiding deeply nested Promise `.then()` and `.catch()` chains.

## Promise.all observable semantics

`Promise.all` aggregates an iterable of Promises into a single Promise:

```ts
const [profile, permissions] = await Promise.all([
  fetchProfile(userId),
  fetchPermissions(userId),
]);
```

- **Fulfillment**: Resolves when all input promises have fulfilled, returning a strongly typed tuple or array matching the types of the input promises.
- **Rejection behavior**: Rejects immediately upon the first input promise rejection (fail-fast).
- **Execution note**: `Promise.all` does not cancel or terminate remaining in-flight operations when one rejects; uncancelled sibling operations continue executing to completion in the background.

## Promise.allSettled observable semantics

`Promise.allSettled` waits for every input promise to complete, regardless of individual fulfillment or rejection:

```ts
const results = await Promise.allSettled([
  taskA(),
  taskB(),
]);
```

- **Return shape**: Resolves to an array of discriminated `PromiseSettledResult<T>` objects:
  - `{ status: 'fulfilled', value: T }`
  - `{ status: 'rejected', reason: any }`
- **Use case**: Allows inspecting the individual outcome of each operation without premature termination upon a single failure.

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

### Timeout semantics vs aborting work

When implementing or consuming timeouts, distinguish between ending caller waiting and aborting the underlying operation:
- A `Promise.race` against a timer only stops waiting for the promise; the in-flight asynchronous operation continues executing in the background.
- To abort the underlying work, tie the timeout directly to an `AbortSignal` (such as `AbortSignal.timeout(ms)` or wiring a timer to `AbortController.abort()`) and pass the signal to cancellable operations.
- Operational timeout policy, deadlines, and fallback decisions remain governed by `pragmatic-functional-programming`.

## The return await pattern

In an `async` function, returning a Promise directly versus using `return await` has distinct behavior inside `try/catch` or `try/finally` blocks:

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

- **Inside try/catch**: `return await` unwraps the Promise before returning, allowing the local `catch` or `finally` block to intercept any rejection. Without `await`, the unresolved Promise is returned directly to the caller, bypassing the local `catch` block.
- **Stack traces**: `return await` ensures that the current function is preserved in asynchronous stack traces when the Promise rejects, aiding debugging in environments where un-awaited Promise returns truncate call frames.
- **Outside try/catch**: Outside of `try` blocks, returning the Promise directly (`return userRepository.findById(id);`) is idiomatic when no local error handling or stack-trace preservation is required.
