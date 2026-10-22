import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

interface AskState {
  open: boolean;
  prefill: string;
  openPanel: (prefill?: string) => void;
  closePanel: () => void;
}

const AskCtx = createContext<AskState | undefined>(undefined);

export function AskProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [prefill, setPrefill] = useState("");

  const openPanel = useCallback((text = "") => {
    setPrefill(text);
    setOpen(true);
  }, []);
  const closePanel = useCallback(() => setOpen(false), []);

  return (
    <AskCtx.Provider value={{ open, prefill, openPanel, closePanel }}>
      {children}
    </AskCtx.Provider>
  );
}

export function useAsk() {
  const ctx = useContext(AskCtx);
  if (!ctx) throw new Error("useAsk must be used within AskProvider");
  return ctx;
}
