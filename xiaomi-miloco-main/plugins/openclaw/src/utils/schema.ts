import { Ajv, type ErrorObject } from "ajv";
import type { FromSchema } from "json-schema-to-ts";

// ─── Public types ──────────────────────────────────────────────────────────────

/** A single validation failure with the field path and a human-readable message. */
export type ParseIssue = {
  /** Dot-notation path to the offending field, e.g. `"data.timeout"`. */
  path: string;
  /** Human-readable description of the violation. */
  message: string;
};

/** Structured error returned by {@link Parser.safeParse} or attached to a thrown {@link ValidationError}. */
export type ParseError = {
  issues: ParseIssue[];
  /** Multi-line summary ready to display to users. */
  message: string;
};

export type ParseSuccess<T> = { success: true; data: T };
export type ParseFailure = { success: false; error: ParseError };
export type ParseResult<T> = ParseSuccess<T> | ParseFailure;

/** Thrown by {@link Parser.parse} on validation failure. Extends `Error` with structured `issues`. */
export class ValidationError extends Error {
  readonly issues: ParseIssue[];
  constructor(err: ParseError) {
    super(err.message);
    this.name = "ValidationError";
    this.issues = err.issues;
  }
}

export type Parser<T> = {
  /**
   * Validate `raw`, fill in schema defaults, and return the typed value.
   *
   * Throws a {@link ValidationError} on failure — the error contains both
   * a human-readable `.message` and structured `.issues` for programmatic use.
   */
  parse(raw: unknown): T;

  /**
   * Validate `raw` without ever throwing. Returns a discriminated union.
   *
   * @example
   * const result = parser.safeParse(input)
   * if (result.success) {
   *   use(result.data)
   * } else {
   *   for (const { path, message } of result.error.issues) {
   *     console.error(`${path}: ${message}`)
   *   }
   * }
   */
  safeParse(raw: unknown): ParseResult<T>;
};

// ─── Internal helpers ──────────────────────────────────────────────────────────

/** Convert a JSON Pointer (e.g. `/meta/firmware`) to a dot path (e.g. `data.meta.firmware`). */
function toDotPath(instancePath: string): string {
  if (!instancePath) {
    return "data";
  }
  return `data${instancePath.replace(/\//g, ".")}`;
}

function formatIssues(errors: ErrorObject[]): ParseIssue[] {
  return errors.map((e) => {
    const base = toDotPath(e.instancePath);
    // additionalProperties errors don't include the field name in instancePath —
    // extract it from params so the message is actionable.
    if (e.keyword === "additionalProperties") {
      const field = (e.params as { additionalProperty: string })
        .additionalProperty;
      return {
        path: `${base}.${field}`,
        message: `unknown property: ${field}`,
      };
    }
    return { path: base, message: e.message ?? e.keyword };
  });
}

function buildError(name: string, errors: ErrorObject[]): ParseError {
  const issues = formatIssues(errors);
  const lines = issues.map((i) => `${i.path}: ${i.message}`);
  return {
    issues,
    message: `${name} validation failed:\n  ${lines.join("\n  ")}`,
  };
}

// ─── Public API ────────────────────────────────────────────────────────────────

/**
 * Build a type-safe parser from a JSON Schema defined `as const`.
 *
 * The output type is inferred directly from the schema — no manual annotations needed.
 * Defaults declared in the schema are automatically filled in on each parse call,
 * without mutating the original input.
 *
 * @example
 * const schema = {
 *   type: 'object',
 *   required: ['id'],
 *   properties: {
 *     id:    { type: 'string' },
 *     count: { type: 'integer', default: 0 },
 *   },
 *   additionalProperties: false,
 * } as const
 *
 * const parser = createParser(schema)
 *
 * // Destructure for a named parse function:
 * const { parse: parseMySchema, safeParse: safeParseMySchema } = createParser(schema)
 *
 * // parse — throws ValidationError on failure
 * const value = parser.parse(rawInput)
 *
 * // safeParse — never throws
 * const result = parser.safeParse(rawInput)
 * if (result.success) {
 *   use(result.data)
 * } else {
 *   console.error(result.error.message)
 * }
 */
export function createParser<const S extends object>(
  schema: S,
  options?: {
    /** Display name used in error messages. Defaults to `schema.title ?? "Schema"`. */
    name?: string;
  },
): Parser<FromSchema<S>> {
  const name =
    options?.name ?? (schema as { title?: string }).title ?? "Schema";

  // Each parser gets its own Ajv instance to avoid cross-schema conflicts.
  const ajv = new Ajv({
    useDefaults: true,
    coerceTypes: false,
    allErrors: true,
  });
  const validate = ajv.compile(schema);

  function run(raw: unknown): { data: unknown; error?: ParseError } {
    // Clone to prevent ajv useDefaults from mutating the caller's original object.
    const data = structuredClone(raw);
    return validate(data)
      ? { data }
      : { data, error: buildError(name, validate.errors ?? []) };
  }

  return {
    parse(raw) {
      const { data, error } = run(raw);
      if (error) {
        throw new ValidationError(error);
      }
      return data as FromSchema<S>;
    },
    safeParse(raw) {
      const { data, error } = run(raw);
      if (error) {
        return { success: false, error };
      }
      return { success: true, data: data as FromSchema<S> };
    },
  };
}
