export class FriendlyError extends Error {
  readonly httpStatus: number | null;

  constructor(message: string, httpStatus: number | null = null) {
    super(message);
    this.httpStatus = httpStatus;
  }
}

export function friendlyMessage(error: unknown): string {
  if (error instanceof FriendlyError) return error.message;
  return "Algo deu errado. Tente novamente.";
}
