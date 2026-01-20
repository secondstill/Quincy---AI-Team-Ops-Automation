'use client';

import React, { useEffect, useState } from 'react';
import KanbanBoard from "@/components/KanbanBoard";
import { getCurrentUser, logout, User } from '@/services/api';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    } else {
      // Double check redirect if middleware missed it or cookie expired
      router.push('/login');
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Quincy Automation
          </h1>
          <p className="text-slate-500 dark:text-slate-400">Offline Intelligence Platform</p>
        </div>

        <div className="flex items-center gap-6">
          {user && (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{user.full_name}</p>
                <p className="text-xs text-slate-500 uppercase font-medium">{user.role}</p>
              </div>
              <div className="w-10 h-10 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-500">
                <UserIcon className="w-5 h-5" />
              </div>
            </div>
          )}

          <div className="h-8 w-px bg-slate-200 dark:bg-slate-800"></div>

          <div className="flex gap-4">
            <a href="/calendar" className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors font-medium">
              Calendar
            </a>
            <a href="/meetings" className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors font-medium">
              Meetings
            </a>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main>
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mb-2">Task Board</h2>
          <p className="text-slate-500 text-sm mb-4">Drag and drop tasks to update their status.</p>
          <KanbanBoard />
        </div>
      </main>
    </div>
  );
}
