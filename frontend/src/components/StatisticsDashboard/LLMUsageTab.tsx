import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Brain, Zap, Cpu, Activity, CheckCircle, XCircle } from 'lucide-react'
import {
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#6366f1', '#14b8a6']

interface LLMUsageData {
  last_used: {
    model: string
    task_type: string
    timestamp: string
    status: string
  } | null
  recent_calls: Array<{
    model: string
    task_type: string
    timestamp: string
    status: string
    duration_ms: number
    tokens_used: number
  }>
  model_distribution: Array<{ _id: string; count: number }>
  task_distribution: Array<{ _id: string; count: number }>
  usage_last_24h: number
  total_calls: number
  success_rate: number
  token_usage: {
    total: number
    average_per_call: number
    total_calls: number
  }
  performance: Array<{ _id: string; avg_duration: number }>
}

interface LLMUsageTabProps {
  llmUsage: LLMUsageData
}

export function LLMUsageTab({ llmUsage }: LLMUsageTabProps) {
  return (
    <>
      {/* LLM Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total LLM Calls</CardTitle>
            <Brain className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{llmUsage.total_calls.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {llmUsage.usage_last_24h} in last 24h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Zap className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{llmUsage.success_rate}%</div>
            <Progress value={llmUsage.success_rate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens Used</CardTitle>
            <Cpu className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{llmUsage.token_usage.total.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {llmUsage.token_usage.average_per_call.toLocaleString()} avg/call
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Used Model</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            {llmUsage.last_used ? (
              <>
                <div
                  className="text-lg font-bold truncate font-mono"
                  title={llmUsage.last_used.model}
                >
                  {llmUsage.last_used.model}
                </div>
                <p className="text-xs text-muted-foreground">
                  {llmUsage.last_used.task_type} • {new Date(llmUsage.last_used.timestamp).toLocaleTimeString()}
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No recent usage</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Model Distribution</CardTitle>
            <CardDescription>LLM calls by model</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={llmUsage.model_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="_id"
                  angle={-45}
                  textAnchor="end"
                  height={120}
                  interval={0}
                  tick={{ fontSize: 11, fontFamily: 'monospace' }}
                />
                <YAxis />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-background border border-border p-2 rounded shadow-lg">
                          <p className="font-mono text-sm font-medium">{payload[0].payload._id}</p>
                          <p className="text-sm">Calls: {payload[0].value}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" fill="#8b5cf6">
                  {llmUsage.model_distribution.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Task Distribution</CardTitle>
            <CardDescription>LLM calls by task type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RePieChart>
                <Pie
                  data={llmUsage.task_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry._id}: ${entry.count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {llmUsage.task_distribution.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </RePieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Average Response Time by Model</CardTitle>
          <CardDescription>Performance comparison across different models</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={llmUsage.performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="_id"
                angle={-45}
                textAnchor="end"
                height={120}
                interval={0}
                tick={{ fontSize: 11, fontFamily: 'monospace' }}
              />
              <YAxis label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-background border border-border p-2 rounded shadow-lg">
                        <p className="font-mono text-sm font-medium">{payload[0].payload._id}</p>
                        <p className="text-sm">Avg Time: {Math.round(payload[0].value as number)}ms</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="avg_duration" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recent Calls Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent LLM Calls</CardTitle>
          <CardDescription>Last 20 LLM API calls</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              {llmUsage.recent_calls.map((call, index) => (
                <div
                  key={`call-${index}`}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex-1 space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={call.status === 'success' ? 'default' : 'destructive'}>
                        {call.status === 'success' ? (
                          <CheckCircle className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircle className="h-3 w-3 mr-1" />
                        )}
                        {call.status}
                      </Badge>
                      <span
                        className="font-medium text-sm font-mono truncate"
                        title={call.model}
                      >
                        {call.model}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Task: {call.task_type} • {new Date(call.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right space-y-1 flex-shrink-0">
                    <div className="text-sm font-medium">{call.tokens_used.toLocaleString()} tokens</div>
                    <div className="text-xs text-muted-foreground">{call.duration_ms}ms</div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </>
  )
}
