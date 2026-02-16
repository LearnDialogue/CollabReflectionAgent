"use client";

import React, { useState } from "react";

interface LLMMetadata {
  routing_signal: string;
  stage_completed: boolean;
  reflection_data: Record<string, unknown> | null;
  model: string;
  prompt_version: string;
  forced_advance: boolean;
  response_time_ms: number;
  token_usage: { prompt: number; completion: number; total: number } | null;
  attempt_number: number;
  [key: string]: unknown;
}

interface StageInfo {
  goal: string;
  system_prompt: string;
  completion_criteria: string;
  max_turns: number;
  next_stage: string | null;
  stage_number: number;
}

interface MetadataPanelProps {
  metadata: LLMMetadata;
  stageInfo?: StageInfo | null;
  mode: "compact" | "full";
}

function Badge({
  label,
  color,
}: {
  label: string;
  color: "green" | "blue" | "yellow" | "red" | "gray";
}) {
  const colors = {
    green: "bg-green-100 text-green-800",
    blue: "bg-blue-100 text-blue-800",
    yellow: "bg-yellow-100 text-yellow-800",
    red: "bg-red-100 text-red-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[color]}`}
    >
      {label}
    </span>
  );
}

function getAdvanceReason(meta: LLMMetadata): string {
  // Use the LLM's own explanation if available
  const reflectionData = meta.reflection_data as Record<string, unknown> | null;
  if (reflectionData?.routing_reason) {
    return String(reflectionData.routing_reason);
  }
  // Fallback to generic descriptions
  if (meta.forced_advance) return "Safety valve — forced advance after max turns";
  if (meta.stage_completed && meta.routing_signal === "NEXT")
    return "LLM determined completion criteria met";
  if (meta.routing_signal === "STAY") return "Staying in current stage";
  return meta.routing_signal;
}

export default function MetadataPanel({
  metadata,
  stageInfo,
  mode,
}: MetadataPanelProps) {
  const isCompact = mode === "compact";
  const [showRawJson, setShowRawJson] = useState(false);

  return (
    <div
      className={`rounded-lg border ${
        metadata.forced_advance
          ? "border-yellow-300 bg-yellow-50"
          : "border-gray-200 bg-gray-50"
      } ${isCompact ? "p-2 text-xs" : "p-4 text-sm"}`}
    >
      {/* Signal badges row */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <Badge
          label={metadata.routing_signal}
          color={metadata.routing_signal === "NEXT" ? "green" : "blue"}
        />
        <Badge
          label={metadata.stage_completed ? "Completed" : "In Progress"}
          color={metadata.stage_completed ? "green" : "gray"}
        />
        {metadata.forced_advance && (
          <Badge label="Forced Advance" color="yellow" />
        )}
        {metadata.attempt_number === 0 && (
          <Badge label="Fallback" color="red" />
        )}
        {metadata.attempt_number > 1 && (
          <Badge label={`Attempt ${metadata.attempt_number}`} color="yellow" />
        )}
      </div>

      {/* Decision reason */}
      <p className={`${isCompact ? "text-xs" : "text-sm"} text-gray-600 mb-2`}>
        {getAdvanceReason(metadata)}
      </p>

      {/* Stats row */}
      <div className="flex flex-wrap gap-4 text-gray-500">
        {metadata.response_time_ms > 0 && (
          <span>{(metadata.response_time_ms / 1000).toFixed(1)}s</span>
        )}
        {metadata.token_usage && metadata.token_usage.total > 0 && (
          <span>
            {metadata.token_usage.total} tokens
            {!isCompact && (
              <span className="text-gray-400">
                {" "}
                ({metadata.token_usage.prompt}→{metadata.token_usage.completion})
              </span>
            )}
          </span>
        )}
        <span>{metadata.model}</span>
      </div>

      {/* Full mode: stage criteria + reflection data */}
      {!isCompact && stageInfo && (
        <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
          <div>
            <p className="font-medium text-gray-700 text-xs uppercase tracking-wide">
              Stage Goal
            </p>
            <p className="text-gray-600">{stageInfo.goal}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700 text-xs uppercase tracking-wide">
              Completion Criteria
            </p>
            <p className="text-gray-600">{stageInfo.completion_criteria}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700 text-xs uppercase tracking-wide">
              System Prompt
            </p>
            <p className="text-gray-500 text-xs whitespace-pre-wrap bg-white p-2 rounded border border-gray-100">
              {stageInfo.system_prompt}
            </p>
          </div>
        </div>
      )}

      {/* Reflection data — structured display (shown in both compact and full) */}
      {metadata.reflection_data && (() => {
        const rd = metadata.reflection_data as Record<string, string | null> | null;
        if (!rd) return null;
        return (
          <div className={`${isCompact ? "mt-2 pt-2" : "mt-3 pt-3"} border-t border-gray-200`}>
            <p className={`font-medium text-gray-700 ${isCompact ? "text-[10px]" : "text-xs"} uppercase tracking-wide mb-2`}>
              LLM Decision Reasoning
            </p>
            <div className={`space-y-2 ${isCompact ? "text-xs" : "text-sm"}`}>
              {rd.routing_reason && (
                <div className="bg-white p-2 rounded border border-gray-100">
                  <span className="text-gray-400 text-xs">Routing Reason: </span>
                  <span className="text-gray-700">{rd.routing_reason}</span>
                </div>
              )}
              {rd.criteria_met && (
                <div className="bg-white p-2 rounded border border-gray-100">
                  <span className="text-gray-400 text-xs">Criteria Assessment: </span>
                  <span className="text-gray-700">{rd.criteria_met}</span>
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                {rd.emotional_tone && (
                  <div className="bg-white px-2 py-1 rounded border border-gray-100">
                    <span className="text-gray-400 text-xs">Tone: </span>
                    <span className="text-gray-600 text-xs">{rd.emotional_tone}</span>
                  </div>
                )}
                {rd.engagement_level && (
                  <div className="bg-white px-2 py-1 rounded border border-gray-100">
                    <span className="text-gray-400 text-xs">Engagement: </span>
                    <span className="text-gray-600 text-xs">{rd.engagement_level}</span>
                  </div>
                )}
              </div>
              {rd.notable_signals && rd.notable_signals !== "null" && (
                <div className="bg-white p-2 rounded border border-gray-100">
                  <span className="text-gray-400 text-xs">Notable Signals: </span>
                  <span className="text-gray-600 text-xs">{rd.notable_signals}</span>
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* Raw JSON metadata — full mode always shows toggle, compact mode shows toggle too */}
      <div className={`${isCompact ? "mt-2" : "mt-3 pt-3 border-t border-gray-200"}`}>
        <button
          onClick={() => setShowRawJson(!showRawJson)}
          className="text-xs text-gray-500 hover:text-gray-700 font-medium"
        >
          {showRawJson ? "Hide" : "Show"} raw JSON
        </button>
        {showRawJson && (
          <pre className="mt-1 text-xs text-gray-600 bg-white p-2 rounded border border-gray-100 overflow-x-auto max-h-64 overflow-y-auto">
            {JSON.stringify(metadata, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
