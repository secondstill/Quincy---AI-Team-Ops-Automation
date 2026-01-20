'use client';

import React, { useState, useEffect } from 'react';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, useSensor, useSensors, PointerSensor, TouchSensor } from '@dnd-kit/core';
import { SortableContext, arrayMove, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { fetchTasks, updateTaskStatus, Task } from '@/services/api';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const COLUMNS = [
    { id: 'pending', title: 'Pending' },
    { id: 'in_progress', title: 'In Progress' },
    { id: 'review', title: 'Review' },
    { id: 'completed', title: 'Completed' },
];

export default function KanbanBoard() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeId, setActiveId] = useState<number | null>(null);

    useEffect(() => {
        loadTasks();
    }, []);

    const loadTasks = async () => {
        try {
            const data = await fetchTasks();
            setTasks(data);
        } catch (error) {
            console.error("Failed to load tasks", error);
        } finally {
            setLoading(false);
        }
    };

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }), // Prevent accidental drags
        useSensor(TouchSensor)
    );

    const handleDragStart = (event: DragStartEvent) => {
        setActiveId(event.active.id as number);
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;

        if (!over) {
            setActiveId(null);
            return;
        }

        const activeId = active.id as number;
        const overId = over.id; // Could be a container ID or a task ID

        // Find the task
        const activeTask = tasks.find(t => t.id === activeId);
        if (!activeTask) return;

        // Determine new status
        let newStatus = activeTask.status;

        // If dropped on a container (column), use that ID
        if (COLUMNS.some(c => c.id === overId)) {
            newStatus = overId as Task['status'];
        } else {
            // Dropped on another task? Find that task's status
            const overTask = tasks.find(t => t.id === overId);
            if (overTask) {
                newStatus = overTask.status;
            }
        }

        if (newStatus !== activeTask.status) {
            // Optimistic update
            setTasks(tasks.map(t =>
                t.id === activeId ? { ...t, status: newStatus } : t
            ));

            // API Call
            try {
                await updateTaskStatus(activeId, newStatus);
            } catch (error) {
                console.error("Failed to update task", error);
                // Revert on failure could be added here
            }
        }

        setActiveId(null);
    };

    if (loading) {
        return <div className="flex justify-center p-10"><Loader2 className="animate-spin h-8 w-8 text-blue-500" /></div>;
    }

    return (
        <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="flex flex-col md:flex-row gap-6 overflow-x-auto pb-4 h-[calc(100vh-120px)]">
                {COLUMNS.map(column => (
                    <Column
                        key={column.id}
                        column={column}
                        tasks={tasks.filter(t => t.status === column.id)}
                    />
                ))}
            </div>
            <DragOverlay>
                {activeId ? (
                    <TaskCard task={tasks.find(t => t.id === activeId)!} overlay />
                ) : null}
            </DragOverlay>
        </DndContext>
    );
}

function Column({ column, tasks }: { column: { id: string, title: string }, tasks: Task[] }) {
    const { setNodeRef } = useSortable({
        id: column.id,
        data: { type: 'Column', column }
    });

    return (
        <div ref={setNodeRef} className="bg-slate-100 dark:bg-slate-800 rounded-xl p-4 min-w-[300px] flex flex-col h-full border border-slate-200 dark:border-slate-700">
            <h3 className="font-semibold text-slate-700 dark:text-slate-200 mb-4 flex items-center justify-between">
                {column.title}
                <span className="bg-slate-200 dark:bg-slate-700 text-xs px-2 py-1 rounded-full">{tasks.length}</span>
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3">
                <SortableContext items={tasks.map(t => t.id)}>
                    {tasks.map(task => (
                        <TaskCard key={task.id} task={task} />
                    ))}
                </SortableContext>
                {tasks.length === 0 && (
                    <div className="h-24 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg flex items-center justify-center text-slate-400 text-sm">
                        No tasks
                    </div>
                )}
            </div>
        </div>
    );
}

function TaskCard({ task, overlay }: { task: Task, overlay?: boolean }) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: task.id,
        data: { type: 'Task', task }
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        transition,
    };

    if (isDragging) {
        return (
            <div ref={setNodeRef} style={style} className="opacity-30 bg-slate-200 h-24 rounded-lg border-2 border-blue-500 border-dashed" />
        );
    }

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className={cn(
                "bg-white dark:bg-slate-900 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 cursor-grab hover:shadow-md transition-shadow group",
                overlay && "rotate-2 shadow-xl cursor-grabbing ring-2 ring-blue-500"
            )}
        >
            <div className="flex justify-between items-start mb-2">
                <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-medium",
                    task.priority === 'High' ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                        task.priority === 'Medium' ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                            "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                )}>
                    {task.priority || 'Normal'}
                </span>
                {task.assignee && (
                    <span className="text-xs text-slate-500 font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">{task.assignee}</span>
                )}
            </div>
            <h4 className="font-medium text-slate-900 dark:text-slate-100 text-sm">{task.title}</h4>
        </div>
    );
}
