const LOCAL_DEV_API_URL = "http://localhost:8000";

function normalizeApiUrl(value: string | undefined): string {
  const trimmed = (value || "").trim();
  const unquoted = trimmed.replace(/^['\"]|['\"]$/g, "");
  return (unquoted || LOCAL_DEV_API_URL).replace(/\/+$/, "");
}

function getFrontendHostname(): string {
  if (typeof window === "undefined") return "";
  return window.location.hostname.toLowerCase();
}

function isPrivateIpv4(hostname: string): boolean {
  const parts = hostname.split(".").map((x) => Number(x));
  if (parts.length !== 4 || parts.some((x) => Number.isNaN(x) || x < 0 || x > 255)) {
    return false;
  }
  return (
    parts[0] === 10 ||
    (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
    (parts[0] === 192 && parts[1] === 168)
  );
}

function isLocalFrontendHost(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "::1" ||
    hostname === "0.0.0.0" ||
    hostname.endsWith(".local") ||
    isPrivateIpv4(hostname)
  );
}

function getHostBasedLocalApiUrl(hostname: string): string | null {
  if (!hostname) return null;
  if (hostname.includes(":")) return null; // Ignore IPv6 hostnames for simplicity.
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1") {
    return null;
  }
  if (hostname === "0.0.0.0") {
    return LOCAL_DEV_API_URL;
  }
  return `http://${hostname}:8000`;
}

export function getConfiguredApiUrl(): string {
  return normalizeApiUrl(process.env.NEXT_PUBLIC_API_URL);
}

export function getApiBaseCandidates(preferred?: string | null): string[] {
  const candidates: string[] = [];

  if (preferred) {
    candidates.push(normalizeApiUrl(preferred));
  }

  const hostname = getFrontendHostname();
  if (isLocalFrontendHost(hostname)) {
    candidates.push(LOCAL_DEV_API_URL);
    const hostBased = getHostBasedLocalApiUrl(hostname);
    if (hostBased) {
      candidates.push(hostBased);
    }
  }

  const configured = getConfiguredApiUrl();
  candidates.push(configured);

  return Array.from(new Set(candidates));
}
