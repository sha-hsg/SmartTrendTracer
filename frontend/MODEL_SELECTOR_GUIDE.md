# Model Selector - Reusable Component Guide

## Overview
The `ModelSelector` component is a centralized, reusable AI model selection UI that eliminates code duplication across the application.

## Features
- ✅ **Single source of truth** for all available models
- ✅ **Automatic localStorage persistence** for user preferences
- ✅ **Task-based filtering** - show only relevant models
- ✅ **Consistent UI** with icons, badges, and descriptions
- ✅ **Easy to update** - add new models in one place

## Quick Start

### Basic Usage

```tsx
import ModelSelector from './ModelSelector'

function MyComponent() {
  const [selectedModel, setSelectedModel] = useState<string>('')

  return (
    <ModelSelector
      value={selectedModel}
      onValueChange={setSelectedModel}
      task="paperAnalysis"
      persist={true}
    />
  )
}
```

### With Custom Label and Description

```tsx
<ModelSelector
  value={selectedModel}
  onValueChange={setSelectedModel}
  task="paperTagSuggestion"
  label="Choose AI Model"
  description="Select the model for analyzing this paper"
  persist={true}
/>
```

### Using the Hook (Alternative Approach)

```tsx
import { useModelSelection } from './ModelSelector'

function MyComponent() {
  const { selectedModel, setSelectedModel } = useModelSelection('paperAnalysis')

  // selectedModel is automatically loaded from localStorage
  // and persisted on change
}
```

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | - | Current selected model value (required) |
| `onValueChange` | `(value: string) => void` | - | Callback when model changes (required) |
| `task` | `keyof MODEL_PRESETS` | `undefined` | Task type for filtering and defaults |
| `label` | `string` | `"AI Model"` | Label text above selector |
| `description` | `string` | `undefined` | Helper text below selector |
| `filterByTask` | `boolean` | `false` | Show only models relevant to task |
| `persist` | `boolean` | `true` | Enable localStorage persistence |
| `storageKey` | `string` | `undefined` | Custom storage key (overrides task-based) |
| `className` | `string` | `""` | Additional className for container |
| `disabled` | `boolean` | `false` | Disable the selector |

## Available Tasks

Task types defined in `src/config/models.ts`:

- `paperTagSuggestion` - For paper tag generation (default: GPT-5)
- `paperAnalysis` - For paper analysis (default: Claude 3.5 Sonnet)
- `entityExtraction` - For entity extraction (default: GPT-5)
- `articleSummarization` - For article summaries (default: Claude 3.5 Sonnet)
- `tweetAnnotation` - For tweet tagging (default: GPT-4o Mini)

## Adding New Models

Edit `/frontend/src/config/models.ts`:

```ts
export const AVAILABLE_MODELS: ModelOption[] = [
  // ... existing models
  {
    value: 'new-model',
    label: 'New Model',
    description: 'Description here',
    icon: Sparkles,  // lucide-react icon
    iconColor: 'text-blue-600',
    badge: 'Fast',
    badgeVariant: 'secondary'
  }
]
```

## localStorage Keys

The component automatically generates localStorage keys:
- `paperTagSuggestion` → `preferredPaperTagSuggestionModel`
- `paperAnalysis` → `preferredPaperAnalysisModel`
- `entityExtraction` → `preferredEntityExtractionModel`
- etc.

## Migration Checklist

When migrating an existing component:

1. ✅ Import `ModelSelector`
2. ✅ Remove hardcoded `Select` component
3. ✅ Simplify state: `useState<string>('')` (no initial value needed)
4. ✅ Remove manual localStorage logic
5. ✅ Replace with `<ModelSelector />`

### Before (Old Way)

```tsx
const [selectedModel, setSelectedModel] = useState<string>(() => {
  return localStorage.getItem('preferredPaperAnalysisModel') || 'claude-3.5-sonnet'
})

useEffect(() => {
  localStorage.setItem('preferredPaperAnalysisModel', selectedModel)
}, [selectedModel])

return (
  <Select value={selectedModel} onValueChange={setSelectedModel}>
    <SelectTrigger>...</SelectTrigger>
    <SelectContent>
      <SelectItem value="gpt-5">GPT-5</SelectItem>
      <SelectItem value="claude-3.5-sonnet">Claude 3.5</SelectItem>
      {/* ... 10 more hardcoded items ... */}
    </SelectContent>
  </Select>
)
```

### After (New Way)

```tsx
const [selectedModel, setSelectedModel] = useState<string>('')

return (
  <ModelSelector
    value={selectedModel}
    onValueChange={setSelectedModel}
    task="paperAnalysis"
    persist={true}
  />
)
```

## Components Already Migrated

- ✅ `PaperTagSuggestionModal.tsx` - Paper tag suggestions
- ✅ `PaperAnalysisPanel.tsx` - Paper analysis generation

## Components To Migrate

- [ ] `EntityAnnotationReviewModern.tsx` - Entity extraction
- [ ] `SummarizationModern.tsx` - Article summarization
- [ ] `ArticleTagSuggestionModalModern.tsx` - Article tag suggestions
- [ ] Any other components with model selection

## Benefits

### Before (Scattered Approach)
- Model list duplicated in 5+ files
- Inconsistent UI across components
- Adding new model = update 5+ files
- Manual localStorage in each component
- Hard to maintain consistency

### After (Centralized Approach)
- Model list defined ONCE in `models.ts`
- Consistent UI everywhere
- Adding new model = update 1 file
- Automatic localStorage handling
- Easy to maintain and extend

## Example: Complete Implementation

```tsx
import React, { useState } from 'react'
import ModelSelector from './ModelSelector'
import { Button } from '@/components/ui/button'

export default function MyAnalysisComponent({ paperId }: { paperId: string }) {
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const analyzeWithModel = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/papers/${paperId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      })
      // Handle response...
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <ModelSelector
        value={selectedModel}
        onValueChange={setSelectedModel}
        task="paperAnalysis"
        label="AI Model"
        description="Choose the model for analysis"
        persist={true}
      />

      <Button
        onClick={analyzeWithModel}
        disabled={!selectedModel || loading}
      >
        {loading ? 'Analyzing...' : 'Analyze Paper'}
      </Button>
    </div>
  )
}
```

## Backend Integration

The `selectedModel` value can be passed directly to backend endpoints:

```tsx
const response = await axios.post(
  `http://localhost:8000/api/papers/${paperId}/analyses/generate`,
  {
    analysis_type: 'summary',
    model: selectedModel  // Pass directly - backend handles mapping
  }
)
```

Backend (FastAPI) receives this and uses LiteLLM's model mapping:

```python
# Backend automatically maps:
# "claude-3.5-sonnet" → "anthropic/claude-sonnet-4-20250514"
# "gpt-5" → "openai/gpt-5-2025-08-07"
# etc.
```

## Notes

- The component is fully TypeScript typed
- Icons from `lucide-react` are used consistently
- Badge variants match shadcn/ui design system
- Storage keys follow naming convention: `preferred{Task}Model`
