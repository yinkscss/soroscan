import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { AlertCircle, CheckCircle2, Info, XCircle, X } from "lucide-react"
import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm grid grid-cols-[auto_1fr_auto] gap-3 items-start [&>svg]:size-5",
  {
    variants: {
      variant: {
        info: "bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800",
        success: "bg-green-50 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
        warning: "bg-yellow-50 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
        error: "bg-red-50 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800",
      },
    },
    defaultVariants: {
      variant: "info",
    },
  }
)

const variantIcons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertCircle,
  error: XCircle,
}

interface AlertProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {
  title?: string
  description?: string
  onDismiss?: () => void
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = "info", title, description, onDismiss, ...props }, ref) => {
    const Icon = variantIcons[variant || "info"]

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        <Icon className="mt-0.5" aria-hidden="true" />
        <div className="flex flex-col gap-1">
          {title && <h5 className="font-semibold leading-none tracking-tight">{title}</h5>}
          {description && <div className="text-sm opacity-90">{description}</div>}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Dismiss alert"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
    )
  }
)
Alert.displayName = "Alert"

export { Alert, alertVariants }