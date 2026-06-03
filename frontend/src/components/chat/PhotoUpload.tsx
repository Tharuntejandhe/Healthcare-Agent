'use client';

import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ImagePlus, X } from 'lucide-react';
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
    const urls = images.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [images]);

  const handleButtonClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files || []);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (picked.length === 0) return;

    const imgs = picked.filter((f) => f.type.startsWith('image/'));
    if (imgs.length !== picked.length) toast.error('Only image files can be attached.');
    if (imgs.length === 0) return;

    const room = max - images.length;
    if (imgs.length > room) toast(`You can attach up to ${max} photos.`);
    onImagesChange([...images, ...imgs.slice(0, room)]);
  };

  const removeAt = (idx: number) => onImagesChange(images.filter((_, i) => i !== idx));

  return (
    <div className={styles.uploadContainer}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        multiple
        className={styles.hiddenInput}
      />

      {previews.map((url, i) => (
        <motion.div
          key={url}
          className={styles.previewWrapper}
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={springClay}
        >
          <img src={url} alt={`Preview ${i + 1}`} className={styles.previewImage} />
          <motion.button
            type="button"
            onClick={() => removeAt(i)}
            className={styles.clearBtn}
            title="Remove image"
            aria-label={`Remove image ${i + 1}`}
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
