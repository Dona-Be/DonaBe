export function ErrorMessage({ message }: Readonly<{ message: string }>) {
  return (
    <p role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      {message}
    </p>
  );
}
