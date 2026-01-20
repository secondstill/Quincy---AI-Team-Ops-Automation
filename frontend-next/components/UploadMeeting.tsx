'use client';

import React, { useState } from 'react';
import { uploadMeeting } from '@/services/api';
import { Loader2, UploadCloud } from 'lucide-react';

export default function UploadMeeting({ onUploadSuccess }: { onUploadSuccess: () => void }) {
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState('');
    const [uploading, setUploading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !title) return;

        setUploading(true);
        try {
            await uploadMeeting(file, title);
            setFile(null);
            setTitle('');
            onUploadSuccess();
        } catch (error) {
            console.error('Upload failed', error);
            alert('Upload failed. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="text-lg font-semibold mb-4 text-slate-800 dark:text-slate-200">New Meeting</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Title</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Q4 Strategy Review"
                        className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        required
                    />
                </div>

                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer relative">
                    <input
                        type="file"
                        accept="audio/*"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                        <UploadCloud className="w-8 h-8" />
                        <span className="text-sm">{file ? file.name : "Click to upload audio"}</span>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={uploading || !file || !title}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {uploading ? <Loader2 className="animate-spin w-4 h-4" /> : 'Start Processing'}
                </button>
            </form>
        </div>
    );
}
