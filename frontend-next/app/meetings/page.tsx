'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchMeetings, Meeting, deleteMeeting } from '@/services/api';
import UploadMeeting from '@/components/UploadMeeting';
import ScheduleMeeting from '@/components/ScheduleMeeting';
import { Calendar, Clock, FileText, CheckCircle2, Loader2, PlayCircle, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MeetingsPage() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);

    const loadMeetings = async () => {
        try {
            setLoading(true);
            const data = await fetchMeetings();
            setMeetings(data);
        } catch (error) {
            console.error("Failed to fetch meetings", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMeetings();
    }, []);

    const handleDelete = async (meetingId: number, meetingTitle: string) => {
        if (!confirm(`Are you sure you want to delete "${meetingTitle}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await deleteMeeting(meetingId);
            await loadMeetings(); // Refresh the list
        } catch (error) {
            console.error("Failed to delete meeting", error);
            alert("Failed to delete meeting");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8">
            <header className="mb-8">
                <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                    <Link href="/" className="hover:text-blue-600">Dashboard</Link> / Meetings
                </div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Meetings</h1>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">Recent Recordings</h2>

                    {loading ? (
                        <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-blue-500" /></div>
                    ) : (
                        <div className="grid gap-4">
                            {meetings.map((meeting) => (
                                <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                                    <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-500 transition-colors group cursor-pointer flex justify-between items-center shadow-sm">
                                        <div className="flex gap-4 items-center">
                                            <div className={cn(
                                                "w-10 h-10 rounded-full flex items-center justify-center",
                                                meeting.status === 'completed' ? "bg-green-100 text-green-600" :
                                                    meeting.status === 'processing' ? "bg-blue-100 text-blue-600" :
                                                        "bg-slate-100 text-slate-600"
                                            )}>
                                                {meeting.status === 'completed' ? <CheckCircle2 className="w-5 h-5" /> :
                                                    meeting.status === 'processing' ? <Loader2 className="animate-spin w-5 h-5" /> :
                                                        <Clock className="w-5 h-5" />}
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 transition-colors">{meeting.title}</h3>
                                                <div className="flex gap-4 text-xs text-slate-500 mt-1">
                                                    <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(meeting.date).toLocaleDateString()}</span>
                                                    <span className="uppercase tracking-wider font-medium">{meeting.status}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            {/* Show Join button ONLY for Scheduled meetings */}
                                            {meeting.status === 'scheduled' && (
                                                <Link href={`/meetings/${meeting.id}/room`} onClick={(e) => e.stopPropagation()}>
                                                    <button className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded shadow-sm transition-colors">
                                                        Join
                                                    </button>
                                                </Link>
                                            )}
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    handleDelete(meeting.id, meeting.title);
                                                }}
                                                className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                                title="Delete meeting"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <div className="text-slate-400 group-hover:translate-x-1 transition-transform">
                                                →
                                            </div>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                            {meetings.length === 0 && <p className="text-slate-500 italic">No meetings recorded yet.</p>}
                        </div>
                    )}
                </div>

                <div>
                    <UploadMeeting onUploadSuccess={loadMeetings} />
                    <ScheduleMeeting onScheduleSuccess={loadMeetings} />
                </div>
            </div>
        </div>
    );
}
