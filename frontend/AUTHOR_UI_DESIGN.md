# Author Management UI - Design Document

**Phase 3 Implementation Plan**
**Date:** November 24, 2025

## Overview

Create a comprehensive author management interface for the SmartTrendTracer frontend, allowing users to:
- View all authors and their statistics
- Search and filter authors
- Edit author information
- Merge duplicate authors
- View author analytics and trends

---

## Component Structure

```
AuthorManagementModern/
├── AuthorListView           # Main list of all authors
├── AuthorDetailModal        # Detailed author information
├── AuthorMergeDialog        # Merge duplicate authors
├── AuthorAnalyticsDashboard # Analytics and visualizations
└── AuthorSearchBar          # Search and filter
```

---

## 1. AuthorListView Component

### Features
- Display all authors in table/card format
- Search by author name
- Sort by: article count, name, last published
- Filter by: has articles, article count range
- Click author to open detail modal
- "Merge Authors" button for selected authors

### Data Display
```typescript
interface Author {
  id: string;
  name: string;
  canonical_name: string;
  subdomain?: string;
  email?: string;
  article_count: number;
  last_article_date?: string;
  created_at: string;
  updated_at: string;
}
```

### UI Layout
```
┌────────────────────────────────────────────────────────────┐
│ Authors Management                        [+ Add] [Merge]  │
├────────────────────────────────────────────────────────────┤
│ [Search: _____________]  Sort: [▼ Article Count]          │
├────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Name              │ Articles │ Last Published │ Actions││
│ ├────────────────────────────────────────────────────────┤ │
│ │ Nathan Lambert    │    20    │ Nov 20, 2025   │ [...] ││
│ │ Ethan Mollick     │    20    │ Nov 18, 2025   │ [...] ││
│ │ Sebastian Raschka │    16    │ Nov 15, 2025   │ [...] ││
│ │ Gary Marcus       │     5    │ Nov 10, 2025   │ [...] ││
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Actions Menu
- View Details
- Edit Author
- View Articles
- Find Similar (for merge)
- Delete (if 0 articles)

---

## 2. AuthorDetailModal Component

### Features
- Display full author information
- Show list of author's articles (paginated)
- Edit author details inline
- View co-authorship relationships
- Link to author's Substack/blog

### UI Layout
```
┌──────────────────────────────────────────────────────┐
│ ✕                Author Details                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Name: Nathan Lambert              [Edit]            │
│ Canonical: Nathan Lambert                           │
│ Subdomain: robotic                                  │
│ Email: [none]                                       │
│                                                      │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ Articles (20)                     [View All]        │
│ • Olmo 3: America's truly open... (Nov 20, 2025)   │
│ • Why AI writing is mid           (Nov 16, 2025)   │
│ • Interview: Ant Group's open...  (Nov 12, 2025)   │
│                                                      │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ Statistics                                          │
│ • Total Articles: 20                                │
│ • Total Words: 234,567                              │
│ • Avg Words/Article: 11,728                         │
│ • First Article: Jan 15, 2025                       │
│ • Last Article: Nov 20, 2025                        │
│                                                      │
│                         [Close]    [Delete Author]  │
└──────────────────────────────────────────────────────┘
```

---

## 3. AuthorMergeDialog Component

### Features
- Find similar authors (fuzzy matching)
- Select source author (to be deleted)
- Select target author (to be kept)
- Preview merge impact
- Execute merge with confirmation

### Workflow
1. Search for similar authors (threshold: 85-90%)
2. Show potential duplicates
3. Select source → target
4. Preview: "X articles will be moved from A to B"
5. Confirm and execute merge
6. Show success/error message

### UI Layout
```
┌──────────────────────────────────────────────────────┐
│ ✕              Merge Duplicate Authors               │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Step 1: Find Similar Authors                        │
│ Search: [Nathan Lambert________]  [Find Similar]    │
│                                                      │
│ Similar Authors Found:                              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ○ Nathan Lambert (robotic) - 20 articles       │ │
│ │ ○ Nathan Lambert (interconnects) - 0 articles  │ │
│ │   Similarity: 95%                               │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Step 2: Select Merge Direction                     │
│ Source (DELETE): [Nathan Lambert (interconnects)]  │
│ Target (KEEP):   [Nathan Lambert (robotic)]        │
│                                                      │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ Merge Preview:                                      │
│ • 0 articles will be moved                          │
│ • Source author will be deleted                     │
│ • Target will remain with 20 articles               │
│                                                      │
│                    [Cancel]    [Confirm Merge]      │
└──────────────────────────────────────────────────────┘
```

---

## 4. AuthorAnalyticsDashboard Component

### Features
- Top authors by article count (bar chart)
- Publishing frequency over time (line chart)
- Word count distribution by author (bar chart)
- Author activity heatmap (calendar view)
- Co-authorship network (future: D3.js graph)

### Charts to Implement

#### Chart 1: Top Authors
```
Nathan Lambert    ████████████████████ 20
Ethan Mollick     ████████████████████ 20
Sebastian Raschka ████████████████ 16
Gary Marcus       ██████ 5
Others            ███ 4
```

#### Chart 2: Publishing Frequency
```
Articles/Month
    ^
 20 │        ╭──╮
 15 │     ╭──╯  ╰╮
 10 │  ╭──╯      ╰─╮
  5 │╭─╯           ╰─╮
  0 └──────────────────────> Time
    Jan Feb Mar Apr May Jun
```

#### Chart 3: Word Count by Author
```
Avg Words/Article
    ^
15k │     █
    │     █    █
10k │     █    █    █
    │     █    █    █    █
 5k │     █    █    █    █    █
    └─────────────────────────────>
         NL   EM   SR   GM   Other
```

### UI Layout
```
┌────────────────────────────────────────────────────────────┐
│ Author Analytics                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌──────────────────────┐  ┌──────────────────────────┐   │
│ │ Top Authors          │  │ Publishing Frequency     │   │
│ │ [Bar Chart]          │  │ [Line Chart]             │   │
│ │                      │  │                          │   │
│ └──────────────────────┘  └──────────────────────────┘   │
│                                                            │
│ ┌──────────────────────┐  ┌──────────────────────────┐   │
│ │ Word Count by Author │  │ Activity Heatmap         │   │
│ │ [Bar Chart]          │  │ [Calendar View]          │   │
│ │                      │  │                          │   │
│ └──────────────────────┘  └──────────────────────────┘   │
│                                                            │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Statistics Summary                                  │   │
│ │ • Total Authors: 8                                  │   │
│ │ • Total Articles: 65                                │   │
│ │ • Avg Articles/Author: 8.1                          │   │
│ │ • Most Active: Nathan Lambert, Ethan Mollick (20)  │   │
│ └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Needed

### Backend Endpoints (some may need creation)

1. **GET /api/authors** - List all authors
   ```typescript
   Response: {
     authors: Author[];
     total: number;
   }
   ```

2. **GET /api/authors/{id}** - Get author details
   ```typescript
   Response: {
     author: Author;
     articles: Article[];
     statistics: AuthorStats;
   }
   ```

3. **PUT /api/authors/{id}** - Update author
   ```typescript
   Body: {
     name?: string;
     canonical_name?: string;
     email?: string;
     subdomain?: string;
   }
   ```

4. **DELETE /api/authors/{id}** - Delete author (if 0 articles)

5. **POST /api/authors/find-similar** - Find similar authors
   ```typescript
   Body: { name: string; threshold?: number }
   Response: {
     similar: Array<{
       author: Author;
       similarity: number;
     }>
   }
   ```

6. **POST /api/authors/merge** - Merge authors
   ```typescript
   Body: {
     source_id: string;
     target_id: string;
   }
   Response: {
     success: boolean;
     merged_author: Author;
   }
   ```

7. **GET /api/authors/analytics** - Get analytics data
   ```typescript
   Response: {
     top_authors: Array<{author: Author, count: number}>;
     publishing_frequency: Array<{month: string, count: number}>;
     word_count_by_author: Array<{author: string, avg_words: number}>;
   }
   ```

---

## Technology Stack

### Frontend Libraries
- **React** - Component framework
- **TypeScript** - Type safety
- **Recharts** - Charts and visualizations
- **shadcn/ui** - UI components (already installed)
- **TailwindCSS** - Styling
- **axios** - HTTP requests

### Components to Use (shadcn/ui)
- `Button` - Actions and navigation
- `Dialog` - Modals and confirmations
- `Table` - Author list display
- `Card` - Container components
- `Input` - Search and forms
- `Badge` - Status indicators
- `Alert` - Success/error messages
- `Tabs` - Multiple views in dashboard

---

## Implementation Order

### Sprint 1: Core Functionality (Priority 1)
1. ✅ Create backend API endpoints
2. ✅ Build AuthorListView component
3. ✅ Build AuthorDetailModal component
4. ✅ Add search and filtering

### Sprint 2: Merge Functionality (Priority 2)
5. ✅ Build AuthorMergeDialog component
6. ✅ Implement find similar authors
7. ✅ Implement merge confirmation flow

### Sprint 3: Analytics (Priority 3)
8. ✅ Build AuthorAnalyticsDashboard
9. ✅ Add Recharts visualizations
10. ✅ Integrate with navigation

---

## Navigation Integration

Add to `ModernNavigation.tsx`:

```typescript
{
  title: 'Authors',
  icon: Users,
  items: [
    { title: 'All Authors', path: '/authors', icon: List },
    { title: 'Merge Duplicates', path: '/authors/merge', icon: GitMerge },
    { title: 'Author Analytics', path: '/authors/analytics', icon: BarChart3 },
  ]
}
```

---

## Acceptance Criteria

### Author List
- [ ] Display all authors with stats
- [ ] Search by name works
- [ ] Sort by article count, name, date
- [ ] Click author opens detail modal

### Author Detail
- [ ] Show full author information
- [ ] List author's articles (paginated)
- [ ] Edit author information inline
- [ ] Delete author (if 0 articles)

### Merge Authors
- [ ] Find similar authors by name
- [ ] Select source and target
- [ ] Preview merge impact
- [ ] Execute merge successfully
- [ ] Show confirmation message

### Analytics
- [ ] Display top authors chart
- [ ] Show publishing frequency
- [ ] Display word count distribution
- [ ] Summary statistics accurate

---

## Testing Checklist

- [ ] Test with 0 authors
- [ ] Test with 1 author
- [ ] Test with 100+ authors (pagination)
- [ ] Test search with special characters
- [ ] Test merge with 0 articles
- [ ] Test merge with many articles
- [ ] Test delete author with articles (should fail)
- [ ] Test edit author name
- [ ] Test analytics with no data

---

## Future Enhancements

1. **Co-authorship Network Graph**
   - D3.js force-directed graph
   - Show collaboration relationships

2. **Author Profiles**
   - Bio and description
   - Social media links
   - Photo/avatar

3. **Author Notifications**
   - Email when new article published
   - RSS feed per author

4. **Bulk Operations**
   - Bulk merge multiple authors
   - Bulk delete unused authors
   - Export author list

5. **Author Verification**
   - ORCID integration
   - Email verification
   - Link to verified profiles

---

**Design Document Status:** ✅ Complete
**Ready for Implementation:** Yes
**Estimated Time:** 4-6 hours
