"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

export const AuthGate = () => {
  const [username, setUsername] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    fetch("/api/auth/me", { credentials: "include" })
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const data = (await res.json()) as { username: string };
          setUsername(data.username);
        } else {
          setUsername(null);
        }
      })
      .catch(() => {
        if (active) setUsername(null);
      })
      .finally(() => {
        if (active) setChecking(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const handleLogout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setUsername(null);
  };

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
        Loading...
      </div>
    );
  }

  if (!username) {
    return <LoginForm onSuccess={setUsername} />;
  }

  return <KanbanBoard username={username} onLogout={handleLogout} />;
};
