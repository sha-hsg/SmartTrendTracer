import React from 'react';

const LEGEND_ITEMS = [
  { color: 'bg-red-400', label: 'Root Concepts' },
  { color: 'bg-teal-400', label: 'Level 1' },
  { color: 'bg-blue-400', label: 'Level 2' },
  { color: 'bg-green-400', label: 'Level 3+' },
  { color: 'bg-gray-400', label: 'Synonyms' },
];

const GraphLegend: React.FC = () => {
  return (
    <div className="absolute bottom-4 left-4 bg-white border rounded-lg shadow p-3">
      <div className="text-xs font-semibold mb-2">Legend</div>
      <div className="space-y-1 text-xs">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GraphLegend;
