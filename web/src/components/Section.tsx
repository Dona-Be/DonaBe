import type { ReactNode } from "react";

export function Section({ title, children }: Readonly<{ title: string; children: ReactNode }>) {
  return (
    <section className="py-6">
      <h2 className="mb-4 text-2xl font-extrabold">{title}</h2>
      <div className="grid gap-x-4 gap-y-6 sm:grid-cols-2">{children}</div>
    </section>
  );
}
