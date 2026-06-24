/** 通用分段控件（tab 风格）。用于用量页的周期切换与时间粒度切换。 */
export function Segmented<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: { key: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  ariaLabel: string;
}) {
  return (
    <div
      className="flex gap-1 bg-bg-primary rounded-lg p-1"
      role="tablist"
      aria-label={ariaLabel}
    >
      {options.map((o) => {
        const on = value === o.key;
        return (
          <button
            key={o.key}
            type="button"
            role="tab"
            aria-selected={on}
            onClick={() => onChange(o.key)}
            className={`text-caption px-3 py-1 rounded-lg transition-colors ${
              on
                ? "bg-bg-secondary text-text-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
