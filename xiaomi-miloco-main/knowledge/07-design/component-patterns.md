# 组件原型

> 设计 SSOT (Mi Console v3 组件原型)
> 写新模块时**直接复制粘贴这些原型**——它们已被锁进视觉契约,不要再发明新变体。

---

## 1. Card(业务最常用容器)

**默认形态**(自带 padding):

```tsx
<section
  className="rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6 anim-in"
  aria-labelledby="my-section-title"
>
  <div className="flex items-baseline justify-between gap-3 mb-4 flex-wrap">
    <h2
      id="my-section-title"
      className="text-title text-text-primary inline-flex items-baseline gap-2"
    >
      标题
      {/* dev tool 风 mono 副标 */}
      <span className="text-caption-mono text-text-tertiary font-normal">
        slug_or_count
      </span>
    </h2>
  </div>
  {/* 内容 */}
</section>
```

**列表型变体**(无内边距,把 padding 让给 row):

```tsx
<section className="rounded-xl bg-bg-secondary border border-border shadow-sm anim-in">
  <div className="flex items-baseline justify-between px-5 pt-4 pb-3">
    <h2 className="text-title">...</h2>
  </div>
  <ul className="divide-y divide-border">
    <li className="text-body px-5 py-2.5 hover:bg-bg-tertiary transition-colors">
      ...
    </li>
  </ul>
</section>
```

---

## 2. Buttons

### 2.1 Primary CTA(主操作,每页 ≤1)

```tsx
<button
  type="button"
  className="text-title px-5 py-2 rounded-md bg-brand-primary text-white hover:bg-brand-accent disabled:opacity-50 transition-colors"
>
  发送
</button>
```

### 2.2 Secondary(次操作,默认按钮)

```tsx
<button
  type="button"
  className="text-caption px-4 py-1.5 rounded-md bg-bg-primary text-text-secondary hover:text-text-primary border border-border hover:border-border-strong transition-colors"
>
  取消
</button>
```

### 2.3 Ghost(行内文字按钮)

```tsx
<button
  type="button"
  className="text-caption text-text-secondary hover:text-text-primary transition-colors"
>
  跳转 →
</button>
```

### 2.4 Danger Solid(危险确认,二次)

```tsx
<button
  type="button"
  className="px-5 py-2 rounded-md bg-error text-white hover:bg-error/90 transition-colors"
>
  解除绑定
</button>
```

### 2.5 Soft Brand(被选中 / hover-active 反馈)

```tsx
<button className="px-3.5 py-1.5 rounded-md bg-brand-soft text-brand-primary hover:bg-brand-primary hover:text-white border border-transparent transition-colors">
  打开
</button>
```

### 2.6 Icon Button(icon-only,32×32 标准框)

```tsx
<button
  type="button"
  aria-label="刷新"
  className="w-8 h-8 inline-flex items-center justify-center rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
>
  <IconChevronRight />
</button>
```

---

## 3. Status Dot(状态点 + 半透明光环)

**统一替代 chip / badge** 表达状态。规格:

- **5px 圆点**(`width:5; height:5`)+ `box-shadow: 0 0 0 3px var(--color-{tone}-bg)`
- 永远在 `inline-flex items-center gap-2` 容器内,后面跟 `<span>` 状态文字
- 颜色映射:`ok=success` / `info=info` / `warn=warning` / `danger=error` / `brand=brand-primary`

```tsx
<span className="inline-flex items-center gap-2 text-caption text-text-secondary">
  <span
    aria-hidden
    className="rounded-full bg-success"
    style={{
      width: 5,
      height: 5,
      boxShadow: "0 0 0 3px var(--color-success-bg)",
    }}
  />
  正在替你看
</span>
```

或用工具类:

```tsx
<span className="inline-flex items-center gap-2 text-caption text-text-secondary">
  <span aria-hidden className="status-dot status-dot-ok" />
  正在替你看
</span>
```

---

## 4. Drawer(右侧抽屉,设置 / 详情)

```tsx
<aside
  aria-label="设置"
  aria-modal="true"
  role="dialog"
  className={`fixed top-0 right-0 bottom-0 w-full md:w-[420px] max-w-md bg-bg-secondary border-l border-border flex flex-col z-[60] transition-transform ${
    open ? "translate-x-0" : "translate-x-full"
  }`}
  style={{
    transitionDuration: "var(--duration-slow)",
    transitionTimingFunction: "var(--easing-emphasized)",
    boxShadow: open ? "var(--shadow-lg)" : "none",
  }}
>
  <header
    className="flex items-center justify-between px-5 border-b border-border"
    style={{ minHeight: 64 }}
  >
    <h2 className="text-title font-semibold">设置</h2>
    <CloseButton onClick={onClose} />
  </header>
  <div className="flex-1 overflow-y-auto px-5 py-4">{/* 内容 */}</div>
</aside>
```

> 所有 drawer 一律 **`max-w-md`**(448px)。

---

## 5. Dialog(居中弹窗)

```tsx
<div
  className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 anim-in"
  onClick={onClose}
>
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="dialog-title"
    className="w-[90%] max-w-md bg-bg-secondary border border-border rounded-2xl shadow-lg p-6"
    onClick={(e) => e.stopPropagation()}
  >
    <h2 id="dialog-title" className="text-title font-semibold mb-3">
      标题
    </h2>
    {/* 内容 */}
    <div className="mt-6 flex justify-end gap-2">
      <SecondaryButton onClick={onClose}>取消</SecondaryButton>
      <PrimaryButton onClick={onConfirm}>确定</PrimaryButton>
    </div>
  </div>
</div>
```

mobile bottom-sheet 变体:`items-end md:items-center` + `rounded-t-2xl md:rounded-2xl`。

---

## 6. Toast / Inline alert

调用方:

```ts
import { toast } from "@/components/Toast";
toast("已暂停", "ok" | "info" | "warn" | "danger");
```

inline 警告条(用于页面顶部,如 Mock 提示):

```tsx
<div className="text-body rounded-lg bg-warning-bg border border-warning/30 text-warning px-4 py-2.5">
  <span className="font-medium">⚠ Mock 数据</span>
  <span className="ml-2 text-warning/80">backend 还没接入真实计费</span>
</div>
```

---

## 7. Chip / Pill(标签 / 预设)

> ⚠️ 不要与 Status Dot 混淆 —— chip 用于**可点击的预设/筛选**,**不是状态信号**。

```tsx
<button className="text-caption px-2.5 py-1 rounded-full bg-bg-tertiary text-text-secondary hover:bg-brand-soft hover:text-brand-primary transition-colors">
  客厅有人吗
</button>
```

---

## 8. Source Tag(dev tool 风 mono 标签)

用于 ActivityFeed / 日志类列表,把 source 类型显式打出来:

```tsx
<span className="text-caption-mono justify-self-start px-2 py-0.5 rounded bg-brand-soft text-brand-primary">
  rule_log
</span>
```

色映射:

| source       | 容器             | 文字                  |
| ------------ | ---------------- | --------------------- |
| `rule`       | `bg-brand-soft`  | `text-brand-primary`  |
| `perception` | `bg-bg-tertiary` | `text-text-secondary` |
| `alert`      | `bg-error-bg`    | `text-error`          |

---

## 9. Switch / Toggle(role=switch)

```tsx
<button
  type="button"
  role="switch"
  aria-checked={active}
  onClick={() => onToggle(!active)}
  className={`relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:outline-none ${
    active ? "bg-brand-primary" : "bg-bg-tertiary border border-border"
  }`}
>
  <span
    className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
      active ? "translate-x-5" : "translate-x-0"
    }`}
  />
</button>
```

---

## 10. TabPanel:Loading / Error 占位

写在 main 容器内,与卡片共用 `rounded-xl bg-bg-secondary` 形态:

```tsx
<div
  className="rounded-xl bg-bg-secondary border border-border shadow-sm p-12 text-center text-text-secondary anim-in"
  role="status" aria-live="polite"
>
  <div className="inline-flex items-center gap-2">
    <span className="inline-block w-2 h-2 rounded-full bg-text-tertiary animate-pulse" />
    正在读家里的设备…
  </div>
</div>

<div
  className="rounded-xl bg-bg-secondary border border-error shadow-sm p-8 text-center anim-in"
  role="alert"
>
  <div className="text-title text-error mb-3 font-normal">加载设备列表失败</div>
  <button
    type="button"
    onClick={onRetry}
    className="text-body px-4 py-2 rounded-lg bg-bg-primary border border-border text-text-secondary hover:text-text-primary"
  >重试</button>
</div>
```
