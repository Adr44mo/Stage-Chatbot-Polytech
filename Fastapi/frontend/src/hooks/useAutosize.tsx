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
      ref.current.style.height = "inherit";
      ref.current.style.height = `${ref.current.scrollHeight + borderWidth}px`;
    }
  }, [value, borderWidth]);

  return ref;
}

export default useAutosize;
