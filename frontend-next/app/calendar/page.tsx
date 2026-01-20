'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchMeetings, fetchTasks, Meeting, Task } from '@/services/api';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming you have this utility

// Helper to get days in month
const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
};

export default function CalendarPage() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [tasks, setTasks] = useState<Task[]>([]); // We'll need due dates on tasks for this to be useful
    const [loading, setLoading] = useState(true);
    const [currentDate, setCurrentDate] = useState(new Date());

    const loadData = async () => {
        try {
            setLoading(true);
            const [meetingsData, tasksData] = await Promise.all([
                fetchMeetings(),
                fetchTasks()
            ]);
            setMeetings(meetingsData);
            setTasks(tasksData);
        } catch (error) {
            console.error("Failed to fetch calendar data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const daysInMonth = getDaysInMonth(currentDate.getFullYear(), currentDate.getMonth());
    const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();

    const renderCalendarDays = () => {
        const days = [];

        // Empty cells for previous month
        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(<div key={`empty-${i}`} className="h-32 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800" />);
        }

        // Days of current month
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = new Date(currentDate.getFullYear(), currentDate.getMonth(), day).toISOString().split('T')[0];

            // Filter events for this day
            const dayMeetings = meetings.filter(m => m.date.startsWith(dateStr));
            // Assuming tasks might have a due_date field in the future, for now filtering simplistic if we had it.
            // const dayTasks = tasks.filter(t => t.due_date?.startsWith(dateStr));

            days.push(
                <div key={day} className="h-32 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-2 overflow-y-auto">
                    <span className={cn(
                        "w-6 h-6 flex items-center justify-center rounded-full text-sm mb-1",
                        new Date().toDateString() === new Date(currentDate.getFullYear(), currentDate.getMonth(), day).toDateString() ? "bg-blue-600 text-white" : "text-slate-500"
                    )}>{day}</span>

                    <div className="space-y-1">
                        {dayMeetings.map(m => (
                            <Link key={m.id} href={`/meetings/${m.id}`}>
                                <div className="text-xs p-1 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 truncate cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800/50">
                                    🕐 {m.title}
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            );
        }
        return days;
    };

    const changeMonth = (offset: number) => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1));
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                        <Link href="/" className="hover:text-blue-600">Dashboard</Link> / Calendar
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Calendar</h1>
                </div>
                <div className="flex items-center gap-4">
                    <button onClick={() => changeMonth(-1)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded">←</button>
                    <h2 className="text-xl font-semibold">{currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}</h2>
                    <button onClick={() => changeMonth(1)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded">→</button>
                </div>
            </header>

            {loading ? (
                <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-blue-500" /></div>
            ) : (
                <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="grid grid-cols-7 text-center py-2 bg-slate-100 dark:bg-slate-800 font-semibold text-slate-600 dark:text-slate-300">
                        <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
                    </div>
                    <div className="grid grid-cols-7">
                        {renderCalendarDays()}
                    </div>
                </div>
            )}
        </div>
    );
}
