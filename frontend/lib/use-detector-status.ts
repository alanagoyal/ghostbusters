"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export function useDetectorStatus() {
  const [running, setRunning] = useState(false);
  useEffect(() => {
    let active = true;
    let fetching = false;
    let lastSuccess = 0;
    const refresh = async () => {
      if (fetching) return;
      fetching = true;
      try {
        const { data, error } = await supabase.rpc("detector_is_running").abortSignal(AbortSignal.timeout(5000));
        if (active) {
          lastSuccess = Date.now();
          setRunning(!error && data === true);
        }
      } catch {
        if (active) setRunning(false);
      } finally {
        fetching = false;
      }
    };
    void refresh();
    const timer = setInterval(() => {
      if (Date.now() - lastSuccess > 20_000) setRunning(false);
      void refresh();
    }, 10_000);
    const visible = () => {
      if (document.visibilityState === "visible") {
        setRunning(false);
        void refresh();
      }
    };
    const offline = () => setRunning(false);
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("offline", offline);
    window.addEventListener("online", visible);
    return () => {
      active = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
      window.removeEventListener("offline", offline);
      window.removeEventListener("online", visible);
    };
  }, []);
  return running;
}
