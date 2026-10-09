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
  ScrollText,
  Flame,
  Brain,
  Layers,
  Columns,
  BookOpen,
  GitBranch,
  FileSearch,
  Library,
  LineChart,
  Rss,
  Newspaper,
  BookOpenCheck
} from 'lucide-react'
import ThemeToggle from './ThemeToggle'

export type ViewType =
  | 'dashboard'
  | 'statistics'
  | 'rag-search'
  | 'weekly-digest'
  | 'paper-qa'
  // Twitter views
  | 'twitter-faceted'
  | 'twitter-media'
  | 'twitter-users'
  | 'twitter-summary'
  | 'twitter-accounts'
  | 'twitter-deck'
  // Article views
  | 'articles-faceted'
  | 'articles-trends'
  // Author views
  | 'author-management'
  // Papers views
  | 'papers-dashboard'
  | 'papers-references'
  | 'papers-feed'
  | 'reviews-dashboard'
  // Books views
  | 'books-dashboard'
  // Analysis views
  | 'topic-explorer'
  | 'trend-dashboard'
  // Concept management
  | 'concept-management'
  | 'concept-graph'

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
      },
      {
        title: 'Weekly Digest',
        view: 'weekly-digest' as ViewType,
        icon: Newspaper,
        description: 'Automatic briefing on the last 7 days'
      },
      {
        title: 'Paper Q&A',
        view: 'paper-qa' as ViewType,
        icon: BookOpenCheck,
        description: 'Ask questions across papers, with cited sections'
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
        title: 'TweetDeck',
        view: 'twitter-deck' as ViewType,
        icon: Columns,
        description: 'Multi-column account view'
      },
      {
        title: 'Media Gallery', 
        view: 'twitter-media' as ViewType, 
        icon: Image,
        description: 'Images and videos'
      },
      { 
        title: 'User Analysis', 
        view: 'twitter-users' as ViewType, 
        icon: Users,
        description: 'Per-user insights'
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
    ]
  },
  {
    title: 'Papers',
    icon: BookOpen,
    items: [
      {
        title: 'Browse Papers',
        view: 'papers-dashboard' as ViewType,
        icon: BookOpen,
        description: 'Research papers analysis'
      },
      {
        title: 'Paper Reviews',
        view: 'reviews-dashboard' as ViewType,
        icon: FileSearch,
        description: 'Unpublished papers under review'
      },
      {
        title: 'References',
        view: 'papers-references' as ViewType,
        icon: Database,
        description: 'Manage paper references'
      },
      {
        title: 'Paper Feed',
        view: 'papers-feed' as ViewType,
        icon: Rss,
        description: 'New arXiv papers for your saved searches'
      }
    ]
  },
  {
    title: 'Books',
    icon: Library,
    items: [
      {
        title: 'Browse Books',
        view: 'books-dashboard' as ViewType,
        icon: BookOpen,
        description: 'Personal book collection'
      },
    ]
  },
  {
    title: 'Analysis',
    icon: LineChart,
    items: [
      {
        title: 'Topic Explorer',
        view: 'topic-explorer' as ViewType,
        icon: TrendingUp,
        description: 'Analyze topic trends and correlations'
      },
      {
        title: 'Trend Dashboard',
        view: 'trend-dashboard' as ViewType,
        icon: Flame,
        description: 'Real-time trend detection and analysis'
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
      <div className="container mx-auto flex min-h-14 flex-wrap items-center px-4 py-1 gap-y-1">
        <div className="mr-2 flex">
          <a className="mr-4 flex items-center space-x-2" href="/">
            <Database className="h-6 w-6 text-primary" />
            <span className="hidden font-bold xl:inline-block">
              SmartTrendTracer
            </span>
          </a>
        </div>
        
        <NavigationMenu viewport={false} className="mx-2">
          <NavigationMenuList className="flex-wrap">
            {navigationItems.map((item) => {
              if (item.items) {
                // Dropdown menu
                return (
                  <NavigationMenuItem key={item.title}>
                    <NavigationMenuTrigger 
                      className={cn(
                        "h-9 px-2",
                        item.items.some(i => i.view === activeView) && "bg-accent"
                      )}
                    >
                      <item.icon className="mr-2 hidden h-4 w-4 2xl:block" />
                      {item.title}
                    </NavigationMenuTrigger>
                    <NavigationMenuContent
                      className={cn(
                        // Groups in the right half open right-aligned so the
                        // panel never overflows the window edge
                        ['Authors', 'Reddit', 'Papers', 'Books', 'Analysis', 'Concepts']
                          .includes(item.title) && "left-auto right-0"
                      )}
                    >
                      <ul className={cn(
                        "grid gap-3 p-4",
                        item.items.length <= 3
                          ? "w-[320px]"
                          : "w-[400px] md:w-[500px] md:grid-cols-2"
                      )}>
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
                                <p className="line-clamp-2 text-sm leading-snug text-muted-foreground break-words mt-1">
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
                      onClick={() => onViewChange(item.view!)}
                      className="h-9 px-2 font-medium"
                    >
                      <item.icon className="mr-2 hidden h-4 w-4 2xl:block" />
                      {item.title}
                    </Button>
                  </NavigationMenuItem>
                )
              }
            })}
          </NavigationMenuList>
        </NavigationMenu>

        <div className="ml-auto flex items-center space-x-2">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}