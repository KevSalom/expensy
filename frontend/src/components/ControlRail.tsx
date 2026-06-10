import { UserSessionBar } from "./UserSessionBar";
import { NewConversationButton } from "./NewConversationButton";

type Props = {
  userName: string | null;
  isAuthenticated: boolean;
  onClearChat: () => void;
  onLogout: () => void;
};

export function ControlRail({
  userName,
  isAuthenticated,
  onClearChat,
  onLogout,
}: Props) {
  return (
    <aside className="controlRail" aria-label="Configuracion de Expensy">
      <div className="controlRailHeader">
        <div>
          <p className="eyebrow">Expensy</p>
          <h1>Gastos, en lenguaje natural.</h1>
        </div>
        <NewConversationButton onClick={onClearChat} disabled={!isAuthenticated} />
      </div>

      {isAuthenticated ? (
        <UserSessionBar userName={userName} onLogout={onLogout} />
      ) : null}
    </aside>
  );
}
