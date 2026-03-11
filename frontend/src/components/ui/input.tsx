import { clsx } from "clsx"
import { InputHTMLAttributes, forwardRef } from "react"

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={clsx(
        "w-full px-3 py-2 bg-inp border bd2 rounded-lg t1 placeholder-gray-400",
        "focus:outline-none focus:ring-2 focus:ring-archon-500 focus:border-transparent",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className
      )}
      {...props}
    />
  )
)
Input.displayName = "Input"
