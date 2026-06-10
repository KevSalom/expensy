import type { Mode } from "../auth";
import { UserSessionBar } from "./UserSessionBar";

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
          <UserSessionBar userName={userName} onLogout={onLogout} />
        </>
      ) : null}
    </aside>
  );
}
