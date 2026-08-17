import { useEffect, useCallback } from 'react'
import styles from './Lightbox.module.css'

export default function Lightbox({ src, title, onClose }) {
  const handleKey = useCallback((e) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [handleKey])

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.box} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <span>{title}</span>
          <button className={styles.close} onClick={onClose}>✕</button>
        </div>
        <img src={src} alt={title} className={styles.img} />
      </div>
    </div>
  )
}
