import { clsx } from "clsx"
import { LabelHTMLAttributes } from "react"

export function Label({ className, children, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label className={clsx("block text-sm font-medium text-gray-300 mb-1", className)} {...props}>
      {children}
    </label>
  )
}
