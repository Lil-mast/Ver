"use client";

"use client";

import { useEffect, useState } from "react";

import AsciiImage from "@/components/originkit/ui/hero-32/ascii-reveal";

function asset(file: string) {
  return `/originkit/hero-32/${file}`;
}

const COLUMNS = 93;

const PORTRAIT = {
  src: asset("hero.png"),
  alt: "ASCII rendering of a figure in a mirrored visor helmet, facing forward.",
};

export const AsciiPortrait = () => {
  const [reveal, setReveal] = useState<boolean | null>(null);

  useEffect(() => {
    const pointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    const sync = () => setReveal(pointer.matches);
    sync();
    pointer.addEventListener("change", sync);
    return () => pointer.removeEventListener("change", sync);
  }, []);

  if (reveal === null) return null;

  return (
    <AsciiImage
      image={PORTRAIT}
      fit="contain"
      columns={COLUMNS}
      contrast={21}
      inkColor="#ffffff"
      reveal={reveal}

      style={{ position: "absolute", inset: 0 }}
    />
  );
};