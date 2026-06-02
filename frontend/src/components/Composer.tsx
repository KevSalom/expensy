import { ComposerPrimitive } from "@assistant-ui/react";

type Props = {
  isStreaming: boolean;
  canSend: boolean;
  onStop: () => void;
};

export function Composer({ isStreaming, canSend, onStop }: Props) {
  return (
    <ComposerPrimitive.Root className="composer">
      <ComposerPrimitive.Input
        placeholder="Escribe un gasto o una consulta..."
        rows={2}
      />
      <div className="composerActions">
        <button type="button" onClick={onStop} disabled={!isStreaming}>
          Detener
        </button>
        <ComposerPrimitive.Send disabled={!canSend}>
          Enviar
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
}