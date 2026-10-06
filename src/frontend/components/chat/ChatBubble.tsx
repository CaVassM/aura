import { Sparkles } from "lucide-react";
import { ChatMessage } from "@/lib/types";

export default function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-br-md bg-aura-teal px-4 py-3 text-sm leading-relaxed text-white">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-aura-teal text-white">
        <Sparkles size={15} />
      </div>
      <div className="max-w-[75%] rounded-2xl rounded-tl-md border border-aura-border bg-white px-4 py-3 text-sm leading-relaxed text-aura-navy shadow-card">
        {message.text}
      </div>
    </div>
  );
}
