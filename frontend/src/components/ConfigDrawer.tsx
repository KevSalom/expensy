import type { Mode } from "../auth";

type Props = {
  open: boolean;
  mode: Mode;
  userName: string | null;
  isAuthenticated: boolean;
  onSwitchMode: (mode: Mode) => void;
  onClose: () => void;
  onClearChat: () => void;
  onLogout: () => void;
};

export function ConfigDrawer({
  open,
  mode,
  userName,
  isAuthenticated,
  onSwitchMode,
  onClose,
  onClearChat,
  onLogout,
}: Props) {
  return (
    <>
      <div
        className={`configDrawerOverlay ${open ? "open" : ""}`}
        onClick={onClose}
      />
      <aside
        className={`configDrawer ${open ? "open" : ""}`}
        aria-label="Configuracion"
      >
        <div className="drawerHeader">
          <h2>Configuracion</h2>
          <button
            type="button"
            className="drawerClose"
            onClick={onClose}
            aria-label="Cerrar"
          >
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="drawerContent">
          {isAuthenticated ? (
            <div className="sessionInfo">
              <p className="userBadge">
                {userName ? `Sesion: ${userName}` : "Sesion: modo demo"}
              </p>
              <p className="sessionModeLabel">
                Activa en{" "}
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
        </div>
      </aside>
    </>
  );
}
