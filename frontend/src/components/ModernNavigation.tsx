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
  Upload,
  Filter
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
  // Article views
  | 'articles-faceted' 
  | 'articles-trends'
  | 'articles-charts'
  // Papers views
  | 'papers-dashboard'
  // Analysis views
  | 'analysis-unified'
  | 'analysis-compare'
  | 'analysis-clustering'
  // Tag management
  | 'tags-organisation'

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
    description: 'System metrics and analytics'
  },
  {
    title: 'AI Search',
    icon: Search,
    view: 'rag-search' as ViewType,
    description: 'Search across all content'
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
        title: 'AI Summaries', 
        view: 'twitter-summary' as ViewType, 
        icon: ScrollText,
        description: 'Generated summaries'
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
      }
    ]
  },
  {
    title: 'Papers',
    icon: BookOpen,
    view: 'papers-dashboard' as ViewType,
    description: 'Research papers analysis'
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
      }
    ]
  },
  {
    title: 'Tags',
    icon: Tags,
    view: 'tags-organisation' as ViewType,
    description: 'Manage tag ontology'
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
        
        <NavigationMenu className="mx-6">
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