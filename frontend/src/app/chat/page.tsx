"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { sessionsApi } from "@/lib/api";

// Types
interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  stage_id: string;
  created_at: string;
}

interface Session {
  id: string;
  student_id: string;
  status: "ACTIVE" | "COMPLETED";
  current_stage: string;
  started_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const { user, isLoading: authLoading, logout } = useAuth();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  // Load or create session on mount
  useEffect(() => {
    if (user) {
      loadOrCreateSession();
    }
  }, [user]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadOrCreateSession = async () => {
    setIsLoadingSession(true);
    try {
      // Check for existing active session
      const { items } = await sessionsApi.list(1, 10);
      const activeSession = items.find(
        (s: Session) => s.status === "ACTIVE"
      );

      if (activeSession) {
        setSession(activeSession);
        // Load existing messages
        const existingMessages = await sessionsApi.getMessages(activeSession.id);
        setMessages(existingMessages);
      } else {
        // Create new session
        const newSession = await sessionsApi.create();
        setSession(newSession);
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to load/create session:", error);
    } finally {
      setIsLoadingSession(false);
    }
  };

  const sendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || !session || isSending) return;

    const messageContent = input.trim();
    setInput("");
    setIsSending(true);

    try {
      const response = await sessionsApi.chat(session.id, messageContent);
      
      // Add both messages to the list
      setMessages((prev: Message[]) => [
        ...prev,
        response.user_message,
        response.assistant_message,
      ]);

      // Update session state
      setSession((prev: Session | null) =>
        prev
          ? {
              ...prev,
              current_stage: response.current_stage,
              status: response.session_status,
            }
          : null
      );
    } catch (error) {
      console.error("Failed to send message:", error);
      // Could show error toast here
    } finally {
      setIsSending(false);
    }
  };

  const startNewSession = async () => {
    if (session && session.status === "ACTIVE") {
      // Complete current session first
      await sessionsApi.complete(session.id);
    }
    // Create new session
    const newSession = await sessionsApi.create();
    setSession(newSession);
    setMessages([]);
  };

  if (authLoading || isLoadingSession) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <main className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Reflection Session
          </h1>
          <p className="text-sm text-gray-500">
            Stage: {session?.current_stage || "Loading..."}
            {session?.status === "COMPLETED" && " (Completed)"}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {user.display_name || user.username}
          </span>
          <button
            onClick={startNewSession}
            className="text-sm bg-primary-100 text-primary-700 px-3 py-1.5 rounded-md hover:bg-primary-200 transition-colors"
          >
            New Session
          </button>
          <button
            onClick={logout}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-messages">
        {messages.length === 0 && !isSending && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Welcome to your reflection session!</p>
            <p className="text-sm mt-2">
              Type a message below to start the conversation.
            </p>
          </div>
        )}

        {messages.map((message: Message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={
                message.role === "user" ? "message-user" : "message-assistant"
              }
            >
              {message.content}
            </div>
          </div>
        ))}

        {isSending && (
          <div className="flex justify-start">
            <div className="message-assistant">
              <span className="inline-flex gap-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={sendMessage} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            placeholder={
              session?.status === "COMPLETED"
                ? "Session completed. Start a new session to continue."
                : "Type your message..."
            }
            disabled={session?.status === "COMPLETED" || isSending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={
              !input.trim() || session?.status === "COMPLETED" || isSending
            }
            className="bg-primary-600 text-white px-6 py-2 rounded-full hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}
