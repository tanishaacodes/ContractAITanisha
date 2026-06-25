import * as React from "react";

const RadioGroup = ({ value, onValueChange, children, ...props }) => {
  return (
    <div role="radiogroup" {...props}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            groupValue: value,
            onGroupChange: onValueChange
          });
        }
        return child;
      })}
    </div>
  );
};

const RadioGroupItem = ({ value, id, groupValue, onGroupChange, ...props }) => {
  const isChecked = groupValue === value;

  return (
    <input
      type="radio"
      id={id}
      value={value}
      checked={isChecked}
      onChange={() => onGroupChange && onGroupChange(value)}
      className="h-4 w-4 border-slate-700 text-blue-600 focus:ring-blue-500"
      {...props}
    />
  );
};

RadioGroup.displayName = "RadioGroup";
RadioGroupItem.displayName = "RadioGroupItem";

export { RadioGroup, RadioGroupItem };
