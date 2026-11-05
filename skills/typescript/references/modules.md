# Modules and dependency boundaries

This reference explains TypeScript mechanisms for module resolution, type-only imports, and package surface boundaries. Architectural separation and dependency injection strategies are established by `pragmatic-functional-programming`.

## Module conventions and cohesion

- **Standard conventions**: Follow ES module syntax (`import`/`export`) and project-standard conventions.
- **Module cohesion**: Keep modules focused and cohesive around related domain concepts or responsibilities; avoid splitting files solely to satisfy arbitrary line-count rules when doing so fragments related logic or introduces unnecessary cross-file coupling.

## Type-only imports (import type)

Using `import type` indicates to TypeScript that an import is referenced only in type positions:

```ts
import type { User, UserRole } from './models/user.js';
import { formatUserName } from './utils/format.js';

export function renderUser(user: User, role: UserRole): string {
  return `${formatUserName(user)} (${role})`;
}
```

This guarantees that the import will be completely elided during compilation, preventing unwanted runtime module evaluation or circular execution side effects.

## Module resolution and extensions

- **Resolution modes**: Respect the project's `moduleResolution` setting in `tsconfig.json` (such as `NodeNext`, `Bundler`, or `Node10`).
- **File extensions**: In `NodeNext` ESM projects, TypeScript requires explicit `.js` extensions on relative import paths even when referencing `.ts` source files. Follow existing project conventions.

## Barrel exports and cycles

- **Internal modules**: Prefer direct file imports (`import { OrderService } from '../services/order-service.js'`) for internal cross-module references. Barrel files (`index.ts`) that re-export multiple siblings frequently introduce circular initialization dependencies and runtime `undefined` values.
- **Public package boundaries**: Reserve barrel exports for curated public entry points of packages or distinct subsystems.
- **Exported type surface**: Keep exported types and interfaces minimal. Avoid exporting internal helpers, temporary shapes, or private contracts without consumers.
