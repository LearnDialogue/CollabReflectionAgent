"use client";

import { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    createUnityInstance?: (
      canvas: HTMLCanvasElement,
      config: {
        dataUrl: string;
        frameworkUrl: string;
        codeUrl: string;
        streamingAssetsUrl?: string;
        companyName?: string;
        productName?: string;
        productVersion?: string;
        errorHandler?: (message: string, filename?: string, line?: number) => boolean | void;
        startupErrorHandler?: (message: string, filename?: string, line?: number) => void;
        showBanner?: (message: string, type?: string) => void;
      },
      onProgress?: (progress: number) => void
    ) => Promise<{
      Quit?: () => Promise<void>;
      SendMessage?: (gameObject: string, methodName: string, parameter?: string) => void;
    }>;
    unityAvatarBridge?: {
      sendState: (state: string) => void;
      sendUserMessage: (message: string) => void;
      sendAssistantMessage: (message: string) => void;
      sendGesture: (gesture: string) => void;
      sendExpression: (expression: string) => void;
      playNextGesture: () => void;
      playNextExpression: () => void;
      sendCommand: (command: {
        state?: string;
        gesture?: string;
        expression?: string;
        text?: string;
        speechText?: string;
        displayInTranscript?: boolean;
      }) => void;
    };
  }
}

const LOADER_URL = "/unity-avatar/Build/WebGL_Build.loader.js";
const BUILD_BASE = "/unity-avatar/Build";

export default function UnityAvatarPanel() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const scriptRef = useRef<HTMLScriptElement | null>(null);
  const unityInstanceRef = useRef<{
    Quit?: () => Promise<void>;
    SendMessage?: (gameObject: string, methodName: string, parameter?: string) => void;
  } | null>(null);

  const [progress, setProgress] = useState(0);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadUnity = async () => {
      if (!canvasRef.current) return;

      try {
        const existingScript = document.querySelector(
          `script[src="${LOADER_URL}"]`
        ) as HTMLScriptElement | null;

        const loaderScript =
          existingScript ??
          Object.assign(document.createElement("script"), {
            src: LOADER_URL,
            async: true,
          });

        scriptRef.current = loaderScript;

        if (!existingScript) {
          await new Promise<void>((resolve, reject) => {
            loaderScript.onload = () => resolve();
            loaderScript.onerror = () => reject(new Error("Failed to load Unity loader."));
            document.body.appendChild(loaderScript);
          });
        } else if (!window.createUnityInstance) {
          // Script tag exists but hasn't finished loading yet (e.g. React strict mode remount)
          await new Promise<void>((resolve, reject) => {
            loaderScript.addEventListener("load", () => resolve(), { once: true });
            loaderScript.addEventListener("error", () => reject(new Error("Failed to load Unity loader.")), { once: true });
          });
        }

        if (!window.createUnityInstance) {
          throw new Error("Unity loader is available, but createUnityInstance was not found.");
        }

        const instance = await window.createUnityInstance(
          canvasRef.current,
          {
            dataUrl: `${BUILD_BASE}/WebGL_Build.data`,
            frameworkUrl: `${BUILD_BASE}/WebGL_Build.framework.js`,
            codeUrl: `${BUILD_BASE}/WebGL_Build.wasm`,
            companyName: "UF Senior Project",
            productName: "Pedagogical Avatar",
            productVersion: "1.0",
            errorHandler: (message: string) => {
              console.warn("Unity runtime error (non-fatal):", message);
              // Don't show error overlay for WASM runtime errors — the avatar
              // usually keeps running fine after these.
              return true;
            },
            startupErrorHandler: (message: string) => {
              console.error("Unity startup error:", message);
              setHasError(true);
              setErrorMessage(message);
            },
            showBanner: (message: string, type?: string) => {
              if (type === "error" || type === "warning") {
                console[type === "error" ? "error" : "warn"]("Unity banner:", message);
              }
            },
          },
          (nextProgress) => {
            if (cancelled) return;
            setProgress(nextProgress);
          }
        );

        if (cancelled) {
          await instance.Quit?.();
          return;
        }

        unityInstanceRef.current = instance;
        window.unityAvatarBridge = {
          sendState: (state: string) => {
            instance.SendMessage?.("ChatLLM", "SetState", state);
          },
          sendUserMessage: (message: string) => {
            instance.SendMessage?.("ChatLLM", "OnUserMessage", message);
          },
          sendAssistantMessage: (message: string) => {
            instance.SendMessage?.("ChatLLM", "OnAssistantMessage", message);
          },
          sendGesture: (gesture: string) => {
            instance.SendMessage?.("ChatLLM", "PlayGesture", gesture);
          },
          sendExpression: (expression: string) => {
            instance.SendMessage?.("ChatLLM", "PlayExpression", expression);
          },
          playNextGesture: () => {
            instance.SendMessage?.("ChatLLM", "PlayNextGesture");
          },
          playNextExpression: () => {
            instance.SendMessage?.("ChatLLM", "PlayNextExpression");
          },
          sendCommand: (command) => {
            instance.SendMessage?.(
              "ChatLLM",
              "ReceiveLlmCommandJson",
              JSON.stringify(command)
            );
          },
        };
        setHasError(false);
        setErrorMessage("");
      } catch (error) {
        console.error("Failed to load Unity avatar:", error);
        if (!cancelled) {
          setHasError(true);
          setErrorMessage(error instanceof Error ? error.message : String(error));
        }
      }
    };

    loadUnity();

    return () => {
      cancelled = true;
      delete window.unityAvatarBridge;
      void unityInstanceRef.current?.Quit?.();
      unityInstanceRef.current = null;
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden">
      <canvas
        ref={canvasRef}
        id="unity-avatar-canvas"
        tabIndex={0}
        className="block w-full"
        style={{
          background: "transparent",
          height: "200%",
          transform: "translateY(-20%)",
        }}
      />

      {/* Loading overlay */}
      {progress < 1 && !hasError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-b from-slate-900/80 to-indigo-950/80 backdrop-blur-sm">
          <div className="h-1.5 w-48 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-white/70 transition-all duration-300"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
          <p className="text-xs text-white/50">{Math.round(progress * 100)}%</p>
        </div>
      )}

      {/* Error overlay */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/90 px-8 text-center">
          <div className="max-w-sm space-y-2">
            <p className="text-sm text-white/70">Could not load the avatar.</p>
            {errorMessage && (
              <pre className="whitespace-pre-wrap rounded-lg border border-white/10 bg-white/5 p-3 text-left text-xs text-rose-300/80">
                {errorMessage}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
