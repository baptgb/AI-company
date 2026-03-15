import { Link } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Users, Bot, ListTodo, CheckCircle, ArrowRight,
  Activity, BarChart3, Settings, Wifi, WifiOff,
  CircleCheck, CircleX, Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTeams } from '@/api/teams';
import { useProjects } from '@/api/projects';
import { useEvents } from '@/api/events';
import { apiFetch } from '@/api/client';
import { useWSStore } from '@/stores/websocket';
import type { Project, TeamStatus, APIResponse } from '@/types';

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  loading,
}: {
  title: string;
  value: number | string;
  description?: string;
  icon: React.ElementType;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-16" />
        ) : (
          <>
            <p className="text-2xl font-bold">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'completed'
      ? 'default'
      : status === 'running' || status === 'in_progress'
        ? 'secondary'
        : status === 'failed'
          ? 'destructive'
          : 'outline';
  const label =
    status === 'completed'
      ? '已完成'
      : status === 'running' || status === 'in_progress'
        ? '进行中'
        : status === 'failed'
          ? '失败'
          : status === 'pending'
            ? '等待中'
            : status;
  return <Badge variant={variant}>{label}</Badge>;
}

function ProjectOverviewCard({ project }: { project: Project }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{project.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {project.description || '暂无描述'}
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-2 -ml-2"
          render={<Link to={`/projects/${project.id}`} />}
        >
          查看详情
          <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { data: projectsData, isLoading: projectsLoading, error: projectsError } = useProjects();
  const projects = projectsData?.data ?? [];

  const { data, isLoading: teamsLoading, error } = useTeams();
  const teams = data?.data ?? [];

  // WebSocket connection status
  const wsConnected = useWSStore((s) => s.connected);

  // Recent events for activity summary
  const { data: eventsData, isLoading: eventsLoading } = useEvents({ limit: 5 });
  const recentEvents = eventsData?.data ?? [];

  // Batch-fetch all team statuses using useQueries (stable hook count)
  const statusQueries = useQueries({
    queries: teams.map((team) => ({
      queryKey: ['teams', team.id, 'status'],
      queryFn: () => apiFetch<APIResponse<TeamStatus>>(`/api/teams/${team.id}/status`),
      enabled: !!team.id,
    })),
  });

  const statusLoading = statusQueries.some((q) => q.isLoading);

  // Build team→status map
  const statusMap = new Map<string, TeamStatus>();
  teams.forEach((team, i) => {
    const s = statusQueries[i]?.data?.data;
    if (s) statusMap.set(team.id, s);
  });

  // Aggregated stats
  let totalAgents = 0;
  let hookAgents = 0;
  let activeTasks = 0;
  let completedTasks = 0;
  const allTasks: { id: string; title: string; status: string; created_at: string; teamName: string }[] = [];

  for (const [, s] of statusMap) {
    totalAgents += s.agents.length;
    hookAgents += s.agents.filter((a) => a.source === 'hook').length;
    activeTasks += s.active_tasks.length;
    completedTasks += s.completed_tasks;
    allTasks.push(...s.active_tasks.map((t) => ({ ...t, teamName: s.team.name })));
  }

  const recentTasks = allTasks
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  const allLoaded = teams.length > 0 && statusMap.size === teams.length;

  if (teamsLoading || projectsLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-20" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader><Skeleton className="h-6 w-24" /></CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || projectsError) {
    return (
      <div className="py-12 text-center">
        <p className="text-sm text-destructive">加载失败: {(error ?? projectsError)?.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="项目数量"
          value={projects.length}
          description="已创建的项目总数"
          icon={Users}
        />
        <StatCard
          title="Agent 总数"
          value={allLoaded ? totalAgents : '--'}
          description={allLoaded && hookAgents > 0
            ? `含 ${hookAgents} 个自动捕获的 Agent`
            : '所有项目中的 Agent'}
          icon={Bot}
          loading={statusLoading && teams.length > 0}
        />
        <StatCard
          title="活跃任务"
          value={allLoaded ? activeTasks : '--'}
          description="正在执行中的任务"
          icon={ListTodo}
          loading={statusLoading && teams.length > 0}
        />
        <StatCard
          title="已完成任务"
          value={allLoaded ? completedTasks : '--'}
          description="累计完成的任务数"
          icon={CheckCircle}
          loading={statusLoading && teams.length > 0}
        />
      </div>

      {/* System Health + Quick Actions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* System Health */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">系统健康状态</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">API 状态</span>
                {teamsLoading ? (
                  <Skeleton className="h-5 w-14" />
                ) : error ? (
                  <Badge variant="destructive" className="gap-1">
                    <CircleX className="h-3 w-3" /> 离线
                  </Badge>
                ) : (
                  <Badge variant="default" className="gap-1">
                    <CircleCheck className="h-3 w-3" /> 在线
                  </Badge>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">WebSocket 连接</span>
                {wsConnected ? (
                  <Badge variant="default" className="gap-1">
                    <Wifi className="h-3 w-3" /> 已连接
                  </Badge>
                ) : (
                  <Badge variant="outline" className="gap-1">
                    <WifiOff className="h-3 w-3" /> 未连接
                  </Badge>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">团队数量</span>
                <span className="text-sm font-medium">{teams.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">最后活动</span>
                <span className="text-sm font-medium">
                  {recentEvents.length > 0
                    ? new Date(recentEvents[0].timestamp).toLocaleString('zh-CN')
                    : '暂无'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">快速操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <Button variant="outline" className="justify-start gap-2" render={<Link to="/tasks" />}>
                <ListTodo className="h-4 w-4" />
                查看任务墙
              </Button>
              <Button variant="outline" className="justify-start gap-2" render={<Link to="/analytics" />}>
                <BarChart3 className="h-4 w-4" />
                活动分析
              </Button>
              <Button variant="outline" className="justify-start gap-2" render={<Link to="/settings" />}>
                <Settings className="h-4 w-4" />
                系统设置
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            近期活动
          </CardTitle>
        </CardHeader>
        <CardContent>
          {eventsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : recentEvents.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              暂无活动记录
            </p>
          ) : (
            <div className="space-y-2">
              {recentEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge variant="outline" className="shrink-0 text-xs">
                      {evt.type}
                    </Badge>
                    <span className="text-sm text-muted-foreground truncate">
                      {evt.source}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 ml-2 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(evt.timestamp).toLocaleString('zh-CN')}
                  </span>
                </div>
              ))}
              <Button
                variant="ghost"
                size="sm"
                className="w-full mt-1"
                render={<Link to="/events" />}
              >
                查看全部事件
                <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Tasks */}
      <Card>
        <CardHeader>
          <CardTitle>近期任务</CardTitle>
        </CardHeader>
        <CardContent>
          {statusLoading && teams.length > 0 ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : recentTasks.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              暂无近期任务，请在项目详情中执行新任务
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务标题</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>创建时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium">{task.title}</TableCell>
                    <TableCell>
                      <StatusBadge status={task.status} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {task.teamName}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Project Overview */}
      <Card>
        <CardHeader>
          <CardTitle>项目概览</CardTitle>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              暂无项目，请先创建一个项目
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <ProjectOverviewCard
                  key={project.id}
                  project={project}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
