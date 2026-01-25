/**
 * Component for displaying tags with concept information
 */
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  TagWithConcept, 
  TagConcept, 
  getEntityTypeConfig, 
  formatTagDisplay 
} from '../types/tagConcept';
import { cn } from '@/lib/utils';

interface TagConceptDisplayProps {
  tag: TagWithConcept | TagConcept;
  onClick?: (tag: TagWithConcept | TagConcept) => void;
  onRemove?: (tag: TagWithConcept | TagConcept) => void;
  showIcon?: boolean;
  showEntityType?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'secondary' | 'outline' | 'destructive';
  className?: string;
}

/**
 * Display a single tag with concept information
 */
export function TagConceptDisplay({
  tag,
  onClick,
  onRemove,
  showIcon = true,
  showEntityType = false,
  size = 'md',
  variant = 'default',
  className
}: TagConceptDisplayProps) {
  const config = getEntityTypeConfig(tag.entity_type);
  const displayName = formatTagDisplay(tag);

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  };

  const badge = (
    <Badge
      variant={variant}
      className={cn(
        sizeClasses[size],
        'cursor-pointer transition-all hover:scale-105',
        onClick && 'hover:bg-opacity-80',
        className
      )}
      style={{
        backgroundColor: tag.color || (tag.entity_type ? config.color : undefined),
        color: tag.color || tag.entity_type ? 'white' : undefined
      }}
      onClick={onClick ? () => onClick(tag) : undefined}
    >
      {showIcon && config.icon && (
        <span className="mr-1">{config.icon}</span>
      )}
      {displayName}
      {showEntityType && tag.entity_type && (
        <span className="ml-1 opacity-70 text-xs">
          ({tag.entity_type})
        </span>
      )}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(tag);
          }}
          className="ml-1 hover:text-red-300"
        >
          ×
        </button>
      )}
    </Badge>
  );

  // Add tooltip if we have additional information
  if ('concept_id' in tag && (tag.concept_id || tag.slug)) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {badge}
          </TooltipTrigger>
          <TooltipContent>
            <div className="text-sm space-y-1">
              {tag.concept_id && (
                <div>
                  <span className="font-semibold">ID:</span> {tag.concept_id}
                </div>
              )}
              {tag.slug && (
                <div>
                  <span className="font-semibold">Slug:</span> {tag.slug}
                </div>
              )}
              {tag.entity_type && (
                <div>
                  <span className="font-semibold">Type:</span> {tag.entity_type}
                </div>
              )}
              {'tag_type' in tag && (
                <div>
                  <span className="font-semibold">Source:</span> {tag.tag_type}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return badge;
}

interface TagConceptListProps {
  tags: (TagWithConcept | TagConcept)[];
  onTagClick?: (tag: TagWithConcept | TagConcept) => void;
  onTagRemove?: (tag: TagWithConcept | TagConcept) => void;
  showIcons?: boolean;
  showEntityTypes?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'secondary' | 'outline' | 'destructive';
  className?: string;
  wrapperClassName?: string;
}

/**
 * Display a list of tags with concept information
 */
export function TagConceptList({
  tags,
  onTagClick,
  onTagRemove,
  showIcons = true,
  showEntityTypes = false,
  size = 'md',
  variant = 'default',
  className,
  wrapperClassName
}: TagConceptListProps) {
  if (!tags || tags.length === 0) {
    return (
      <div className={cn('text-muted-foreground text-sm', wrapperClassName)}>
        No tags
      </div>
    );
  }

  return (
    <div className={cn('flex flex-wrap gap-2', wrapperClassName)}>
      {tags.map((tag, index) => (
        <TagConceptDisplay
          key={`${tag.concept_id || tag.slug || index}`}
          tag={tag}
          onClick={onTagClick}
          onRemove={onTagRemove}
          showIcon={showIcons}
          showEntityType={showEntityTypes}
          size={size}
          variant={variant}
          className={className}
        />
      ))}
    </div>
  );
}

interface TagConceptCloudProps {
  tags: Array<(TagWithConcept | TagConcept) & { count?: number }>;
  onTagClick?: (tag: TagWithConcept | TagConcept) => void;
  showCounts?: boolean;
  maxSize?: number;
  minSize?: number;
  className?: string;
}

/**
 * Display a tag cloud with varying sizes based on usage
 */
export function TagConceptCloud({
  tags,
  onTagClick,
  showCounts = true,
  maxSize = 2,
  minSize = 0.8,
  className
}: TagConceptCloudProps) {
  // Calculate size scale
  const counts = tags.map(t => t.count || t.usage_count || 1);
  const maxCount = Math.max(...counts);
  const minCount = Math.min(...counts);
  const range = maxCount - minCount || 1;

  const getSize = (count: number) => {
    const normalized = (count - minCount) / range;
    return minSize + (normalized * (maxSize - minSize));
  };

  return (
    <div className={cn('flex flex-wrap gap-3 items-center', className)}>
      {tags.map((tag, index) => {
        const count = tag.count || tag.usage_count || 1;
        const size = getSize(count);
        
        return (
          <div
            key={`${tag.concept_id || tag.slug || index}`}
            className="inline-flex items-center gap-1"
            style={{ fontSize: `${size}rem` }}
          >
            <TagConceptDisplay
              tag={tag}
              onClick={onTagClick}
              showIcon={size > 1}
              className="text-current"
            />
            {showCounts && (
              <span className="text-muted-foreground text-xs">
                ({count})
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}