'use client';

import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ImagePlus, X, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { springClay } from '@/lib/motion';
import styles from './PhotoUpload.module.css';

interface PhotoUploadProps {
  images: File[];
  onImagesChange: (files: File[]) => void;
  max?: number;
}

export const PhotoUpload: React.FC<PhotoUploadProps> = ({ images, onImagesChange, max = 5 }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<string[]>([]);

  useEffect(() => {
    const urls = images.map((f) => f.type.startsWith('image/') ? URL.createObjectURL(f) : '');
    setPreviews(urls);
    return () => urls.forEach((u) => { if (u) URL.revokeObjectURL(u) });
  }, [images]);

  const handleButtonClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files || []);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (picked.length === 0) return;

    const valid = picked.filter((f) => f.type.startsWith('image/') || f.type === 'application/pdf');
    if (valid.length !== picked.length) toast.error('Only images and PDFs can be attached.');
    if (valid.length === 0) return;

    const room = max - images.length;
    if (valid.length > room) toast(`You can attach up to ${max} files.`);
    onImagesChange([...images, ...valid.slice(0, room)]);
  };

  const removeAt = (idx: number) => onImagesChange(images.filter((_, i) => i !== idx));

  return (
    <div className={styles.uploadContainer}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf,image/*"
        multiple
        className={styles.hiddenInput}
      />

      {images.map((file, i) => (
        <motion.div
          key={i}
          className={styles.previewWrapper}
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={springClay}
        >
          {file.type.startsWith('image/') ? (
            <img src={previews[i]} alt={`Preview ${i + 1}`} className={styles.previewImage} />
          ) : (
            <div className={styles.previewPdf}>
              <FileText size={24} />
              <span className={styles.pdfName}>{file.name.slice(0, 10)}...</span>
            </div>
          )}
          <motion.button
            type="button"
            onClick={() => removeAt(i)}
            className={styles.clearBtn}
            title="Remove file"
            aria-label={`Remove file ${i + 1}`}
            whileHover={{ scale: 1.15 }}
            whileTap={{ scale: 0.85 }}
            transition={springClay}
          >
            <X size={12} strokeWidth={3} />
          </motion.button>
        </motion.div>
      ))}

      {images.length < max && (
        <motion.button
          type="button"
          onClick={handleButtonClick}
          className={styles.uploadBtn}
          title="Attach photo(s)"
          aria-label="Attach photos"
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.9 }}
          transition={springClay}
        >
          <ImagePlus size={20} />
        </motion.button>
      )}
    </div>
  );
};
