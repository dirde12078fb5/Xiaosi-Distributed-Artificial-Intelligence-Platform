// vitest 全局 setup：node 环境给 client.ts::resolveToken() 它读的 window 桩。
if (typeof (globalThis as { window?: unknown }).window === "undefined") {
  (globalThis as unknown as { window: Record<string, unknown> }).window = {
    __MILOCO_TOKEN__: undefined,
  };
}
