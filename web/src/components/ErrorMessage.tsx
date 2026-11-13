export function ErrorMessage({ message }: Readonly<{ message: string }>) {
  return (
    <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
      {message}
    </p>
  );
}
