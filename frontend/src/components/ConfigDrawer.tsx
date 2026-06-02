type ChatMode = "personal" | "demo";

type Props = {
  open: boolean;
  mode: ChatMode;
  token: string;
  onModeChange: (mode: ChatMode) => void;
  onTokenChange: (token: string) => void;
  onClose: () => void;
  onClearChat: () => void;
};

export function ConfigDrawer({
  open,
  mode,
  token,
  onModeChange,
  onTokenChange,
  onClose,
  onClearChat,
}: Props) {
  return (
    <>
      <div
        className={`configDrawerOverlay ${open ? "open" : ""}`}
        onClick={onClose}
      />
      <aside className={`configDrawer ${open ? "open" : ""}`} aria-label="Configuracion">
        <div className="drawerHeader">
          <h2>Configuracion</h2>
          <button
            type="button"
            className="drawerClose"
            onClick={onClose}
            aria-label="Cerrar"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="drawerContent">
          <div className="modeSwitch" aria-label="Modo de datos">
            <button
              type="button"
              className={mode === "demo" ? "active" : ""}
              onClick={() => onModeChange("demo")}
            >
              Demo
            </button>
            <button
              type="button"
              className={mode === "personal" ? "active" : ""}
              onClick={() => onModeChange("personal")}
            >
              Personal
            </button>
          </div>

          <label className="tokenField">
            <span>Contraseña {mode === "demo" ? "demo" : "personal"}</span>
            <input
              type="password"
              value={token}
              placeholder={
                mode === "demo" ? "Contraseña demo" : "Contraseña personal"
              }
              onChange={(event) => onTokenChange(event.target.value)}
            />
            <small>Usa la contraseña configurada para este modo.</small>
          </label>

          <button
            type="button"
            className="secondaryAction"
            onClick={onClearChat}
          >
            Limpiar chat
          </button>
        </div>
      </aside>
    </>
  );
}