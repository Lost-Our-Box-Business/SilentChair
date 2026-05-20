"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { sendInterviewMessage, type ChatMessage } from "@/lib/api";
import { Send, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface InterviewChatProps {
  userId: string;
  sessionId: string;
}

const WELCOME_MESSAGE: ChatMessage = {
  role: "assistant",
  content: "Hi! I'm your Business Analyst at SilentChair. I'm going to ask you a few questions to understand the business you want to build, so we can set up the perfect AI workforce for you.\n\nLet's start simple — what kind of business are you looking to create?",
};

export function InterviewChat({ userId, sessionId }: InterviewChatProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");

    const history = messages.slice(1); // skip welcome message for API history
    const newMessages: ChatMessage[] = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const result = await sendInterviewMessage({
        sessionId,
        userId,
        message: userMessage,
        history,
      });

      setMessages([...newMessages, { role: "assistant", content: result.message }]);

      if (result.is_complete) {
        setIsComplete(true);
        setTimeout(() => router.push(`/onboarding/${result.session_id}/departments`), 2000);
      }
    } catch {
      setMessages([
        ...newMessages,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 p-4 border-b shrink-0">
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary text-primary-foreground text-xs font-semibold">BA</AvatarFallback>
        </Avatar>
        <div>
          <p className="text-sm font-medium">Business Analyst</p>
          <p className="text-xs text-muted-foreground">SilentChair Onboarding</p>
        </div>
        {isComplete && (
          <Badge className="ml-auto" variant="secondary">
            Interview complete — building your team...
          </Badge>
        )}
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 max-w-2xl mx-auto">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              {msg.role === "assistant" && (
                <Avatar className="h-7 w-7 shrink-0 mt-0.5">
                  <AvatarFallback className="bg-primary text-primary-foreground text-[10px] font-semibold">BA</AvatarFallback>
                </Avatar>
              )}
              <div
                className={`rounded-2xl px-4 py-2.5 max-w-[80%] text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-tr-sm whitespace-pre-wrap"
                    : "bg-muted rounded-tl-sm"
                }`}
              >
                {msg.role === "user" ? msg.content : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
                      li: ({ children }) => <li>{children}</li>,
                      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                      em: ({ children }) => <em className="italic">{children}</em>,
                      code: ({ children }) => <code className="bg-background/50 rounded px-1 py-0.5 text-xs font-mono">{children}</code>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <Avatar className="h-7 w-7 shrink-0 mt-0.5">
                <AvatarFallback className="bg-primary text-primary-foreground text-[10px] font-semibold">BA</AvatarFallback>
              </Avatar>
              <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="p-4 border-t shrink-0">
        <div className="max-w-2xl mx-auto flex gap-2 items-end">
          <Textarea
            placeholder="Type your message… (Enter to send, Shift+Enter for newline)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || isComplete}
            rows={1}
            className="resize-none min-h-[42px] max-h-32"
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || loading || isComplete}
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-center text-[10px] text-muted-foreground mt-2">
          SilentChair uses AI — answers go toward building your business profile
        </p>
      </div>
    </div>
  );
}
