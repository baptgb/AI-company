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
import { useT } from '@/i18n';
import type { Project } from '@/types';

function PhaseCount({ projectId }: { projectId: string }) {
  const { data, isLoading } = useProjectPhases(projectId);
  if (isLoading) return <Skeleton className="h-4 w-8 inline-block" />;
  return <>{data?.data?.length ?? 0}</>;
}

export function ProjectsPage() {
  const t = useT();
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
        <h1 className="text-2xl font-bold">{t.projects.title}</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t.projects.createProject}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t.projects.projectList}</CardTitle>
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
              {t.projects.loadFailed(error.message)}
            </p>
          ) : projects.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {t.projects.noProjects}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.projects.colName}</TableHead>
                  <TableHead>{t.projects.colDesc}</TableHead>
                  <TableHead>{t.projects.colTaskCount}</TableHead>
                  <TableHead>{t.projects.colCreatedAt}</TableHead>
                  <TableHead className="text-right">{t.projects.colActions}</TableHead>
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
                          {t.projects.viewDetail}
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
                          {t.projects.deleteProject}
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
            <DialogTitle>{t.projects.confirmDelete}</DialogTitle>
            <DialogDescription>
              {t.projects.confirmDeleteDesc(deleteTarget?.name ?? '')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              {t.common.cancel}
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
              {deleteProject.isPending ? t.common.deleting : t.projects.confirmDelete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Project Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>{t.projects.createTitle}</DialogTitle>
              <DialogDescription>
                {t.projects.createDesc}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="project-name">{t.projects.projectName}</Label>
                <Input
                  id="project-name"
                  placeholder={t.projects.projectNamePlaceholder}
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="project-desc">{t.projects.projectDesc}</Label>
                <Textarea
                  id="project-desc"
                  placeholder={t.projects.projectDescPlaceholder}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="project-root">{t.projects.rootPath}</Label>
                <Input
                  id="project-root"
                  placeholder={t.projects.rootPathPlaceholder}
                  value={newRootPath}
                  onChange={(e) => setNewRootPath(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={createProject.isPending || !newName.trim()}>
                {createProject.isPending ? t.common.creating : t.common.create}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
