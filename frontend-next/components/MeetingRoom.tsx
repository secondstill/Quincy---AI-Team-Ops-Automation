'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Camera, Mic, MicOff, Video, VideoOff, PhoneOff, Loader2 } from 'lucide-react';
import { joinMeeting, endMeeting, uploadMeetingAudio } from '@/services/api';

interface MeetingRoomProps {
    meetingId: string;
    userId: string;
    userName: string;
    onLeave: () => void;
}

export default function MeetingRoom({ meetingId, userId, userName, onLeave }: MeetingRoomProps) {
    const [localStream, setLocalStream] = useState<MediaStream | null>(null);
    const [peers, setPeers] = useState<{ [key: string]: RTCPeerConnection }>({});
    const [remoteStreams, setRemoteStreams] = useState<{ [key: string]: MediaStream }>({});
    const [micOn, setMicOn] = useState(true);
    const [videoOn, setVideoOn] = useState(true);

    const [isEnding, setIsEnding] = useState(false);
    const [meetingTitle, setMeetingTitle] = useState("Meeting");

    const wsRef = useRef<WebSocket | null>(null);
    const localVideoRef = useRef<HTMLVideoElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const configuration = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' }, // Public Google STUN server
        ]
    };

    useEffect(() => {
        // Automatically join the meeting on DB level
        joinMeeting(meetingId).catch(err => console.error("Failed to join meeting", err));

        startLocalStream();
        return () => {
            localStream?.getTracks().forEach(track => track.stop());
            wsRef.current?.close();
            Object.values(peers).forEach(pc => pc.close());
        };
    }, []);

    useEffect(() => {
        if (localVideoRef.current && localStream) {
            localVideoRef.current.srcObject = localStream;
        }
    }, [localStream]);

    const startLocalStream = async () => {
        try {
            console.log("Requesting media permissions...");
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            console.log("Media stream obtained:", stream.getAudioTracks().length, "audio tracks");
            setLocalStream(stream);
            connectToSignalServer(stream);
            startRecording(stream);
        } catch (err) {
            console.error("Failed to get media", err);
            alert("Could not access camera or microphone. Please ensure you have given permissions.");
        }
    };

    const startRecording = (stream: MediaStream) => {
        try {
            // Create a new stream with only audio for recording
            const audioStream = new MediaStream(stream.getAudioTracks());
            const recorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            recorder.start(1000); // Collect data every second
            mediaRecorderRef.current = recorder;
            console.log("Recording started");
        } catch (err) {
            console.error("Failed to start recording", err);
        }
    };

    const connectToSignalServer = (stream: MediaStream) => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        // Dynamic Hostname for LAN support
        const hostname = window.location.hostname;
        const wsUrl = `${protocol}://${hostname}:8000/ws/meeting/${meetingId}/${userId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("Connected to signaling server");
            // Optionally send "join" message if simpler
            ws.send(jsonMsg({ type: "join", sender: userId }));
        };

        ws.onmessage = async (event) => {
            const msg = JSON.parse(event.data);
            handleSignalMessage(msg, stream);
        };
    };

    const jsonMsg = (data: any) => JSON.stringify(data);

    const handleSignalMessage = async (msg: any, stream: MediaStream) => {
        const sender = msg.sender || msg.userId; // user-left uses userId
        if (sender === userId) return;

        switch (msg.type) {
            case "join":
                // New user joined, we are existing user. Call them.
                createPeerConnection(sender, true, stream);
                break;
            case "offer":
                // Received offer from new user. Answer them.
                createPeerConnection(sender, false, stream, msg.payload);
                break;
            case "answer":
                if (peers[sender]) {
                    await peers[sender].setRemoteDescription(new RTCSessionDescription(msg.payload));
                }
                break;
            case "candidate":
                if (peers[sender]) {
                    await peers[sender].addIceCandidate(new RTCIceCandidate(msg.payload));
                }
                break;
            case "user-left":
                removePeer(sender);
                break;
        }
    };

    const createPeerConnection = async (targetId: string, isInitiator: boolean, stream: MediaStream, offer?: RTCSessionDescriptionInit) => {
        if (peers[targetId]) return; // Already connected

        const pc = new RTCPeerConnection(configuration);

        // Add tracks
        stream.getTracks().forEach(track => pc.addTrack(track, stream));

        // Handle ICE candidates
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                wsRef.current?.send(jsonMsg({ type: "candidate", target: targetId, sender: userId, payload: event.candidate }));
            }
        };

        // Handle remote stream
        pc.ontrack = (event) => {
            console.log("Received remote track from", targetId);
            setRemoteStreams(prev => ({
                ...prev,
                [targetId]: event.streams[0]
            }));
        };

        if (isInitiator) {
            const newOffer = await pc.createOffer();
            await pc.setLocalDescription(newOffer);
            wsRef.current?.send(jsonMsg({ type: "offer", target: targetId, sender: userId, payload: newOffer }));
        } else if (offer) {
            await pc.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            wsRef.current?.send(jsonMsg({ type: "answer", target: targetId, sender: userId, payload: answer }));
        }

        setPeers(prev => ({ ...prev, [targetId]: pc }));
    };

    const removePeer = (targetId: string) => {
        if (peers[targetId]) {
            peers[targetId].close();
            setPeers(prev => {
                const { [targetId]: deleted, ...rest } = prev;
                return rest;
            });
            setRemoteStreams(prev => {
                const { [targetId]: deleted, ...rest } = prev;
                return rest;
            });
        }
    };

    const toggleMic = () => {
        if (localStream) {
            localStream.getAudioTracks().forEach(t => t.enabled = !micOn);
            setMicOn(!micOn);
        }
    };

    const toggleVideo = () => {
        if (localStream) {
            localStream.getVideoTracks().forEach(t => t.enabled = !videoOn);
            setVideoOn(!videoOn);
        }
    };

    const handleLeave = async () => {
        if (isEnding) return;
        setIsEnding(true);

        try {
            // 1. Stop recording and get the blob
            let audioBlob: Blob | null = null;
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                const stopPromise = new Promise<Blob>((resolve) => {
                    mediaRecorderRef.current!.onstop = () => {
                        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                        resolve(blob);
                    };
                });
                mediaRecorderRef.current.stop();
                audioBlob = await stopPromise;
            }

            // 2. End meeting in DB
            await endMeeting(meetingId);

            // 3. Upload audio if we have it
            if (audioBlob && audioBlob.size > 0) {
                console.log("Uploading audio blob of size:", audioBlob.size);
                await uploadMeetingAudio(audioBlob, meetingId, meetingTitle);
                console.log("Audio upload complete");
            }
        } catch (error) {
            console.error("Failed to end meeting properly", error);
        } finally {
            onLeave();
        }
    };

    return (
        <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden relative">
            {/* Grid Container */}
            <div className="flex-1 p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Local Video */}
                <div className="relative bg-slate-800 rounded-lg overflow-hidden aspect-video border-2 border-slate-700">
                    <video ref={localVideoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                    <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 text-xs rounded">
                        {userName} (You)
                    </div>
                </div>

                {/* Remote Videos */}
                {Object.entries(remoteStreams).map(([peerId, stream]) => (
                    <RemoteVideo key={peerId} id={peerId} stream={stream} />
                ))}
            </div>

            {/* Controls */}
            <div className="p-4 bg-slate-800 flex justify-center items-center gap-4">
                {isEnding ? (
                    <div className="flex items-center gap-3 text-white">
                        <Loader2 className="animate-spin" />
                        <span>Ending meeting & processing audio...</span>
                    </div>
                ) : (
                    <>
                        <button onClick={toggleMic} className={`p-3 rounded-full ${micOn ? 'bg-slate-600 hover:bg-slate-500' : 'bg-red-500 hover:bg-red-600'} text-white transition-colors`}>
                            {micOn ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
                        </button>
                        <button onClick={toggleVideo} className={`p-3 rounded-full ${videoOn ? 'bg-slate-600 hover:bg-slate-500' : 'bg-red-500 hover:bg-red-600'} text-white transition-colors`}>
                            {videoOn ? <Video className="w-6 h-6" /> : <VideoOff className="w-6 h-6" />}
                        </button>
                        <button onClick={handleLeave} className="p-3 rounded-full bg-red-600 hover:bg-red-700 text-white transition-colors">
                            <PhoneOff className="w-6 h-6" />
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}

function RemoteVideo({ id, stream }: { id: string, stream: MediaStream }) {
    const videoRef = useRef<HTMLVideoElement>(null);
    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    return (
        <div className="relative bg-slate-800 rounded-lg overflow-hidden aspect-video border border-slate-700">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
            <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 text-xs rounded">
                User {id}
            </div>
        </div>
    );
}
