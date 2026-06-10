type Props = {
  userName: string | null;
  onLogout: () => void;
};

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function UserSessionBar({ userName, onLogout }: Props) {
  const displayName = userName ? capitalize(userName) : "Demo";
  const initial = displayName.charAt(0);

  return (
    <div className="userSessionBar">
      <div className="userSessionInfo">
        <span className="userAvatar">{initial}</span>
        <span className="userBadge">
          {displayName}
        </span>
      </div>
      <button
        type="button"
        className="iconButton logoutButton"
        onClick={onLogout}
        aria-label="Cerrar sesion"
      >
        <svg
          viewBox="0 0 24 24"
          width="16"
          height="16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </div>
  );
}
