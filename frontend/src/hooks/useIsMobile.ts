'use client';

import { useState, useEffect } from 'react';

/**
 * Retourne true si la largeur de l'écran est < 768px (mobile / tablette portrait).
 * Utilise un event listener resize pour réagir aux changements.
 */
export function useIsMobile(breakpoint = 768): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < breakpoint);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, [breakpoint]);

  return isMobile;
}
