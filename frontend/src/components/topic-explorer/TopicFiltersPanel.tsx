import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Hash,
  Twitter,
  FileText,
  BookOpen,
  ChevronDown,
  Check,
  X,
  Search
} from 'lucide-react'
import { Topic, DATE_PRESETS } from './types'

interface TopicFiltersPanelProps {
  selectedTopics: Topic[]
  availableTopics: Topic[]
  topicsLoading: boolean
  sourceTweets: boolean
  sourceArticles: boolean
  sourcePapers: boolean
  datePreset: string
  granularity: string
  onToggleTopic: (topic: Topic) => void
  onRemoveTopic: (topicId: string) => void
  onSourceTweetsChange: (checked: boolean) => void
  onSourceArticlesChange: (checked: boolean) => void
  onSourcePapersChange: (checked: boolean) => void
  onDatePresetChange: (value: string) => void
  onGranularityChange: (value: string) => void
}

export default function TopicFiltersPanel({
  selectedTopics,
  availableTopics,
  topicsLoading,
  sourceTweets,
  sourceArticles,
  sourcePapers,
  datePreset,
  granularity,
  onToggleTopic,
  onRemoveTopic,
  onSourceTweetsChange,
  onSourceArticlesChange,
  onSourcePapersChange,
  onDatePresetChange,
  onGranularityChange,
}: TopicFiltersPanelProps) {
  const [topicSearchOpen, setTopicSearchOpen] = useState(false)
  const [topicSearchQuery, setTopicSearchQuery] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  // Reset highlighted index when search changes
  useEffect(() => {
    setHighlightedIndex(-1)
  }, [topicSearchQuery])

  // Filter available topics by search
  const filteredTopics = useMemo(() => {
    if (!topicSearchQuery) return availableTopics.slice(0, 20)
    const query = topicSearchQuery.toLowerCase()
    return availableTopics
      .filter(t => t.name.toLowerCase().includes(query))
      .slice(0, 20)
  }, [availableTopics, topicSearchQuery])

  // Handle keyboard navigation in topic search
  const handleTopicSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev =>
          prev < filteredTopics.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredTopics.length) {
          onToggleTopic(filteredTopics[highlightedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setTopicSearchOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Topic Selector */}
        <div className="space-y-2">
          <Label>Topics (select up to 10)</Label>
          <div className="flex flex-wrap gap-2 mb-2">
            {selectedTopics.map(topic => (
              <Badge
                key={topic.id}
                variant="secondary"
                className="flex items-center gap-1 px-3 py-1"
              >
                <span style={{ color: topic.color }}>{topic.name}</span>
                <button
                  onClick={() => onRemoveTopic(topic.id)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {selectedTopics.length === 0 && (
              <span className="text-sm text-muted-foreground">No topics selected</span>
            )}
          </div>
          <Popover open={topicSearchOpen} onOpenChange={setTopicSearchOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  Add topics...
                </span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[400px] p-0" align="start">
              <div className="flex flex-col">
                {/* Search Input */}
                <div className="flex items-center border-b px-3">
                  <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
                  <input
                    type="text"
                    placeholder="Search topics... (up/down to navigate, Enter to select)"
                    value={topicSearchQuery}
                    onChange={(e) => setTopicSearchQuery(e.target.value)}
                    onKeyDown={handleTopicSearchKeyDown}
                    className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
                    autoFocus
                  />
                </div>
                {/* Topic List */}
                <div className="max-h-[300px] overflow-y-auto p-1">
                  {topicsLoading ? (
                    <p className="py-6 text-center text-sm text-muted-foreground">Loading topics...</p>
                  ) : filteredTopics.length === 0 ? (
                    <p className="py-6 text-center text-sm text-muted-foreground">No topics found.</p>
                  ) : (
                    <>
                      <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">Popular Topics</p>
                      {filteredTopics.map((topic, index) => (
                        <div
                          key={topic.id}
                          onClick={() => onToggleTopic(topic)}
                          className={`flex cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground ${
                            index === highlightedIndex ? 'bg-accent text-accent-foreground' : ''
                          }`}
                        >
                          <span className="flex items-center gap-2">
                            {selectedTopics.find(t => t.id === topic.id) ? (
                              <Check className="h-4 w-4 text-primary" />
                            ) : (
                              <Hash className="h-4 w-4 text-muted-foreground" />
                            )}
                            {topic.name}
                          </span>
                          <Badge variant="outline" className="ml-2">
                            {topic.count}
                          </Badge>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>

        {/* Source Types */}
        <div className="space-y-2">
          <Label>Content Sources</Label>
          <div className="flex gap-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="source-tweets"
                checked={sourceTweets}
                onCheckedChange={(checked) => onSourceTweetsChange(checked as boolean)}
              />
              <label htmlFor="source-tweets" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                <Twitter className="h-4 w-4 text-blue-500" />
                Tweets
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="source-articles"
                checked={sourceArticles}
                onCheckedChange={(checked) => onSourceArticlesChange(checked as boolean)}
              />
              <label htmlFor="source-articles" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                <FileText className="h-4 w-4 text-purple-500" />
                Articles
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="source-papers"
                checked={sourcePapers}
                onCheckedChange={(checked) => onSourcePapersChange(checked as boolean)}
              />
              <label htmlFor="source-papers" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                <BookOpen className="h-4 w-4 text-green-500" />
                Papers
              </label>
            </div>
          </div>
        </div>

        {/* Date Range and Granularity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Time Period</Label>
            <Select value={datePreset} onValueChange={onDatePresetChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DATE_PRESETS.map(preset => (
                  <SelectItem key={preset.days} value={preset.days.toString()}>
                    {preset.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Granularity</Label>
            <Select value={granularity} onValueChange={onGranularityChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="day">Daily</SelectItem>
                <SelectItem value="week">Weekly</SelectItem>
                <SelectItem value="month">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
