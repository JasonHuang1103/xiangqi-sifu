import { useState } from "react";

import type { CoachMessage } from "../app/types";

interface CoachPanelProps {
  messages?: CoachMessage[];
  onSend?: (question: string) => Promise<void> | void;
}


export function CoachPanel({ messages = [], onSend }: CoachPanelProps) {
  const [question, setQuestion] = useState("");
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const value = question.trim();
    if (!value || !onSend) return;
    setQuestion("");
    await onSend(value);
  };
  return (
    <aside className="coach-panel" aria-label="Ask Sifu">
      <header className="coach-header"><span className="coach-seal">師</span><div><h2>Ask Sifu</h2><p>Grounded in the position</p></div></header>
      <div className="coach-messages">
        {messages.length === 0 ? (
          <div className="coach-welcome"><p className="section-kicker">COACHING CONVERSATION</p><h3>Look first.<br />Then ask why.</h3><p>Ask about the best move, compare two ideas, or request a simpler explanation.</p></div>
        ) : messages.map((message, index) => <div key={index} className={`coach-message ${message.role}`}>{message.content}</div>)}
      </div>
      <div className="coach-prompts"><button type="button">Show the threat</button><button type="button">Compare lines</button><button type="button">Explain simply</button></div>
      <form className="coach-compose" onSubmit={submit}><label className="sr-only" htmlFor="coach-question">Ask about this position</label><input id="coach-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about this position…" disabled={!onSend} /><button type="submit" disabled={!onSend || !question.trim()}>Send</button></form>
    </aside>
  );
}
