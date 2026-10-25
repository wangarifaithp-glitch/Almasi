export function getHttpsUrl(value?: string): string | undefined {
  const candidate = value?.trim();
  if (!candidate) return undefined;

  try {
    const url = new URL(candidate);
    return url.protocol === "https:" && url.hostname ? url.toString() : undefined;
  } catch {
    return undefined;
  }
}

export function getContactDestination(value?: string): string {
  const candidate = value?.trim();
  if (!candidate) return "/#contact";

  if (candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }
  if (/^mailto:[^\s@]+@[^\s@]+\.[^\s@]+$/i.test(candidate)) {
    return candidate;
  }

  return getHttpsUrl(candidate) ?? "/#contact";
}
