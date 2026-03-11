import { clsx } from "clsx"
import { TextareaHTMLAttributes, forwardRef } from "react"

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={clsx(
        "w-full px-3 py-2 bg-inp border bd2 rounded-lg t1 placeholder-gray-400",
        "focus:outline-none focus:ring-2 focus:ring-archon-500 focus:border-transparent resize-none",
        className
      )}
      {...props}
    />
  )
)
Textarea.displayName = "Textarea"
