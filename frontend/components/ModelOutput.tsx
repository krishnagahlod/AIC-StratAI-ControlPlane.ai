"use client";

import React from "react";

/**
 * Renders model output as formatted text.
 *
 * Models emit markdown whether or not you ask for it, and rendering it as
 * `whitespace-pre-wrap` leaves raw `**bold**` and `*` bullets on screen — which reads as
 * a broken product rather than a faithful transcript.
 *
 * Deliberately a small hand-rolled parser rather than a markdown dependency: this text is
 * untrusted model output, and the safest way to display it is to build React elements from
 * a known-small grammar and never touch `dangerouslySetInnerHTML`. It covers what models
 * actually produce here — headings, bullets, numbered lists, bold, italic and inline code —
 * and falls back to plain text for anything else.
 */

type Block =
  | { kind: "p"; lines: string[] }
  | { kind: "h"; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] };

const BULLET = /^\s*[-*•]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const HEADING = /^\s*#{1,6}\s+(.*)$/;

function parse(text: string): Block[] {
  const blocks: Block[] = [];
  for (const rawLine of text.replace(/\r\n/g, "\n").split("\n")) {
    const line = rawLine.trimEnd();
    const heading = HEADING.exec(line);
    const bullet = BULLET.exec(line);
    const numbered = NUMBERED.exec(line);
    const last = blocks[blocks.length - 1];

    if (!line.trim()) {
      if (last?.kind === "p") blocks.push({ kind: "p", lines: [] });
      continue;
    }
    if (heading) {
      blocks.push({ kind: "h", text: heading[1] });
    } else if (bullet) {
      if (last?.kind === "ul") last.items.push(bullet[1]);
      else blocks.push({ kind: "ul", items: [bullet[1]] });
    } else if (numbered) {
      if (last?.kind === "ol") last.items.push(numbered[1]);
      else blocks.push({ kind: "ol", items: [numbered[1]] });
    } else if (last?.kind === "p" && last.lines.length) {
      last.lines.push(line.trim());
    } else {
      blocks.push({ kind: "p", lines: [line.trim()] });
    }
  }
  return blocks.filter((b) => b.kind !== "p" || b.lines.length > 0);
}

/** Inline emphasis: **bold**, *italic*, `code`. Split-based, so no HTML is ever injected. */
function inline(text: string, keyPrefix: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const token = m[0];
    const key = `${keyPrefix}-${i++}`;
    if (token.startsWith("**")) {
      out.push(<strong key={key} className="font-semibold text-foreground">{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      out.push(
        <code key={key} className="font-mono text-[0.92em] bg-surface-3 rounded px-1 py-0.5">
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      out.push(<em key={key}>{token.slice(1, -1)}</em>);
    }
    last = m.index + token.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export default function ModelOutput({ text, className = "" }: { text: string; className?: string }) {
  if (!text?.trim()) {
    return <span className="text-xs text-muted-2">(empty response)</span>;
  }
  const blocks = parse(text);

  return (
    <div className={`space-y-2 ${className}`}>
      {blocks.map((b, i) => {
        if (b.kind === "h") {
          return (
            <div key={i} className="font-semibold text-foreground pt-0.5">
              {inline(b.text, `h${i}`)}
            </div>
          );
        }
        if (b.kind === "ul") {
          return (
            <ul key={i} className="list-disc pl-4 space-y-1 marker:text-muted-2">
              {b.items.map((it, j) => (
                <li key={j}>{inline(it, `u${i}-${j}`)}</li>
              ))}
            </ul>
          );
        }
        if (b.kind === "ol") {
          return (
            <ol key={i} className="list-decimal pl-4 space-y-1 marker:text-muted-2">
              {b.items.map((it, j) => (
                <li key={j}>{inline(it, `o${i}-${j}`)}</li>
              ))}
            </ol>
          );
        }
        return <p key={i}>{inline(b.lines.join(" "), `p${i}`)}</p>;
      })}
    </div>
  );
}
