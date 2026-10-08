import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { GOOGLE_LOGIN_URL, readPendingSignup, signUp } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { BUTTON_CLASS, Button } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { Loading } from "../components/Loading";
import { friendlyMessage } from "../errors";
import type { PendingSignup, Role } from "../types/user";

const LOGIN_FAILED_MESSAGE = "Não foi possível entrar com o Google. Tente novamente.";

type PendingSignupQuery =
  | { stage: "loading" }
  | { stage: "none"; errorMessage?: string }
  | { stage: "pending"; signup: PendingSignup };

function GoogleLogin({ errorMessage }: Readonly<{ errorMessage?: string }>) {
  return (
    <>
      <h1 className="text-2xl font-semibold">Entrar no DonaBe</h1>
      {errorMessage && <ErrorMessage message={errorMessage} />}
      <p className="text-slate-600">
        Use sua conta Google. No primeiro acesso você escolhe se é doador ou se representa uma
        instituição.
      </p>
      <a href={GOOGLE_LOGIN_URL} className={BUTTON_CLASS}>
        Entrar com Google
      </a>
    </>
  );
}

function RoleChoice({ signup }: Readonly<{ signup: PendingSignup }>) {
  const { setUser } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function choose(role: Role) {
    setSubmitting(true);
    setErrorMessage(null);
    signUp(role)
      .then(setUser)
      .catch((error: unknown) => setErrorMessage(friendlyMessage(error)))
      .finally(() => setSubmitting(false));
  }

  return (
    <>
      <h1 className="text-2xl font-semibold">Boas-vindas ao DonaBe</h1>
      <div className="flex items-center justify-center gap-3">
        {signup.picture_url && (
          <img
            src={signup.picture_url}
            alt=""
            referrerPolicy="no-referrer"
            className="h-12 w-12 rounded-full"
          />
        )}
        <div className="text-left">
          <p className="font-medium">{signup.name}</p>
          <p className="text-sm text-slate-600">{signup.email}</p>
        </div>
      </div>
      <p className="text-slate-600">
        Como você vai usar o DonaBe? Esta escolha não pode ser alterada depois.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        <Button disabled={submitting} onClick={() => choose("donor")}>
          Sou doador
        </Button>
        <Button disabled={submitting} onClick={() => choose("manager")}>
          Represento uma instituição
        </Button>
      </div>
      {errorMessage && (
        <>
          <ErrorMessage message={errorMessage} />
          <a href={GOOGLE_LOGIN_URL} className="inline-block text-sm text-emerald-700 underline">
            Entrar com Google novamente
          </a>
        </>
      )}
    </>
  );
}

export function Login() {
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState<PendingSignupQuery>({ stage: "loading" });
  const loginError =
    searchParams.get("error") === "login_failed" ? LOGIN_FAILED_MESSAGE : undefined;

  useEffect(() => {
    let cancelled = false;
    readPendingSignup()
      .then((signup) => {
        if (!cancelled) setQuery(signup ? { stage: "pending", signup } : { stage: "none" });
      })
      .catch((error: unknown) => {
        if (!cancelled) setQuery({ stage: "none", errorMessage: friendlyMessage(error) });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mx-auto max-w-md space-y-4 rounded border border-slate-200 bg-white p-6 text-center">
      {query.stage === "loading" && <Loading />}
      {query.stage === "pending" && <RoleChoice signup={query.signup} />}
      {query.stage === "none" && <GoogleLogin errorMessage={loginError ?? query.errorMessage} />}
    </section>
  );
}
