/*
 * Hook pour ajuster automatiquement la hauteur
 * d'une zone de texte en fonction de son contenu
 */

import { useState, useLayoutEffect, useRef } from "react";
import type { RefObject } from "react";

function useAutosize(value: string): RefObject<HTMLTextAreaElement | null> {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [borderWidth, setBorderWidth] = useState<number>(0);

  useLayoutEffect(() => {
    if (ref.current) {
      const style = window.getComputedStyle(ref.current);
      const top = parseFloat(style.borderTopWidth || "0");
      const bottom = parseFloat(style.borderBottomWidth || "0");
      setBorderWidth(top + bottom);
    }
  }, []);

  useLayoutEffect(() => {
    if (ref.current) {
      const el = ref.current;
      el.style.height = ""; // reset
      // Si le contenu déborde, applique scrollHeight, sinon laisse vide
      if (el.scrollHeight > el.clientHeight + 1) {
        el.style.height = `${el.scrollHeight + borderWidth}px`;
      }
    }
  }, [value, borderWidth]);

  // Recalcule la hauteur sur resize de la fenêtre
  useLayoutEffect(() => {
    const handleResize = () => {
      if (ref.current) {
        ref.current.style.height = "auto";
        ref.current.style.height = `${
          ref.current.scrollHeight + borderWidth
        }px`;
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [borderWidth]);

  return ref;
}

export default useAutosize;
