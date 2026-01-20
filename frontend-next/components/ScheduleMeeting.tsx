'use client';

import React, { useState } from 'react';
import { scheduleMeeting } from '@/services/api';
import { Loader2, Plus, Calendar } from 'lucide-react';

interface ScheduleMeetingProps {
    onScheduleSuccess: () => void;
}

export default function ScheduleMeeting({ onScheduleSuccess }: ScheduleMeetingProps) {
    const [title, setTitle] = useState('');
    const [date, setDate] = useState('');
    const [isScheduling, setIsScheduling] = useState(false);

    const handleSchedule = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !date) return;

        setIsScheduling(true);
        try {
            // date input is YYYY-MM-DDTHH:mm, backend expects ISO or similar
            // Let's ensure it sends a valid datetime string
            const dateObj = new Date(date);
            await scheduleMeeting(title, dateObj.toISOString());
            setTitle('');
            setDate('');
            onScheduleSuccess();
        } catch (error) {
            console.error("Schedule failed", error);
            alert("Failed to schedule meeting");
        } finally {
            setIsScheduling(false);
        }
    };

    return (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm mt-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-green-500" />
                Schedule New Meeting
            </h2>
            <form onSubmit={handleSchedule} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Meeting Title</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Weekly Sync"
                        className="w-full px-3 py-2 border rounded-lg dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Date & Time</label>
                    <input
                        type="datetime-local"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        required
                    />
                </div>
                <button
                    type="submit"
                    disabled={isScheduling}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                    {isScheduling ? <Loader2 className="animate-spin w-4 h-4" /> : <Plus className="w-4 h-4" />}
                    Schedule Meeting
                </button>
            </form>
        </div>
    );
}
