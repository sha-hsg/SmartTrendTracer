/**
 * LLM Model Selector Component
 *
 * Allows users to view and manage their LLM model preferences for different tasks.
 * Integrates with the unified LLM Manager backend.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface ModelInfo {
  model: string;
  provider: string;
  temperature?: number;
  max_tokens?: number;
}

interface TaskInfo {
  task_type: string;
  model: string;
  provider: string;
  temperature?: number;
  max_tokens?: number;
}

interface UserPreference {
  task_type: string;
  model_name: string;
}

interface LLMModelSelectorProps {
  open: boolean;
  onClose: () => void;
  userId?: string;
}

export const LLMModelSelector: React.FC<LLMModelSelectorProps> = ({
  open,
  onClose,
  userId = 'default'
}) => {
  const [tasks, setTasks] = useState<string[]>([]);
  const [allModels, setAllModels] = useState<Record<string, ModelInfo[]>>({});
  const [preferences, setPreferences] = useState<Record<string, string>>({});
  const [taskDetails, setTaskDetails] = useState<Record<string, TaskInfo>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [pendingChanges, setPendingChanges] = useState<Record<string, string>>({});

  // Fetch all data on mount
  useEffect(() => {
    if (open) {
      loadAllData();
    }
  }, [open, userId]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch tasks, models, and preferences in parallel
      const [tasksRes, modelsRes, prefsRes] = await Promise.all([
        fetch('http://localhost:8000/api/llm/tasks'),
        fetch('http://localhost:8000/api/llm/models'),
        fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`)
      ]);

      if (!tasksRes.ok || !modelsRes.ok || !prefsRes.ok) {
        throw new Error('Failed to load LLM configuration');
      }

      const tasksData = await tasksRes.json();
      const modelsData = await modelsRes.json();
      const prefsData = await prefsRes.json();

      setTasks(tasksData);
      setAllModels(modelsData);
      setPreferences(prefsData);

      // Fetch task details for all tasks
      const details: Record<string, TaskInfo> = {};
      await Promise.all(
        tasksData.map(async (task: string) => {
          try {
            const res = await fetch(`http://localhost:8000/api/llm/tasks/${task}`);
            if (res.ok) {
              details[task] = await res.json();
            }
          } catch (err) {
            console.error(`Failed to load details for ${task}`, err);
          }
        })
      );
      setTaskDetails(details);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectModel = (taskType: string, modelName: string) => {
    setPendingChanges({
      ...pendingChanges,
      [taskType]: modelName
    });
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const preferencesArray = Object.entries(pendingChanges).map(([task_type, model_name]) => ({
        task_type,
        model_name
      }));

      const response = await fetch(`http://localhost:8000/api/llm/preferences/batch?user_id=${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ preferences: preferencesArray })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save preferences');
      }

      const result = await response.json();

      if (result.success) {
        setPreferences(result.preferences);
        setPendingChanges({});
        setSuccess(`Successfully updated ${result.updated} preference(s)`);

        // Auto-hide success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Some preferences failed to update');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleResetToDefault = async (taskType: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/llm/preferences/${taskType}?user_id=${userId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error('Failed to reset preference');
      }

      // Remove from preferences and pending changes
      const newPrefs = { ...preferences };
      delete newPrefs[taskType];
      setPreferences(newPrefs);

      const newPending = { ...pendingChanges };
      delete newPending[taskType];
      setPendingChanges(newPending);

      setSuccess(`Reset ${taskType} to default`);
      setTimeout(() => setSuccess(null), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset preference');
    }
  };

  const handleResetAll = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/llm/preferences?user_id=${userId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error('Failed to reset all preferences');
      }

      const result = await response.json();
      setPreferences({});
      setPendingChanges({});
      setSuccess(result.message);
      setTimeout(() => setSuccess(null), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset all preferences');
    }
  };

  const getCurrentModel = (taskType: string): string => {
    // Check pending changes first, then user preferences, then default
    if (pendingChanges[taskType]) {
      return pendingChanges[taskType];
    }
    if (preferences[taskType]) {
      return preferences[taskType];
    }
    return taskDetails[taskType]?.model || 'default';
  };

  const getProviderBadgeColor = (provider: string): string => {
    switch (provider) {
      case 'anthropic': return 'bg-orange-100 text-orange-800';
      case 'openai': return 'bg-green-100 text-green-800';
      case 'gemini':
      case 'google': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTaskName = (taskType: string): string => {
    return taskType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Group tasks by category (inferred from name)
  const groupedTasks = React.useMemo(() => {
    const groups: Record<string, string[]> = {
      'Tagging': [],
      'Analysis': [],
      'Generation': [],
      'Other': []
    };

    tasks.forEach(task => {
      if (task.includes('tag') || task.includes('ontology')) {
        groups['Tagging'].push(task);
      } else if (task.includes('analysis') || task.includes('entity')) {
        groups['Analysis'].push(task);
      } else if (task.includes('summary') || task.includes('generation')) {
        groups['Generation'].push(task);
      } else {
        groups['Other'].push(task);
      }
    });

    // Remove empty groups
    return Object.fromEntries(
      Object.entries(groups).filter(([_, tasks]) => tasks.length > 0)
    );
  }, [tasks]);

  const hasPendingChanges = Object.keys(pendingChanges).length > 0;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">LLM Model Preferences</DialogTitle>
          <DialogDescription>
            Customize which AI models are used for different tasks. Changes are saved per user.
          </DialogDescription>
        </DialogHeader>

        {/* Error and Success Messages */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="bg-green-50 border-green-200">
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <Tabs defaultValue={Object.keys(groupedTasks)[0]} className="w-full">
            <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Object.keys(groupedTasks).length}, 1fr)` }}>
              {Object.keys(groupedTasks).map(category => (
                <TabsTrigger key={category} value={category}>
                  {category}
                </TabsTrigger>
              ))}
            </TabsList>

            {Object.entries(groupedTasks).map(([category, categoryTasks]) => (
              <TabsContent key={category} value={category} className="mt-4 space-y-4">
                {categoryTasks.map(task => {
                  const currentModel = getCurrentModel(task);
                  const taskInfo = taskDetails[task];
                  const hasChange = pendingChanges[task] !== undefined;

                  return (
                    <div key={task} className="border rounded-lg p-4 space-y-3">
                      {/* Task Header */}
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-lg">{formatTaskName(task)}</h3>
                          <p className="text-sm text-gray-500">{task}</p>
                        </div>
                        {hasChange && (
                          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                            Unsaved
                          </Badge>
                        )}
                      </div>

                      {/* Current Configuration */}
                      {taskInfo && (
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-600">Current:</span>
                          <Badge className={getProviderBadgeColor(taskInfo.provider)}>
                            {taskInfo.provider}
                          </Badge>
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {taskInfo.model}
                          </code>
                          {taskInfo.temperature !== undefined && (
                            <span className="text-gray-500">
                              temp: {taskInfo.temperature}
                            </span>
                          )}
                          {taskInfo.max_tokens !== undefined && (
                            <span className="text-gray-500">
                              max: {taskInfo.max_tokens}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Model Selection */}
                      {allModels[task] && allModels[task].length > 1 && (
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">
                            Select Model:
                          </label>
                          <div className="grid grid-cols-1 gap-2">
                            {allModels[task].map((model, idx) => {
                              const isSelected = currentModel === model.model;
                              return (
                                <button
                                  key={idx}
                                  onClick={() => handleSelectModel(task, model.model)}
                                  className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${
                                    isSelected
                                      ? 'border-blue-500 bg-blue-50'
                                      : 'border-gray-200 hover:border-gray-300'
                                  }`}
                                >
                                  <div className="flex items-center gap-2">
                                    <input
                                      type="radio"
                                      checked={isSelected}
                                      onChange={() => handleSelectModel(task, model.model)}
                                      className="w-4 h-4"
                                    />
                                    <div className="flex items-center gap-2">
                                      <Badge className={getProviderBadgeColor(model.provider)}>
                                        {model.provider}
                                      </Badge>
                                      <code className="text-xs">{model.model}</code>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3 text-xs text-gray-500">
                                    {model.temperature !== undefined && (
                                      <span>T: {model.temperature}</span>
                                    )}
                                    {model.max_tokens !== undefined && (
                                      <span>Max: {model.max_tokens}</span>
                                    )}
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Reset Button */}
                      {preferences[task] && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResetToDefault(task)}
                          className="text-xs"
                        >
                          Reset to Default
                        </Button>
                      )}
                    </div>
                  );
                })}
              </TabsContent>
            ))}
          </Tabs>
        )}

        <DialogFooter className="flex items-center justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleResetAll}
              disabled={Object.keys(preferences).length === 0}
            >
              Reset All
            </Button>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSavePreferences}
              disabled={!hasPendingChanges || saving}
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default LLMModelSelector;
