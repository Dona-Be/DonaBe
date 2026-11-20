import { useAuth } from "../auth/useAuth";
import { roleLabels } from "../roles";
import { ProfileForm } from "./ProfileForm";

export function MyProfile() {
  const { user, role } = useAuth();

  if (!user || !role) return null;

  return (
    <section className="rounded border border-slate-200 bg-white p-6 sm:p-8">
      <h1 className="text-4xl font-extrabold">Meu perfil</h1>
      <div className="my-6 flex flex-wrap items-center gap-4 rounded-lg bg-slate-100 p-4">
        {user.picture_url && (
          <img
            src={user.picture_url}
            alt=""
            referrerPolicy="no-referrer"
            className="size-16 rounded-full"
          />
        )}
        <div className="wrap-anywhere">
          <p className="text-xl font-bold">{user.name}</p>
          <p className="text-slate-600">{user.email}</p>
          <p className="text-slate-600">{roleLabels[role]}</p>
        </div>
      </div>
      <ProfileForm user={user} />
    </section>
  );
}
