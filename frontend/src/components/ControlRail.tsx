import type { Mode } from "../auth";

type Props = {
  mode: Mode;
  userName: string | null;
  isAuthenticated: boolean;
  onSwitchMode: (mode: Mode) => void;
  onClearChat: () => void;
  onLogout: () => void;
};

export function ControlRail({
  mode,
  userName,
  isAuthenticated,
  onSwitchMode,
  onClearChat,
  onLogout,
}: Props) {
  return (
    <aside className="controlRail" aria-label="Configuracion de Expensy">
      <div>
        <p className="eyebrow">Expensy</p>
        <h1>Gastos, en lenguaje natural.</h1>
      </div>

      {isAuthenticated ? (
        <div className="sessionInfo">
          <p className="userBadge">
            {userName ? `Hola, ${userName}` : "Modo demo"}
          </p>
          <p className="sessionModeLabel">
            Sesion activa en{" "}
            <strong>{mode === "personal" ? "Personal" : "Demo"}</strong>
          </p>
        </div>
      ) : null}

      <button
        type="button"
        className="secondaryAction"
        onClick={onClearChat}
        disabled={!isAuthenticated}
      >
        Limpiar chat
      </button>

      {isAuthenticated ? (
        <>
          <button
            type="button"
            className="secondaryAction"
            onClick={() =>
              onSwitchMode(mode === "personal" ? "demo" : "personal")
            }
          >
            Cambiar a {mode === "personal" ? "Demo" : "Personal"}
          </button>
          <button
            type="button"
            className="secondaryAction logoutAction"
            onClick={onLogout}
          >
            Cerrar sesion
          </button>
        </>
      ) : null}
    </aside>
  );
}
