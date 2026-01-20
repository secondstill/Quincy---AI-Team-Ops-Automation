'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchMeeting, MeetingDetail, Task } from '@/services/api';
import { Loader2, FileText, ListTodo, Bot, Calendar, Video, PlayCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MeetingDetailPage() {
    const params = useParams();
    const id = Number(params?.id);

    const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'tasks'>('summary');

    useEffect(() => {
        if (id) {
            loadMeeting();
        }
    }, [id]);

    const loadMeeting = async () => {
        try {
            setLoading(true);
            const data = await fetchMeeting(id);
            setMeeting(data);
        } catch (error) {
            console.error("Failed to fetch meeting details", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center"><Loader2 className="animate-spin text-blue-600 w-8 h-8" /></div>;
    if (!meeting) return <div className="p-8">Meeting not found</div>;

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8">
            {/* Header */}
            <header className="mb-8">
                <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                    <Link href="/" className="hover:text-blue-600">Dashboard</Link> /
                    <Link href="/meetings" className="hover:text-blue-600">Meetings</Link> / Details
                </div>
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">{meeting.title}</h1>
                        <p className="text-slate-500 mt-2 flex items-center gap-2">
                            <Calendar className="w-4 h-4" /> {new Date(meeting.date).toLocaleString()}
                            <span className="bg-slate-200 dark:bg-slate-800 text-xs px-2 py-0.5 rounded-full ml-2 uppercase font-medium">{meeting.status}</span>
                        </p>
                    </div>

                    {/* Only show Join button for Scheduled meetings */}
                    {meeting.status === 'scheduled' && (
                        <Link href={`/meetings/${id}/room`}>
                            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium shadow-sm transition-colors flex items-center gap-2">
                                <Video className="w-4 h-4" /> Join Live Room
                            </button>
                        </Link>
                    )}
                </div>

                {meeting.audio_url && (
                    <div className="mt-6 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-4">
                        <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-full">
                            <PlayCircle className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Meeting Recording</h3>
                            <audio
                                controls
                                className="w-full h-8"
                                src={`http://${window.location.hostname}:8000${meeting.audio_url}`}
                            />
                        </div>
                    </div>
                )}
            </header>

            <div className="max-w-5xl mx-auto bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden min-h-[600px] flex flex-col">
                {/* Tabs */}
                <div className="flex border-b border-slate-200 dark:border-slate-800">
                    <button
                        onClick={() => setActiveTab('summary')}
                        className={cn("px-6 py-4 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors", activeTab === 'summary' ? "border-blue-500 text-blue-600" : "border-transparent text-slate-500 hover:text-slate-700")}
                    >
                        <Bot className="w-4 h-4" /> AI Summary
                    </button>
                    <button
                        onClick={() => setActiveTab('transcript')}
                        className={cn("px-6 py-4 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors", activeTab === 'transcript' ? "border-blue-500 text-blue-600" : "border-transparent text-slate-500 hover:text-slate-700")}
                    >
                        <FileText className="w-4 h-4" /> Transcript
                    </button>
                    <button
                        onClick={() => setActiveTab('tasks')}
                        className={cn("px-6 py-4 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors", activeTab === 'tasks' ? "border-blue-500 text-blue-600" : "border-transparent text-slate-500 hover:text-slate-700")}
                    >
                        <ListTodo className="w-4 h-4" /> Tasks <span className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded-full text-xs">{meeting.tasks.length}</span>
                    </button>
                </div>

                {/* Content */}
                <div className="p-8 flex-1 bg-slate-50/50 dark:bg-slate-900/50">
                    {activeTab === 'summary' && (
                        <div className="prose dark:prose-invert max-w-none">
                            {meeting.summary ? (
                                <div className="whitespace-pre-wrap">{meeting.summary}</div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                                    <Bot className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No summary generated yet.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'transcript' && (
                        <div className="font-mono text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                            {meeting.transcript ? (
                                <div className="whitespace-pre-wrap p-4 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                                    {meeting.transcript}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                                    <FileText className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No transcript available.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'tasks' && (
                        <div className="space-y-3">
                            {meeting.tasks.length > 0 ? meeting.tasks.map(task => (
                                <div key={task.id} className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <span className={cn(
                                            "w-2 h-2 rounded-full",
                                            task.status === 'completed' ? "bg-green-500" : "bg-blue-500"
                                        )} />
                                        <span className="font-medium text-slate-800 dark:text-slate-200">{task.title}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300">{task.priority || 'Normal'}</span>
                                        {task.assignee && <span className="text-xs font-mono text-slate-400">{task.assignee}</span>}
                                    </div>
                                </div>
                            )) : (
                                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                                    <ListTodo className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No tasks extracted.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
