'use client';

import React, { useState, useRef } from 'react';
import { motion } from 'motion/react';
import { Mic, Square } from 'lucide-react';
import { toast } from 'sonner';
import { transcribeAudio } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';
import { springClay } from '@/lib/motion';
import styles from './VoiceInput.module.css';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onRecordingStateChange?: (isRecording: boolean) => void;
  isLoading: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onRecordingStateChange,
  isLoading: parentLoading
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await handleTranscription(audioBlob);
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      if (onRecordingStateChange) onRecordingStateChange(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      toast.error('Could not access microphone. Please ensure permissions are granted.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (onRecordingStateChange) onRecordingStateChange(false);
    }
  };

  const handleTranscription = async (blob: Blob) => {
    // Guard against accidental taps / no audio captured.
    if (blob.size < 1200) {
      toast('Hold the mic and speak for a moment — that recording was too short.');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('access_token') || '';
      const result = await transcribeAudio(blob, token);
      const text = (result.transcript || '').trim();
      // Whisper returns "." / "" for silence — don't dump that into the input.
      if (text && text.replace(/[.\s]/g, '').length > 0) {
        onTranscript(text);
      } else {
        toast("Couldn't detect any speech. Please try again and speak clearly.");
      }
    } catch (err: any) {
      console.error('Transcription failed:', err);
      toast.error(err?.message || 'Transcription failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const disabled = loading || parentLoading;

  return (
    <div className={styles.voiceContainer}>
      <motion.button
        type="button"
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={stopRecording} // Stop if mouse leaves button
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        className={`${styles.micBtn} ${isRecording ? styles.recording : ''} ${disabled ? styles.disabled : ''}`}
        disabled={disabled}
        title="Hold to speak"
        aria-label="Hold to speak"
        whileHover={disabled ? undefined : { scale: 1.08 }}
        whileTap={disabled ? undefined : { scale: 0.9 }}
        animate={isRecording ? { scale: [1, 1.08, 1] } : { scale: 1 }}
        transition={isRecording ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } : springClay}
      >
        {loading ? (
          <Spinner size={20} />
        ) : isRecording ? (
          <Square size={14} fill="currentColor" />
        ) : (
          <Mic size={20} />
        )}
      </motion.button>
    </div>
  );
};
