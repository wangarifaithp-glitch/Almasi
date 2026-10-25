const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(
  /\/+$/,
  "",
);

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    statusText: string,
  ) {
    super(`API request failed (${status}): ${statusText}`);
    this.name = "ApiError";
  }
}

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");

  const response = await fetch(
    `${API_BASE_URL}/${path.replace(/^\/+/, "")}`,
    { credentials: "include", ...init, headers },
  );

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  return response;
}
