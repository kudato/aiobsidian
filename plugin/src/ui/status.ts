/**
 * The status bar item.
 *
 * There is no way to tell from the outside whether a vault is reachable, so the
 * plugin says so where the user is already looking, and clicking it stops the socket.
 */
export class StatusItem {
  readonly element: HTMLElement;

  constructor(element: HTMLElement) {
    this.element = element;
    this.element.addClass("mod-clickable");
  }

  serving(connections: number): void {
    this.#render(
      connections === 0 ? "AIO" : `AIO ${connections}`,
      connections === 0
        ? "Serving this vault. No client is connected."
        : `Serving this vault. ${connections} ${connections === 1 ? "client" : "clients"} connected.`,
    );
  }

  stopped(): void {
    this.#render("AIO off", "Not serving this vault.");
  }

  failed(message: string): void {
    this.#render("AIO error", message);
  }

  #render(text: string, tooltip: string): void {
    this.element.setText(text);
    this.element.setAttribute("aria-label", tooltip);
  }
}
