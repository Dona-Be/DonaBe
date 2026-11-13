import { useSearchParams } from "react-router";
import { GOOGLE_LOGIN_URL } from "../api/auth";
import { AuthLayout } from "../components/AuthLayout";
import { SECONDARY_CLASS } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { GoogleIcon } from "../components/GoogleIcon";

const LOGIN_FAILED_MESSAGE = "Não foi possível entrar com o Google. Tente novamente.";

export function Login() {
  const [searchParams] = useSearchParams();
  const loginFailed = searchParams.get("error") === "login_failed";

  return (
    <AuthLayout title="Entrar">
      <div className="space-y-4">
        <a
          href={GOOGLE_LOGIN_URL}
          className={`${SECONDARY_CLASS} flex w-full items-center justify-center gap-3`}
        >
          <GoogleIcon />
          Entrar com o Google
        </a>
        {loginFailed && <ErrorMessage message={LOGIN_FAILED_MESSAGE} />}
        <p className="text-slate-600">
          No primeiro acesso você escolhe se quer doar ou se representa uma instituição.
        </p>
      </div>
    </AuthLayout>
  );
}
