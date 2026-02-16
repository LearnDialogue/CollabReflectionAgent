"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy /chat route — redirects to the new dashboard.
 */
export default function ChatRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);
  return null;
}
