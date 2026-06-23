import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { login, type Mode, type Session } from "../auth";

type Props = {
  open: boolean;
  initialMode: Mode;
  onSuccess: (session: Session) => void;
};

export function LoginModal({ open, initialMode, onSuccess }: Props) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const nameRef = useRef<HTMLInputElement | null>(null);
  const passwordRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!open) return;
    setMode(initialMode);
    setError(null);
    setPassword("");
    setName("");
  }, [open, initialMode]);

  useEffect(() => {
    if (!open) return;
    const target = mode === "personal" ? nameRef.current : passwordRef.current;
    target?.focus();
  }, [open, mode]);

  if (!open) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    setError(null);

    const trimmedName = name.trim();
    if (mode === "personal" && !trimmedName) {
      setError("Escribe tu nombre");
      return;
    }
    if (mode === "personal" && !password) {
      setError("Escribe la contraseña");
      return;
    }

    setLoading(true);
    try {
      const session = await login(
        mode === "personal" ? trimmedName : null,
        mode === "personal" ? password : null,
        mode,
      );
      onSuccess(session);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="loginModalOverlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="loginModalTitle"
    >
      <form className="loginModalCard" onSubmit={handleSubmit} noValidate>
        <header className="loginModalHeader">
          <p className="loginModalEyebrow">Expensy</p>
          <h2 id="loginModalTitle" className="loginModalTitle">
            {mode === "personal" ? "Hola, vuelve a tu cuenta." : "Modo demo."}
          </h2>
          <p className="loginModalSubtitle">
            {mode === "personal"
              ? "Ingresa tu nombre y contraseña para registrar gastos."
              : "Prueba la aplicación inmediatamente en modo demo."}
          </p>
        </header>

        <div className="loginModeSwitch" role="tablist" aria-label="Modo">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "demo"}
            className={mode === "demo" ? "active" : ""}
            onClick={() => setMode("demo")}
            disabled={loading}
          >
            Demo
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "personal"}
            className={mode === "personal" ? "active" : ""}
            onClick={() => setMode("personal")}
            disabled={loading}
          >
            Personal
          </button>
        </div>

        <div className="loginForm">
          {mode === "personal" ? (
            <label className="loginField">
              <span>Nombre</span>
              <input
                ref={nameRef}
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="username"
                placeholder="kev"
                disabled={loading}
                required
              />
            </label>
          ) : null}

          {mode === "personal" ? (
            <label className="loginField">
              <span>Contraseña</span>
              <input
                ref={passwordRef}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="Tu contraseña"
                disabled={loading}
                required
              />
            </label>
          ) : (
            <p className="loginDemoMessage">
              Puedes probar todas las funcionalidades de Expensy inmediatamente. No se requiere contraseña para el modo demo.
            </p>
          )}

          {error ? (
            <p className="loginError" role="alert">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="loginSubmit"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </div>
      </form>
    </div>
  );
}
