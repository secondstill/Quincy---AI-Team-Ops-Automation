'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MeetingRoom from '@/components/MeetingRoom';
import { getCurrentUser, User } from '@/services/api';
import { Loader2 } from 'lucide-react';

export default function LiveMeetingPage() {
    const params = useParams();
    const router = useRouter();
    const id = params?.id as string;
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        const currentUser = getCurrentUser();
        if (!currentUser) {
            router.push('/login');
            return;
        }
        setUser(currentUser);
    }, []);

    const handleLeave = () => {
        router.push(`/meetings/${id}`);
    };

    if (!user) {
        return <div className="min-h-screen bg-slate-950 flex items-center justify-center"><Loader2 className="animate-spin text-blue-500 w-8 h-8" /></div>;
    }

    return (
        <div className="h-screen bg-black text-white p-4">
            <header className="absolute top-4 left-4 z-10 bg-black/50 px-3 py-1 rounded text-sm text-slate-300">
                Meeting ID: {id}
            </header>
            <MeetingRoom
                meetingId={id}
                userId={user.username} // using username as ID for signaling simplicity
                userName={user.full_name}
                onLeave={handleLeave}
            />
        </div>
    );
}
