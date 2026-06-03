'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  ImagePlus,
  ScanSearch,
  RotateCcw,
  CircleAlert,
  Sparkles,
  TriangleAlert,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { analyzeInjury } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { Reveal } from '@/components/ui/Reveal';
import { springClay } from '@/lib/motion';
import { cn } from '@/lib/cn';
import { useAuth } from '@clerk/nextjs';
import styles from './InjuryAnalyzer.module.css';

const InjuryAnalyzer: React.FC = () => {
  const { getToken } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const selectFile = (selectedFile: File) => {
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setAnalysis(null);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      selectFile(selectedFile);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      selectFile(droppedFile);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const token = await getToken() || '';
      const result = await analyzeInjury(file, token);
      setAnalysis(result.analysis);
    } catch (err: any) {
      setError(err.message || 'Something went wrong during analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Reveal inView={false} delay={0.12}>
        <Card padding="large" className={styles.uploadCard}>
          <label
            className={cn(styles.dropZone, isDragging && styles.dropZoneActive)}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className={styles.hiddenInput}
            />
            <AnimatePresence mode="wait" initial={false}>
              {preview ? (
                <motion.img
                  key="preview"
                  src={preview}
                  alt="Selected injury preview"
                  className={styles.previewImage}
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={springClay}
                />
              ) : (
                <motion.div
                  key="placeholder"
                  className={styles.placeholder}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                >
                  <motion.span
                    className={styles.placeholderIcon}
                    animate={isDragging ? { y: -6, scale: 1.08 } : { y: 0, scale: 1 }}
                    transition={springClay}
                  >
                    <ImagePlus size={34} />
                  </motion.span>
                  <span className={styles.placeholderTitle}>
                    {isDragging ? 'Drop your image here' : 'Click to upload or drag & drop'}
                  </span>
                  <span className={styles.placeholderHint}>PNG, JPG or HEIC up to a few MB</span>
                </motion.div>
              )}
            </AnimatePresence>
          </label>

          <AnimatePresence>
            {file && (
              <motion.div
                className={styles.actions}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={springClay}
              >
                <Button
                  variant="primary"
                  size="large"
                  onClick={handleAnalyze}
                  isLoading={loading}
                >
                  {loading ? (
                    <>
                      <Spinner size={18} /> Analyzing…
                    </>
                  ) : (
                    <>
                      <ScanSearch size={18} /> Analyze injury
                    </>
                  )}
                </Button>
                <label className={styles.replaceLabel}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className={styles.hiddenInput}
                  />
                  <Button as="span" variant="ghost" size="large">
                    <RotateCcw size={16} /> Replace
                  </Button>
                </label>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </Reveal>

      <AnimatePresence>
        {error && (
          <motion.div
            className={styles.error}
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={springClay}
            role="alert"
          >
            <CircleAlert size={18} className={styles.errorIcon} />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {analysis && (
        <Reveal className={styles.resultWrapper}>
          <Card padding="large" className={styles.resultCard}>
            <div className={styles.resultHeader}>
              <span className={styles.resultIcon}>
                <Sparkles size={20} />
              </span>
              <h3>Analysis result</h3>
            </div>
            <div className={styles.analysisText}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis}</ReactMarkdown>
            </div>
          </Card>

          <Card padding="medium" variant="inset" className={styles.disclaimer}>
            <TriangleAlert size={18} className={styles.disclaimerIcon} />
            <span>
              This analysis is generated by AI and is for informational purposes only.
              Consult a doctor for medical emergencies.
            </span>
          </Card>
        </Reveal>
      )}
    </div>
  );
};

export default InjuryAnalyzer;
