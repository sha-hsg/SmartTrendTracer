import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

const tagBadgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Default tag style - light blue background with blue text
        default: "bg-blue-100 text-blue-700 hover:bg-blue-200",
        
        // AI suggested tags - purple theme
        ai: "bg-purple-100 text-purple-700 hover:bg-purple-200",
        
        // Similar to existing tags - green theme
        similar: "bg-green-100 text-green-700 hover:bg-green-200",
        
        // Manual tags - default blue
        manual: "bg-blue-100 text-blue-700 hover:bg-blue-200",
        
        // Entity tags - amber theme
        entity: "bg-amber-100 text-amber-700 hover:bg-amber-200",
        
        // New/proposed tags - indigo theme
        new: "bg-indigo-100 text-indigo-700 hover:bg-indigo-200",
        
        // Trending tags - red theme
        trending: "bg-red-100 text-red-700 hover:bg-red-200",
        
        // Neutral/system tags
        system: "bg-gray-100 text-gray-700 hover:bg-gray-200",
      },
      size: {
        sm: "text-xs px-2 py-0.5",
        default: "text-xs px-2.5 py-0.5",
        lg: "text-sm px-3 py-1",
      },
      removable: {
        true: "pr-1.5",
        false: "",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      removable: false,
    },
  }
)

export interface TagBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof tagBadgeVariants> {
  onRemove?: () => void
  count?: number
  icon?: React.ReactNode
}

const TagBadge = React.forwardRef<HTMLSpanElement, TagBadgeProps>(
  ({ className, variant, size, removable, onRemove, count, icon, children, ...props }, ref) => {
    return (
      <span
        className={cn(tagBadgeVariants({ variant, size, removable }), className)}
        ref={ref}
        {...props}
      >
        {icon && <span className="mr-0.5">{icon}</span>}
        {children}
        {count !== undefined && count > 0 && (
          <span className="ml-1 rounded-full bg-white/20 px-1.5 py-0 text-[10px] font-semibold">
            {count}
          </span>
        )}
        {removable && onRemove && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
            className="ml-0.5 rounded-full p-0.5 hover:bg-white/20 focus:outline-none"
            aria-label="Remove tag"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </span>
    )
  }
)
TagBadge.displayName = "TagBadge"

export { TagBadge, tagBadgeVariants }