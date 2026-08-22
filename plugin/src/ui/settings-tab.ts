import { type App, PluginSettingTab, Setting } from "obsidian";

import type AioPlugin from "../main.ts";

export class AioSettingTab extends PluginSettingTab {
  readonly #plugin: AioPlugin;

  constructor(app: App, plugin: AioPlugin) {
    super(app, plugin);
    this.#plugin = plugin;
  }

  override display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName("Serve this vault")
      .setDesc(
        "Hold a socket that programs on this machine connect to. It is a local socket, " +
          "not a network port: nothing outside this machine can reach it.",
      )
      .addToggle((toggle) =>
        toggle.setValue(this.#plugin.settings.serve).onChange(async (value) => {
          this.#plugin.settings.serve = value;
          await this.#plugin.saveSettings();
          await (value ? this.#plugin.startServing() : this.#plugin.stopServing());
          this.display();
        }),
      );

    new Setting(containerEl).setName("Socket").setDesc(this.#socketDescription()).setDisabled(true);
  }

  /** Say where the socket is, or why there is not one, in the place the user asks. */
  #socketDescription(): string {
    const failure = this.#plugin.failure;
    if (failure !== null) {
      return failure.message;
    }
    if (!this.#plugin.serving) {
      return "Not serving this vault.";
    }
    return this.#plugin.socketPath ?? "Not serving this vault.";
  }
}
