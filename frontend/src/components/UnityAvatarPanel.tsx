"use client";

declare global {
  interface Window {
    unityAvatarBridge?: {
      sendState: (state: string) => void;
      sendUserMessage: (message: string) => void;
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

interface UnityAvatarPanelProps {
  imageSrc?: string;
}

export default function UnityAvatarPanel({ imageSrc = "/avatar.png" }: UnityAvatarPanelProps) {
  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden flex items-center justify-center">
      {/* Static background image representing the avatar */}
      <img
        src={imageSrc}
        alt="Robotics Teamwork Reflection Mentor"
        className="w-full h-full object-cover object-center opacity-95 transition-opacity duration-700"
      />
    </div>
  );
}
