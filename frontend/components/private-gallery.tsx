"use client";

import { useEffect, useState, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { DashboardClient } from "@/components/dashboard/dashboard-client";

export function PrivateGallery() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let live = true;
    let generation = 0;
    let currentUser: string | undefined;
    const check = async (next: Session | null) => {
      if (!live) return;
      const ticket = ++generation;
      setSession(next);
      if (currentUser !== next?.user.id || !next) setAllowed(false);
      currentUser = next?.user.id;
      if (next) {
        try {
          const { data, error } = await supabase.from("gallery_viewers")
            .select("user_id").eq("user_id", next.user.id).maybeSingle();
          if (live && ticket === generation) setAllowed(!error && !!data);
        } catch {
          if (live && ticket === generation) setAllowed(false);
        }
      }
      if (live && ticket === generation) setLoading(false);
    };
    void supabase.auth.getSession().then(({ data }) => check(data.session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, next) => {
      // Do not await Supabase calls inside the auth callback (auth lock).
      setTimeout(() => { void check(next); }, 0);
    });
    // Revoked membership clears displayed data within this interval; RLS is immediate.
    const timer = setInterval(() => {
      void supabase.auth.getSession().then(({ data }) => check(data.session));
    }, 60_000);
    return () => { live = false; subscription.unsubscribe(); clearInterval(timer); };
  }, []);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setSending(true);
    try {
      await supabase.auth.signInWithOtp({ email, options: {
        shouldCreateUser: false,
        emailRedirectTo: window.location.origin + window.location.pathname,
      }});
    } catch {
      // Keep network/account failures indistinguishable in the public UI.
    } finally {
      // Do not distinguish an unknown address from an existing account.
      setMessage("If your account is invited, check your email for a sign-in link. If it does not arrive, contact the owner.");
      setSending(false);
    }
  }

  if (loading) return <p className="p-8">Loading gallery…</p>;
  if (session && allowed) return <>
    <div className="p-4 text-right"><button onClick={() => {
      setAllowed(false); setSession(null); void supabase.auth.signOut();
    }}>Sign out</button></div>
    <DashboardClient key={session.user.id} initialDetections={[]} />
  </>;
  return <main className="mx-auto max-w-md p-8 space-y-5">
    <h1 className="text-2xl font-bold">Ghostbusters</h1>
    <p>This gallery is private. Only viewers invited by its owner can see photos.</p>
    {session ? <><p>Your account does not have gallery access.</p>
      <button onClick={() => { void supabase.auth.signOut(); }}>Use another account</button></>
      : <form onSubmit={signIn} className="space-y-4">
        <label className="block">Email
          <input className="block w-full rounded border p-2" type="email" autoComplete="email"
            required value={email} onChange={e => setEmail(e.target.value)} />
        </label>
        <button className="rounded border px-4 py-2" disabled={sending} type="submit">
          {sending ? "Sending…" : "Send sign-in link"}
        </button>
      </form>}
    <p role="status">{message}</p>
  </main>;
}
