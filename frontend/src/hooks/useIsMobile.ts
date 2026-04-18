'use client';

import { useState, useEffect } from 'react';

/**
 * Détecte si l'appareil est réellement mobile (par userAgent).
 * Window width < 768px ≠ mobile réel (ex: desktop avec fenêtre étroite).
 * 
 * Retourne true seulement si:
 * - Device réel: Android, iPhone, iPad, iPod
 * - Pas si: desktop avec fenêtre resizée
 */
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Détecte le vrai type d'appareil par userAgent
    const isRealMobile = /Android|iPhone|iPad|iPod|Mobile|webOS|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
    setIsMobile(isRealMobile);
  }, []);

  return isMobile;
}
