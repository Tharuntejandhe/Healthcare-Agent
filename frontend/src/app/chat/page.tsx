"use client";

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import {
  MessagesSquare,
  Plus,
  ArrowLeft,
  Bot,
  User,
  Brain,
  Send,
  Camera,
  Volume2,
  Square,
  ShieldCheck,
  Check,
  FileSearch,
  Sparkles,
  FileText,
  Trash2,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/Button';
import { IconButton } from '@/components/ui/IconButton';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { Logo } from '@/components/ui/Logo';
import { API_BASE_URL, analyzeImage, extractErrorMessage } from '@/lib/api';
import { bubbleIn, springClay } from '@/lib/motion';
import { useAuth } from '@clerk/nextjs';
import { PhotoUpload } from '@/components/chat/PhotoUpload';
import { VoiceInput } from '@/components/chat/VoiceInput';
import { CameraCapture } from '@/components/chat/CameraCapture';
import styles from './chat.module.css';

interface Attachment {
  name: string;
  type: 'image' | 'pdf';
  url: string;
}

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  agentName?: string;
  imageUrls?: string[];
  attachments?: Attachment[];
}

interface ChatSession {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
}

export default function ChatPage() {
  const router = useRouter();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [isMounted, setIsMounted] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [usePersonalAnalysis, setUsePersonalAnalysis] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  const messages = activeSessionId 
    ? sessions.find(s => s.id === activeSessionId)?.messages || []
    : [];

  const fetchSessionMessages = async (id: string, token: string | null = null) => {
    if (!token) token = await getToken();
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(prev => prev.map(s => s.id === id ? { ...s, messages: data.messages } : s));
      }
    } catch (e) { console.error(e); }
  };

  const handleSessionSelect = async (id: string) => {
    setActiveSessionId(id);
    const session = sessions.find(s => s.id === id);
    if (session && (!session.messages || session.messages.length === 0)) {
      const token = await getToken();
      fetchSessionMessages(id, token);
    }
  };

  const setMessages = (updater: Message[] | ((prev: Message[]) => Message[])) => {
    setSessions(prevSessions => {
      let currentSession = prevSessions.find(s => s.id === activeSessionId);
      const currentMessages = currentSession?.messages || [];
      const newMessages = typeof updater === 'function' ? updater(currentMessages) : updater;

      if (!currentSession) return prevSessions;

      let title = currentSession.title;
      let titleChanged = false;
      if (title === 'New Consultation') {
        const firstUserMsg = newMessages.find(m => m.role === 'user');
        if (firstUserMsg && firstUserMsg.content.trim()) {
          title = firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '');
          titleChanged = true;
        } else if (firstUserMsg && ((firstUserMsg.imageUrls && firstUserMsg.imageUrls.length > 0) || (firstUserMsg.attachments && firstUserMsg.attachments.length > 0))) {
          title = 'Document Analysis';
          titleChanged = true;
        }
      }

      if (titleChanged) {
        getToken().then(token => {
          fetch(`${API_BASE_URL}/api/v1/chat/sessions/${activeSessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ title })
          }).catch(console.error);
        });
      }

      const updatedSession = {
        ...currentSession,
        updatedAt: Date.now(),
        messages: newMessages,
        title
      };

      return [updatedSession, ...prevSessions.filter(s => s.id !== activeSessionId)];
    });
  };

  const startNewSession = async () => {
    const newId = Date.now().toString();
    const token = await getToken();
    
    try {
      await fetch(`${API_BASE_URL}/api/v1/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id: newId, title: 'New Consultation' })
      });
    } catch (e) { console.error(e); }

    setActiveSessionId(newId);
    setSessions(prev => [
      {
        id: newId,
        title: 'New Consultation',
        updatedAt: Date.now(),
        messages: [{
          id: 'init-1',
          role: 'ai',
          content: 'Hello! I am your Healthcare AI Assistant. How can I help you today?',
          agentName: 'Support Router'
        }]
      },
      ...prev
    ]);
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    
    // Optimistic delete
    setSessions(prev => prev.filter(s => s.id !== id));
    
    // If we delete the active session, switch to another or start a new one
    if (id === activeSessionId) {
      const remaining = sessions.filter(s => s.id !== id);
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id);
        fetchSessionMessages(remaining[0].id);
      } else {
        startNewSession();
      }
    }

    try {
      const token = await getToken();
      await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  };

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;

    const loadSessions = async () => {
      try {
        const token = await getToken();
        const res = await fetch(`${API_BASE_URL}/api/v1/chat/sessions`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          // Ensure messages array exists
          const formatted = data.map((s: any) => ({ ...s, messages: s.messages || [] }));
          setSessions(formatted);
          if (formatted.length > 0) {
            setActiveSessionId(formatted[0].id);
            fetchSessionMessages(formatted[0].id, token);
          } else {
            startNewSession();
          }
        } else {
          startNewSession();
        }
      } catch {
        startNewSession();
      } finally {
        setIsMounted(true);
      }
    };
    
    loadSessions();
  }, [isLoaded, isSignedIn]);



  useEffect(() => {
    if (isMounted && isLoaded && !isSignedIn) {
      router.push('/login');
    }
  }, [isMounted, isLoaded, isSignedIn, router]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const formatAgentName = (classification: string) => {
    if (!classification) return 'AI Assistant';
    return classification
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const handleSpeak = (text: string) => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/') || file.type === 'application/pdf');
      if (files.length > 0) {
        setSelectedImages(prev => [...prev, ...files]);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputValue.trim() && selectedImages.length === 0) || isLoading) return;

    const attachments: Attachment[] = selectedImages.map((f) => ({
      name: f.name,
      type: f.type.startsWith('image/') ? 'image' : 'pdf',
      url: f.type.startsWith('image/') ? URL.createObjectURL(f) : ''
    }));

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      attachments,
    };

    const imagesToProcess = selectedImages; // Store reference before clearing
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setSelectedImages([]);
    setIsLoading(true);

    try {
      const token = await getToken() || '';

      let finalQuery = userMsg.content;
      
      const imageFiles = imagesToProcess.filter(f => f.type.startsWith('image/'));
      const pdfFiles = imagesToProcess.filter(f => f.type === 'application/pdf');

      if (pdfFiles.length > 0) {
        const uploadPromises = pdfFiles.map(async (file) => {
          const formData = new FormData();
          formData.append('file', file);
          const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
          if (!res.ok) throw new Error(`Failed to upload ${file.name}`);
        });
        await Promise.all(uploadPromises);
        
        if (!usePersonalAnalysis) {
            setUsePersonalAnalysis(true);
        }
        finalQuery = `[SYSTEM NOTE: The user just uploaded ${pdfFiles.length} document(s). Please reference them if needed.]\n\n` + finalQuery;
      }

      // If there are image(s), analyze each (in parallel) and prepend to the query.
      if (imageFiles.length > 0) {
        const analyses = await Promise.all(
          imageFiles.map((img, i) =>
            analyzeImage(img, token)
              .then((r) => `Image ${i + 1}: ${r.analysis}`)
              .catch((err) => `Image ${i + 1}: (could not be analyzed — ${err?.message || 'error'})`)
          )
        );
        finalQuery = `[IMAGE ANALYSIS CONTEXT]:\n${analyses.join('\n\n')}\n\n[USER QUERY]:\n${finalQuery || 'Based on the image(s) above, what can you tell me?'}`;
      }

      const res = await fetch(`${API_BASE_URL}/api/v1/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: finalQuery,
          use_personal_analysis: pdfFiles.length > 0 ? true : usePersonalAnalysis,
          session_id: activeSessionId
        }),
      });

      if (!res.ok) {
        throw new Error(await extractErrorMessage(res, `Server error (${res.status})`));
      }

      const data = await res.json();

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: data.response,
        agentName: formatAgentName(data.classification),
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: error.message || 'Sorry, I encountered an error while processing your request.',
        agentName: 'System Error',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isMounted) return null;

  const canSend = (inputValue.trim() !== '' || selectedImages.length > 0) && !isLoading && !isRecording;

  return (
    <div className={styles.chatWrapper}>
      {/* Consultation history sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarInner}>
          <div className={styles.sidebarHeader}>
            <Logo size="sm" />
            <div className={styles.sidebarTitle}>
              <MessagesSquare size={15} />
              Consultations
            </div>
            <Button
              variant="primary"
              fullWidth
              onClick={startNewSession}
            >
              <Plus size={18} />
              New consultation
            </Button>
          </div>

          <div className={styles.historyList}>
            {sessions.length === 0 ? (
              <div className={styles.emptyHistory}>
                <span><MessagesSquare size={22} /></span>
                <p>Your past consultations will appear here.</p>
              </div>
            ) : (
              sessions.map(session => (
                <div key={session.id} className={styles.historyItemWrapper}>
                  <button
                    className={`${styles.historyItem} ${session.id === activeSessionId ? styles.historyItemActive : ''}`}
                    onClick={() => handleSessionSelect(session.id)}
                  >
                    <span className={styles.historyItemTitle}>{session.title}</span>
                    <span className={styles.historyItemTime}>
                      {new Date(session.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </span>
                  </button>
                  <button 
                    className={styles.deleteSessionBtn} 
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    title="Delete consultation"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className={styles.sidebarFooter}>
            <Button as={Link} href="/dashboard" variant="ghost" size="small">
              <ArrowLeft size={16} />
              Dashboard
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </aside>

      <main 
        className={styles.mainChat}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.mainInner}>
          <AnimatePresence>
            {isDragging && (
              <motion.div 
                className={styles.dragOverlay}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className={styles.dragOverlayInner}>
                  <Camera size={48} />
                  <h3>Drop images here</h3>
                  <p>They will be added to your message</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <header className={styles.header}>
            <div className={styles.headerInfo}>
              <span className={styles.headerMark}>
                <Sparkles size={22} strokeWidth={2.4} />
              </span>
              <div className={styles.headerText}>
                <h2>AI Specialist Workspace</h2>
                <p>
                  <motion.span
                    className={styles.statusDot}
                    animate={{ boxShadow: ['0 0 0 0 var(--success)', '0 0 0 5px transparent'] }}
                    transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
                  />
                  Clinical Intelligence Active
                </p>
              </div>
            </div>
            <div className={styles.headerActions}>
              <Button as={Link} href="/dashboard" variant="ghost" size="small">
                <ArrowLeft size={16} />
                Back to dashboard
              </Button>
              <ThemeToggle />
            </div>
          </header>

          <div className={styles.chatArea} ref={chatAreaRef}>
            <div className={styles.chatInner}>
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    layout
                    variants={bubbleIn}
                    initial="hidden"
                    animate="show"
                    className={`${styles.messageWrapper} ${styles[msg.role]}`}
                  >
                    <div className={`${styles.avatar} ${msg.role === 'user' ? styles.userAvatar : styles.aiAvatar}`}>
                      {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                    </div>
                    <div className={styles.messageContent}>
                      {msg.role === 'ai' && <span className={styles.agentName}>{msg.agentName}</span>}
                      <div className={styles.bubble}>
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            table: ({ node, ...props }) => (
                              <div className={styles.tableScroll}>
                                <table className={styles.mdTable} {...props} />
                              </div>
                            ),
                            th: ({ node, ...props }) => <th className={styles.mdTh} {...props} />,
                            td: ({ node, ...props }) => <td className={styles.mdTd} {...props} />,
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                        {msg.imageUrls?.map((u, i) => (
                          <div key={`img-${i}`} className={styles.messageImageContainer}>
                            <img src={u} alt={`Uploaded attachment ${i + 1}`} className={styles.messageImage} />
                          </div>
                        ))}
                        {msg.attachments?.map((att, i) => (
                          <div key={`att-${i}`} className={styles.messageImageContainer}>
                            {att.type === 'image' ? (
                              <img src={att.url} alt={`Uploaded attachment ${i + 1}`} className={styles.messageImage} />
                            ) : (
                              <div className={styles.messagePdfAttachment}>
                                <FileText size={16} />
                                <span>{att.name}</span>
                              </div>
                            )}
                          </div>
                        ))}
                        {msg.role === 'ai' && (
                          <motion.button
                            type="button"
                            className={`${styles.speakBtn} ${isSpeaking ? styles.speaking : ''}`}
                            onClick={() => handleSpeak(msg.content)}
                            title={isSpeaking ? 'Stop reading' : 'Read aloud'}
                            aria-label={isSpeaking ? 'Stop reading' : 'Read aloud'}
                            whileHover={{ scale: 1.12 }}
                            whileTap={{ scale: 0.88 }}
                            // Looping 3-keyframe pulse needs a tween (spring only
                            // supports 2 keyframes); use spring for hover/tap idle.
                            transition={isSpeaking ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } : springClay}
                            animate={isSpeaking ? { scale: [1, 1.08, 1] } : { scale: 1 }}
                          >
                            {isSpeaking ? <Square size={13} fill="currentColor" /> : <Volume2 size={14} />}
                          </motion.button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {isLoading && (
                  <motion.div
                    key="loading"
                    layout
                    variants={bubbleIn}
                    initial="hidden"
                    animate="show"
                    exit={{ opacity: 0 }}
                    className={`${styles.messageWrapper} ${styles.ai}`}
                  >
                    <div className={`${styles.avatar} ${styles.aiAvatar}`}>
                      <Brain size={20} />
                    </div>
                    <div className={styles.messageContent}>
                      <span className={styles.agentName}>Processing Data</span>
                      <div className={`${styles.bubble} ${styles.loadingIndicator}`}>
                        {[0, 1, 2].map((i) => (
                          <motion.span
                            key={i}
                            className={styles.dot}
                            animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
                          />
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className={styles.inputArea}>
            <div className={styles.inputContainer}>
              <PhotoUpload images={selectedImages} onImagesChange={setSelectedImages} />
              <IconButton
                aria-label="Take photo"
                title="Take Photo"
                onClick={() => setShowCamera(true)}
              >
                <Camera size={20} />
              </IconButton>
              <VoiceInput
                onTranscript={(text) => setInputValue(prev => prev + (prev ? ' ' : '') + text)}
                onRecordingStateChange={setIsRecording}
                isLoading={isLoading}
              />
              <div className={styles.textField}>
                <AnimatePresence>
                  {isRecording && (
                    <motion.div
                      className={styles.recordingOverlay}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <div className={styles.waveContainer}>
                        {[0, 1, 2, 3, 4].map((i) => (
                          <motion.span
                            key={i}
                            className={styles.waveBar}
                            animate={{ height: ['7px', '22px', '7px'] }}
                            transition={{ duration: 0.85, repeat: Infinity, delay: i * 0.1, ease: 'easeInOut' }}
                          />
                        ))}
                      </div>
                      <span>Listening…</span>
                    </motion.div>
                  )}
                </AnimatePresence>
                <input
                  className={`${styles.inputBox} ${isRecording ? styles.inputRecording : ''}`}
                  placeholder={isRecording ? '' : 'Ask your medical query…'}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmit(e as any)}
                  disabled={isLoading || isRecording}
                />
              </div>
              <IconButton
                variant="primary"
                aria-label="Send message"
                onClick={handleSubmit}
                disabled={!canSend}
              >
                <Send size={18} />
              </IconButton>
            </div>

            <div className={styles.toggleBar}>
              <motion.button
                type="button"
                className={`${styles.toggleChip} ${usePersonalAnalysis ? styles.toggleChipActive : ''}`}
                onClick={() => setUsePersonalAnalysis(!usePersonalAnalysis)}
                whileTap={{ scale: 0.96 }}
                transition={springClay}
                aria-pressed={usePersonalAnalysis}
              >
                <span className={styles.toggleCheck}>
                  {usePersonalAnalysis ? <Check size={12} strokeWidth={3} /> : <FileSearch size={12} />}
                </span>
                Analyze my reports
              </motion.button>
              <span className={styles.encChip}>
                <ShieldCheck size={16} />
                Encrypted
              </span>
            </div>
          </div>

          <AnimatePresence>
            {showCamera && (
              <CameraCapture
                onCapture={(file) => setSelectedImages((prev) => [...prev, file])}
                onClose={() => setShowCamera(false)}
              />
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
