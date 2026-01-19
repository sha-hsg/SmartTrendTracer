import React from 'react';
import OntologyGraph from '../components/OntologyGraph';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const OntologyGraphPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/ontology')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Manager
              </Button>
              <h1 className="text-3xl font-bold">Tag Ontology Graph</h1>
            </div>
          </div>
          <p className="text-gray-600 mt-2">
            Interactive visualization of the tag hierarchy and relationships
          </p>
        </div>

        {/* Graph Component */}
        <OntologyGraph />

        {/* Info Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border">
            <h3 className="font-semibold mb-2">🎯 Navigation</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Click and drag to pan around</li>
              <li>• Scroll to zoom in/out</li>
              <li>• Click nodes for details</li>
              <li>• Drag nodes to reposition</li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-4 border">
            <h3 className="font-semibold mb-2">🎨 Visual Encoding</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Node size = usage frequency</li>
              <li>• Node color = hierarchy level</li>
              <li>• Link width = relationship strength</li>
              <li>• Green badge = verified concept</li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-4 border">
            <h3 className="font-semibold mb-2">⚙️ Filters</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Toggle orphan nodes visibility</li>
              <li>• Show/hide synonym relationships</li>
              <li>• Filter by minimum usage count</li>
              <li>• Export graph as PNG image</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OntologyGraphPage;