"use client";

import { useState, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type AIChatSidebarProps = {
  onBoardUpdate: (board: BoardData) => void;
};

export const AIChatSidebar = ({ onBoardUpdate }: AIChatSidebarProps) => {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }

    const history = messages;
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: trimmed, history }),
      });

      if (!response.ok) {
        const errData = (await response.json().catch(() => null)) as {
          detail?: string;
        } | null;
        throw new Error(errData?.detail || "AI request failed");
      }

      const data = (await response.json()) as {
        reply: string;
        updated: boolean;
        board: BoardData;
      };

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);

      if (data.updated) {
        onBoardUpdate(data.board);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach AI");
    } finally {
      setIsSending(false);
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-20">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white shadow-[var(--shadow)] transition hover:brightness-110"
        >
          Open AI Chat
        </button>
      </div>
    );
  }

  return (
    <aside
      aria-label="AI Assistant"
      className="flex w-full shrink-0 flex-col border-t border-[var(--stroke)] bg-white/90 p-6 backdrop-blur lg:h-screen lg:sticky lg:top-0 lg:w-[360px] lg:border-l lg:border-t-0"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="h-1.5 w-10 rounded-full bg-[var(--accent-yellow)]" />
          <h2 className="mt-3 font-display text-xl font-semibold text-[var(--navy-dark)]">
            AI Assistant
          </h2>
          <p className="mt-1 text-xs text-[var(--gray-text)]">
            Ask questions or tell AI to create, edit, or move cards.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="rounded-full border border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
        >
          Hide
        </button>
      </div>

      <div className="mt-5 flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[var(--stroke)] p-4 text-xs leading-5 text-[var(--gray-text)]">
            Try: &quot;Add a card to Backlog for API docs&quot; or &quot;Move
            card-1 to Review&quot;.
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={`${msg.role}-${index}`}
              className={
                msg.role === "user"
                  ? "ml-6 rounded-2xl bg-[var(--primary-blue)] px-4 py-3 text-sm text-white"
                  : "mr-6 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)]"
              }
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.2em] opacity-75">
                {msg.role === "user" ? "You" : "AI"}
              </p>
              <p className="whitespace-pre-wrap leading-6">{msg.content}</p>
            </div>
          ))
        )}
        {isSending && (
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Thinking...
          </p>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-3 text-xs font-medium text-red-600">
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-2">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask AI about your board..."
          aria-label="AI chat message"
          rows={2}
          className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:opacity-50"
        >
          {isSending ? "Sending..." : "Send"}
        </button>
      </form>
    </aside>
  );
};
