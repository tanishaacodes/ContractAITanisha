import * as React from "react";
import { Check } from "lucide-react";

const Checkbox = React.forwardRef(({ className = "", checked, onCheckedChange, ...props }, ref) => {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      ref={ref}
      onClick={() => onCheckedChange && onCheckedChange(!checked)}
      className={`peer h-4 w-4 shrink-0 rounded-sm border border-slate-700 bg-slate-900 ring-offset-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${checked ? 'bg-blue-600 border-blue-600' : ''} ${className}`}
      {...props}
    >
      {checked && (
        <Check className="h-4 w-4 text-white" />
      )}
    </button>
  );
});

Checkbox.displayName = "Checkbox";

export { Checkbox };
