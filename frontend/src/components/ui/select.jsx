import * as React from "react";

const Select = React.forwardRef(({ children, value, onValueChange, disabled, ...props }, ref) => {
  return (
    <select
      ref={ref}
      value={value}
      onChange={(e) => onValueChange && onValueChange(e.target.value)}
      disabled={disabled}
      className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
      {...props}
    >
      {children}
    </select>
  );
});

Select.displayName = "Select";

const SelectTrigger = ({ children, ...props }) => children;
const SelectValue = ({ placeholder }) => <option value="">{placeholder}</option>;
const SelectContent = ({ children }) => <>{children}</>;
const SelectItem = ({ value, children }) => <option value={value}>{children}</option>;

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
