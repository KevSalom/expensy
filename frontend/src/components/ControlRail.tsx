type ChatMode = "personal" | "demo";

type Props = {
  mode: ChatMode;
  token: string;
  onModeChange: (mode: ChatMode) => void;
  onTokenChange: (token: string) => void;
  onClearChat: () => void;
};

export function ControlRail({
  mode,
  token,
  onModeChange,
  onTokenChange,
  onClearChat,
}: Props) {
  return (
    <aside className="controlRail" aria-label="Configuracion de Expensy">
      <div>
        <p className="eyebrow">Expensy</p>
        <h1>Gastos, en lenguaje natural.</h1>
      </div>

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
    </aside>
  );
}