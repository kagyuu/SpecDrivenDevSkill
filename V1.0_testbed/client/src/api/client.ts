// 共通APIクライアント。docs/P002-frontend-spec.md §2(共通エラーレスポンス形式)。

export interface ApiErrorBody {
  error_code: string;
  message: string;
  details?: { field: string; reason: string }[];
}

export class ApiError extends Error {
  status: number;
  errorCode: string;
  details?: ApiErrorBody["details"];

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.status = status;
    this.errorCode = body.error_code;
    this.details = body.details;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(response.status, body as ApiErrorBody);
  }

  return body as T;
}
