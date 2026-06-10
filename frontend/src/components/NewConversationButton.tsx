type Props = {
  onClick: () => void;
  disabled?: boolean;
};

export function NewConversationButton({ onClick, disabled }: Props) {
  return (
    <button
      type="button"
      className="newConversationButton"
      onClick={onClick}
      disabled={disabled}
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
        <path d="M12 5v14M5 12h14" />
      </svg>
      Nueva conversacion
    </button>
  );
}
