import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plus, Eye, Trash2 } from 'lucide-react';
import { useProjects, useCreateProject, useDeleteProject, useProjectPhases } from '@/api/projects';
import type { Project } from '@/types';

function PhaseCount({ projectId }: { projectId: string }) {
  const { data, isLoading } = useProjectPhases(projectId);
  if (isLoading) return <Skeleton className="h-4 w-8 inline-block" />;
  return <>{data?.data?.length ?? 0}</>;
}

export function ProjectsPage() {
  const { data, isLoading, error } = useProjects();
  const projects = data?.data ?? [];
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();

  const [createOpen, setCreateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newRootPath, setNewRootPath] = useState('');

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    createProject.mutate(
      {
        name: newName.trim(),
        description: newDesc.trim() || undefined,
        root_path: newRootPath.trim() || undefined,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setNewName('');
          setNewDesc('');
          setNewRootPath('');
        },
      }
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">项目管理</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          创建项目
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>项目列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <p className="text-sm text-destructive">
              加载失败: {error.message}
            </p>
          ) : projects.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              暂无项目，点击上方按钮创建第一个项目
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>阶段数</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project: Project) => (
                  <TableRow key={project.id}>
                    <TableCell className="font-medium">{project.name}</TableCell>
                    <TableCell className="text-muted-foreground max-w-[300px] truncate">
                      {project.description || '--'}
                    </TableCell>
                    <TableCell>
                      <PhaseCount projectId={project.id} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(project.created_at).toLocaleString('zh-CN')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          render={<Link to={`/projects/${project.id}`} />}
                        >
                          <Eye className="mr-1 h-3 w-3" />
                          详情
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeleteTarget(project);
                            setDeleteOpen(true);
                          }}
                        >
                          <Trash2 className="mr-1 h-3 w-3 text-destructive" />
                          删除
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除项目「{deleteTarget?.name}」吗？此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (!deleteTarget) return;
                deleteProject.mutate(deleteTarget.id, {
                  onSuccess: () => { setDeleteOpen(false); setDeleteTarget(null); },
                });
              }}
              disabled={deleteProject.isPending}
            >
              {deleteProject.isPending ? '删除中...' : '确认删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Project Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>创建项目</DialogTitle>
              <DialogDescription>
                创建一个新的 AI Agent 项目
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="project-name">项目名称</Label>
                <Input
                  id="project-name"
                  placeholder="输入项目名称"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="project-desc">项目描述</Label>
                <Textarea
                  id="project-desc"
                  placeholder="输入项目描述（可选）"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="project-root">根路径</Label>
                <Input
                  id="project-root"
                  placeholder="项目根目录路径（可选）"
                  value={newRootPath}
                  onChange={(e) => setNewRootPath(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={createProject.isPending || !newName.trim()}>
                {createProject.isPending ? '创建中...' : '创建'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
