import React from 'react'
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
import {
  Home,
  Search,
  Twitter,
  FileText,
  TrendingUp,
  Tags,
  BarChart3,
  Database,
  Image,
  Users,
  PieChart,
  ScrollText,
  Flame,
  Brain,
  GitCompare,
  Layers,
  Settings,
  Activity,
  BookOpen,
  GitBranch,
  MessageSquare
} from 'lucide-react'

export type ViewType =
  | 'dashboard'
  | 'statistics'
  | 'rag-search'
  // Twitter views
  | 'twitter-faceted'
  | 'twitter-media'
  | 'twitter-trends'
  | 'twitter-users'
  | 'twitter-charts'
  | 'twitter-summary'
  | 'twitter-accounts'
  // Article views
  | 'articles-faceted'
  | 'articles-trends'
  | 'articles-charts'
  | 'articles-clustering'
  // Author views
  | 'author-management'
  | 'author-analytics'
  | 'author-merge'
  // Reddit views
  | 'reddit-faceted'
  | 'reddit-trends'
  // Papers views
  | 'papers-dashboard'
  | 'papers-references'
  // Books views
  | 'books-dashboard'
  | 'books-analysis'
  // Analysis views
  | 'analysis-unified'
  | 'analysis-compare'
  | 'analysis-clustering'
  | 'topic-explorer'
  // Concept management
  | 'concept-management'
  | 'concept-graph'
  // Legacy (to be removed)
  | 'tags-organisation'
  | 'concept-organizer'

interface ModernNavigationProps {
  activeView: ViewType
  onViewChange: (view: ViewType) => void
}

const navigationItems = [
  {
    title: 'Dashboard',
    icon: Home,
    view: 'dashboard' as ViewType,
    description: 'Overview and quick access'
  },
  {
    title: 'Statistics',
    icon: BarChart3,
    view: 'statistics' as ViewType,
    description: 'Comprehensive system metrics and analytics'
  },
  {
    title: 'AI Insights',
    icon: Brain,
    items: [
      { 
        title: 'AI Search', 
        view: 'rag-search' as ViewType, 
        icon: Search,
        description: 'Search across all content'
      },
      { 
        title: 'AI Summarization', 
        view: 'twitter-summary' as ViewType, 
        icon: ScrollText,
        description: 'Generate intelligent summaries'
      }
    ]
  },
  {
    title: 'Twitter/X',
    icon: Twitter,
    items: [
      { 
        title: 'Browse Tweets', 
        view: 'twitter-faceted' as ViewType, 
        icon: FileText,
        description: 'Filter and explore tweets'
      },
      { 
        title: 'Media Gallery', 
        view: 'twitter-media' as ViewType, 
        icon: Image,
        description: 'Images and videos'
      },
      { 
        title: 'Trending Topics', 
        view: 'twitter-trends' as ViewType, 
        icon: TrendingUp,
        description: 'Hot topics and trends'
      },
      { 
        title: 'User Analysis', 
        view: 'twitter-users' as ViewType, 
        icon: Users,
        description: 'Per-user insights'
      },
      {
        title: 'Visualizations',
        view: 'twitter-charts' as ViewType,
        icon: PieChart,
        description: 'Charts and graphs'
      },
      {
        title: 'Account Manager',
        view: 'twitter-accounts' as ViewType,
        icon: Users,
        description: 'Manage monitored accounts'
      }
    ]
  },
  {
    title: 'Articles',
    icon: FileText,
    items: [
      {
        title: 'Browse Articles',
        view: 'articles-faceted' as ViewType,
        icon: FileText,
        description: 'Explore newsletters'
      },
      {
        title: 'Article Trends',
        view: 'articles-trends' as ViewType,
        icon: Flame,
        description: 'Hot topics in articles'
      },
      {
        title: 'Article Analytics',
        view: 'articles-charts' as ViewType,
        icon: BarChart3,
        description: 'Article statistics'
      },
      {
        title: 'Topic Clustering',
        view: 'articles-clustering' as ViewType,
        icon: Layers,
        description: 'Cluster articles by tags'
      }
    ]
  },
  {
    title: 'Authors',
    icon: Users,
    items: [
      {
        title: 'Manage Authors',
        view: 'author-management' as ViewType,
        icon: Users,
        description: 'View and organize article authors'
      },
      {
        title: 'Author Analytics',
        view: 'author-analytics' as ViewType,
        icon: BarChart3,
        description: 'Publishing statistics and insights'
      },
      {
        title: 'Merge Duplicates',
        view: 'author-merge' as ViewType,
        icon: GitCompare,
        description: 'Find and merge duplicate authors'
      }
    ]
  },
  {
    title: 'Reddit Posts',
    icon: MessageSquare,
    items: [
      { 
        title: 'Browse Posts', 
        view: 'reddit-faceted' as ViewType, 
        icon: FileText,
        description: 'Filter and explore Reddit posts'
      },
      { 
        title: 'Reddit Trends', 
        view: 'reddit-trends' as ViewType, 
        icon: TrendingUp,
        description: 'Trending topics on Reddit'
      }
    ]
  },
  {
    title: 'Research Papers',
    icon: BookOpen,
    items: [
      {
        title: 'Browse Papers',
        view: 'papers-dashboard' as ViewType,
        icon: BookOpen,
        description: 'Research papers analysis'
      },
      {
        title: 'References',
        view: 'papers-references' as ViewType,
        icon: Database,
        description: 'Manage paper references'
      }
    ]
  },
  {
    title: 'Book Library',
    icon: BookOpen,
    items: [
      {
        title: 'Browse Books',
        view: 'books-dashboard' as ViewType,
        icon: BookOpen,
        description: 'Personal book collection'
      },
      {
        title: 'Book Analytics',
        view: 'books-analysis' as ViewType,
        icon: BarChart3,
        description: 'Reading statistics and insights'
      }
    ]
  },
  {
    title: 'Analysis',
    icon: Brain,
    items: [
      { 
        title: 'Unified Trends', 
        view: 'analysis-unified' as ViewType, 
        icon: Activity,
        description: 'Combined insights'
      },
      { 
        title: 'Compare Sources', 
        view: 'analysis-compare' as ViewType, 
        icon: GitCompare,
        description: 'Twitter vs Articles'
      },
      {
        title: 'Topic Clustering',
        view: 'analysis-clustering' as ViewType,
        icon: Layers,
        description: 'Related topics'
      },
      {
        title: 'Topic Explorer',
        view: 'topic-explorer' as ViewType,
        icon: TrendingUp,
        description: 'Analyze topic trends and correlations'
      }
    ]
  },
  {
    title: 'Concepts',
    icon: Tags,
    items: [
      { 
        title: 'Concept Management', 
        view: 'concept-management' as ViewType, 
        icon: GitBranch,
        description: 'Manage hierarchy and organize concepts'
      },
      { 
        title: 'Concept Graph', 
        view: 'concept-graph' as ViewType, 
        icon: Layers,
        description: 'Interactive concept visualization'
      }
    ]
  }
]

export default function ModernNavigation({ activeView, onViewChange }: ModernNavigationProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <a className="mr-6 flex items-center space-x-2" href="/">
            <Database className="h-6 w-6 text-blue-600" />
            <span className="hidden font-bold sm:inline-block">
              SmartTrendTracer
            </span>
          </a>
        </div>
        
        <NavigationMenu className="mx-6 [&_[data-radix-popper-content-wrapper]]:!transform-none [&_[data-radix-popper-content-wrapper]]:!top-full">
          <NavigationMenuList>
            {navigationItems.map((item) => {
              if (item.items) {
                // Dropdown menu
                return (
                  <NavigationMenuItem key={item.title}>
                    <NavigationMenuTrigger 
                      className={cn(
                        "h-9",
                        item.items.some(i => i.view === activeView) && "bg-accent"
                      )}
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {item.title}
                    </NavigationMenuTrigger>
                    <NavigationMenuContent>
                      <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2">
                        {item.items.map((subItem) => (
                          <li key={subItem.view}>
                            <NavigationMenuLink asChild>
                              <button
                                onClick={() => onViewChange(subItem.view)}
                                className={cn(
                                  "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground w-full text-left",
                                  activeView === subItem.view && "bg-accent"
                                )}
                              >
                                <div className="flex items-center gap-2">
                                  <subItem.icon className="h-4 w-4" />
                                  <div className="text-sm font-medium leading-none">
                                    {subItem.title}
                                  </div>
                                </div>
                                <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
                                  {subItem.description}
                                </p>
                              </button>
                            </NavigationMenuLink>
                          </li>
                        ))}
                      </ul>
                    </NavigationMenuContent>
                  </NavigationMenuItem>
                )
              } else {
                // Single item
                return (
                  <NavigationMenuItem key={item.title}>
                    <Button
                      variant={activeView === item.view ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => onViewChange(item.view!)}
                      className="h-9"
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {item.title}
                    </Button>
                  </NavigationMenuItem>
                )
              }
            })}
          </NavigationMenuList>
        </NavigationMenu>

        <div className="ml-auto flex items-center space-x-4">
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <Settings className="h-4 w-4" />
            <span className="sr-only">Settings</span>
          </Button>
        </div>
      </div>
    </header>
  )
}