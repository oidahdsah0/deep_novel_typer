"use client";

import { DialogProvider } from "@/components/dialog";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return <DialogProvider>{children}</DialogProvider>;
}
