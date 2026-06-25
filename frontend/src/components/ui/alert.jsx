import * as React from "react";

const Alert = React.forwardRef(({ className = "", variant = "default", children, ...props }, ref) => {
  const variantStyles = {
    default: "bg-slate-800 text-white border-slate-700",
    destructive: "bg-red-900/20 text-red-400 border-red-800",
    success: "bg-green-900/20 text-green-400 border-green-800"
  };

  return (
    <div
      ref={ref}
      role="alert"
      className={`relative w-full rounded-lg border p-4 ${variantStyles[variant] || variantStyles.default} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
});

Alert.displayName = "Alert";

const AlertDescription = React.forwardRef(({ className = "", ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={`text-sm [&_p]:leading-relaxed ${className}`}
      {...props}
    />
  );
});

AlertDescription.displayName = "AlertDescription";

export { Alert, AlertDescription };
