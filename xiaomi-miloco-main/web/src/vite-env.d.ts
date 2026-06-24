/// <reference types="vite/client" />

// 由 vite.config.ts 的 define 注入：构建版本号（build 用 package.json，dev 用 git describe）
declare const __APP_VERSION__: string;
