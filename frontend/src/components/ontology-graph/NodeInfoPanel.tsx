import React from 'react';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { GraphNode } from './types';

interface NodeInfoPanelProps {
  node: GraphNode;
  layoutType: 'force' | 'elk';
  collapsedNodes: Set<string>;
  onClose: () => void;
}

const NodeInfoPanel: React.FC<NodeInfoPanelProps> = ({
  node,
  layoutType,
  collapsedNodes,
  onClose,
}) => {
  return (
    <div className="absolute top-4 right-4 bg-white border rounded-lg shadow-lg p-4 max-w-xs">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold">{node.name}</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          x
        </button>
      </div>

      <div className="space-y-1 text-sm">
        <div>Tag: <code className="bg-gray-100 px-1">{node.tag}</code></div>
        <div>Level: {node.level}</div>
        <div>Usage: {node.usage}</div>
        {node.child_count !== undefined && (
          <div>Children: {node.child_count}</div>
        )}
        {node.descendant_count !== undefined && (
          <div>Descendants: {node.descendant_count}</div>
        )}
        {layoutType === 'elk' && node.child_count && node.child_count > 0 && (
          <div className="flex items-center gap-2">
            <span>Status:</span>
            {collapsedNodes.has(String(node.id)) ? (
              <Badge variant="destructive" className="text-xs">
                <ChevronRight className="w-3 h-3 mr-1" />
                Collapsed
              </Badge>
            ) : (
              <Badge variant="default" className="text-xs">
                <ChevronDown className="w-3 h-3 mr-1" />
                Expanded
              </Badge>
            )}
          </div>
        )}
        {node.verified && (
          <Badge className="mt-2" variant="default">Verified</Badge>
        )}
        {node.is_synonym && (
          <Badge className="mt-2" variant="secondary">Synonym</Badge>
        )}
        {node.description && (
          <div className="mt-2 text-gray-600">{node.description}</div>
        )}
      </div>
    </div>
  );
};

export default NodeInfoPanel;
