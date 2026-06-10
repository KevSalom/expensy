import { UserSessionBar } from "./UserSessionBar";
import { NewConversationButton } from "./NewConversationButton";

type Props = {
  open: boolean;
  userName: string | null;
  isAuthenticated: boolean;
  onClose: () => void;
  onClearChat: () => void;
  onLogout: () => void;
};

export function ConfigDrawer({
  open,
  userName,
  isAuthenticated,
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
          <NewConversationButton onClick={onClearChat} disabled={!isAuthenticated} />

          {isAuthenticated ? (
            <UserSessionBar userName={userName} onLogout={onLogout} />
          ) : null}
        </div>
      </aside>
    </>
  );
}
