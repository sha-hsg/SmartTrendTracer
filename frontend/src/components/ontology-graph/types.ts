export interface GraphNode {
  id: string | number;
  name: string;
  tag: string;
  level: number;
  usage: number;
  size: number;
  color: string;
  description?: string;
  verified?: boolean;
  quality_score?: number;
  child_count?: number;
  descendant_count?: number;
  is_synonym?: boolean;
  x?: number;
  y?: number;
}

export interface GraphLink {
  source: string | number;
  target: string | number;
  strength: number;
  type: 'parent-child' | 'synonym';
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  stats: {
    total_nodes: number;
    total_links: number;
    root_nodes: number;
    max_depth: number;
    total_usage: number;
    orphan_count: number;
  };
}
