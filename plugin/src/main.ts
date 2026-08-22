import fs from "node:fs";

import { FileSystemAdapter, Notice, Plugin } from "obsidian";

import { ServeError } from "./lib/errors.ts";
import {
  currentEnvironment,
  runtimeDirectory,
  socketPath as deriveSocketPath,
  vaultId,
} from "./lib/paths.ts";
import { SocketServer } from "./server/socket.ts";
import { DEFAULT_SETTINGS, parseSettings, type Settings } from "./settings.ts";
import { AioSettingTab } from "./ui/settings-tab.ts";
import { StatusItem } from "./ui/status.ts";

export default class AioPlugin extends Plugin {
  override settings: Settings = { ...DEFAULT_SETTINGS };

  /** Where this vault is listening, or `null` when it is not. */
  socketPath: string | null = null;

  /** Why it is not, when the reason is a refusal rather than a choice. */
  failure: ServeError | null = null;

  #server: SocketServer | null = null;
  #status: StatusItem | null = null;

  get serving(): boolean {
    return this.#server?.listening ?? false;
  }

  override async onload(): Promise<void> {
    this.settings = parseSettings(await this.loadData());

    const status = new StatusItem(this.addStatusBarItem());
    // `registerDomEvent` rather than `addEventListener`, so the listener leaves with
    // the plugin instead of outliving it.
    this.registerDomEvent(status.element, "click", () => {
      void this.#toggleServing();
    });
    this.#status = status;

    this.addSettingTab(new AioSettingTab(this.app, this));
    this.addCommand({
      id: "start",
      name: "Start serving this vault",
      callback: () => {
        void this.startServing();
      },
    });
    this.addCommand({
      id: "stop",
      name: "Stop serving this vault",
      callback: () => {
        void this.stopServing();
      },
    });

    if (this.settings.serve) {
      await this.startServing();
    } else {
      status.stopped();
    }
  }

  override onunload(): void {
    void this.#server?.stop();
    this.#server = null;
    this.socketPath = null;
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  /** Start listening, reporting a refusal where the user can see it. */
  async startServing(): Promise<void> {
    this.failure = null;
    try {
      const server = this.#server ?? this.#buildServer();
      this.#server = server;
      await server.start();
      this.#status?.serving(server.connectionCount);
    } catch (error) {
      this.#server = null;
      this.socketPath = null;
      const failure =
        error instanceof ServeError
          ? error
          : new ServeError("listen-failed", String(error), { cause: error });
      this.failure = failure;
      this.#status?.failed(failure.message);
      new Notice(`AIO is not serving this vault: ${failure.message}`, 10_000);
    }
  }

  /** Stop listening. The socket goes away with it, and so does every connection. */
  async stopServing(): Promise<void> {
    const server = this.#server;
    this.#server = null;
    this.socketPath = null;
    this.failure = null;
    await server?.stop();
    this.#status?.stopped();
  }

  async #toggleServing(): Promise<void> {
    this.settings.serve = !this.serving;
    await this.saveSettings();
    await (this.settings.serve ? this.startServing() : this.stopServing());
  }

  #buildServer(): SocketServer {
    const adapter = this.app.vault.adapter;
    if (!(adapter instanceof FileSystemAdapter)) {
      throw new ServeError(
        "unsupported-platform",
        "AIO serves vaults stored on a real filesystem, and this one is not.",
      );
    }

    // `realpath` before the name is derived: the client resolves the vault path the
    // same way, and a symlinked vault must not answer to two different names.
    const base = fs.realpathSync(adapter.getBasePath());
    const environment = currentEnvironment();
    const socketPath = deriveSocketPath(environment, vaultId(base, environment.platform));
    this.socketPath = socketPath;

    return new SocketServer({
      socketPath,
      directory: runtimeDirectory(environment),
      onConnection: (socket) => {
        // Nothing speaks the protocol yet, and a server that stays silent on an open
        // socket is indistinguishable from one that has hung. Closing says so.
        socket.destroy();
      },
      onConnectionsChanged: (count) => {
        if (this.serving) {
          this.#status?.serving(count);
        }
      },
      onRuntimeError: (error) => {
        this.failure = new ServeError("listen-failed", error.message, { cause: error });
        this.#status?.failed(error.message);
      },
    });
  }
}
