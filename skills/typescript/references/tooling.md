# Tooling, tests, and verification

This reference explains TypeScript compiler configuration, type-aware linting, and compile-time type verification. Compiler and linter suppression rules are governed canonically by `AGENTS.md` under `## TypeScript Rules`. General testing strategies, failure testing, and invariant verification are owned by `pragmatic-functional-programming`.

## Compiler options

- **Strict mode (`strict: true`)**: Enable `strict: true` for new TypeScript projects. For existing codebases, respect the established migration plan and do not alter compiler policy or lower strictness silently.
- **Module and target settings**: Use the project's established `module`, `moduleResolution`, and `target` settings in `tsconfig.json`. Avoid speculative changes to compiler targets or module systems.
- **Unchecked index access (`noUncheckedIndexedAccess: true`)**: Treats object and array index lookups as potentially `undefined`, requiring explicit checks before accessing properties on indexed values.
- **Exact optional properties (`exactOptionalPropertyTypes: true`)**: Distinguishes omitted optional properties from properties explicitly set to `undefined`.

## Type-aware linting

- **Type-aware rules**: Lint rules powered by `typescript-eslint` leverage the TypeScript type checker to detect subtle issues that standard linters miss, such as unhandled Promises (`@typescript-eslint/no-floating-promises`) and misused Promises in conditionals (`@typescript-eslint/no-misused-promises`).
- **Inline exceptions**: When an external library incompatibility necessitates a lint exception, use narrow, documented inline comments (`// eslint-disable-next-line <rule> -- <justification>`) rather than disabling rules for entire files.

## Compile-time type testing

- **Verification tools**: Tools such as `tsd` or `expect-type` verify that TypeScript types, generics, and inferred return types match expected shapes at compile time.
- **Application**: Useful for generic utility libraries, custom type combinators, and exported public SDK contracts where type inference is part of the API surface.

## Script discovery

Inspect `package.json` before running verification commands. Common examples:

```sh
npm run typecheck      # typically runs `tsc --noEmit`
npm run lint           # linter including TypeScript rules
```

Never assume script names or package managers; inspect the project's setup and run the appropriate commands.

## Supporting references
- [TypeScript Handbook: Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)
- [typescript-eslint Documentation](https://typescript-eslint.io/)
