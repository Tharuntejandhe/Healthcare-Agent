'use client';

import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { X, AlertTriangle } from 'lucide-react';
import { overlayFade, modalPop, springClay } from '@/lib/motion';
import styles from './CameraCapture.module.css';

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user' },
          audio: false
        });
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      } catch (err) {
        console.error('Error accessing camera:', err);
        setError('Could not access camera. Please check permissions.');
      }
    };

    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
            onCapture(file);
            stopCamera();
            onClose();
          }
        }, 'image/jpeg', 0.8);
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  return (
    <motion.div
      className={styles.overlay}
      variants={overlayFade}
      initial="hidden"
      animate="show"
      exit="exit"
      onClick={() => { stopCamera(); onClose(); }}
    >
      <motion.div
        className={styles.modal}
        variants={modalPop}
        initial="hidden"
        animate="show"
        exit="exit"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <h3>Capture image</h3>
          <motion.button
            type="button"
            onClick={() => { stopCamera(); onClose(); }}
            className={styles.closeBtn}
            aria-label="Close camera"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            transition={springClay}
          >
            <X size={18} />
          </motion.button>
        </div>

        <div className={styles.videoContainer}>
          {error ? (
            <div className={styles.error}>
              <AlertTriangle size={28} />
              <span>{error}</span>
            </div>
          ) : (
            <video ref={videoRef} autoPlay playsInline className={styles.video} />
          )}
        </div>

        <div className={styles.footer}>
          {!error && (
            <motion.button
              type="button"
              onClick={capturePhoto}
              className={styles.captureBtn}
              aria-label="Capture photo"
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.9 }}
              transition={springClay}
            >
              <span className={styles.innerCircle} />
            </motion.button>
          )}
        </div>
      </motion.div>
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </motion.div>
  );
};
