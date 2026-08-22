import fs from "node:fs";
import path from "node:path";

import { apiVersion, FileSystemAdapter, Notice, Plugin } from "obsidian";

import { buildRegistry } from "./api/index.ts";
import { ServeError } from "./lib/errors.ts";
import {
  currentEnvironment,
  type Environment,
  runtimeDirectory,
  socketPath as deriveSocketPath,
  tokenPath,
  vaultId,
} from "./lib/paths.ts";
import { loadOrCreateToken } from "./server/auth.ts";
import { ensureRuntimeDirectory } from "./server/directory.ts";
import { Sessions } from "./server/sessions.ts";
import { SocketServer } from "./server/socket.ts";
import { DEFAULT_SETTINGS, parseSettings, type Settings } from "./settings.ts";
import { AioSettingTab } from "./ui/settings-tab.ts";
import { StatusItem } from "./ui/status.ts";

/** Everything derived from where the vault sits on disk. */
interface Location {
  readonly environment: Environment;
  readonly id: string;
  readonly name: string;
  readonly base: string;
  readonly socketPath: string;
  readonly tokenPath: string;
}

export default class AioPlugin extends Plugin {
  override settings: Settings = { ...DEFAULT_SETTINGS };

  /** Where this vault is listening, or `null` when it is not. */
  socketPath: string | null = null;

  /** Why it is not, when the reason is a refusal rather than a choice. */
  failure: ServeError | null = null;

  #server: SocketServer | null = null;
  #sessions: Sessions | null = null;
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
    this.#sessions?.closeAll("unloading");
    this.#sessions = null;
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
      const server = this.#server ?? (await this.#buildServer());
      this.#server = server;
      await server.start();
      this.#status?.serving(server.connectionCount);
    } catch (error) {
      this.#server = null;
      this.#sessions = null;
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
    // Say goodbye before the socket goes, so a client learns why rather than finding
    // out from a dead connection.
    this.#sessions?.closeAll("stopped");
    this.#sessions = null;
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

  async #buildServer(): Promise<SocketServer> {
    const location = this.#locate();
    this.socketPath = location.socketPath;

    const onWindows = location.environment.platform === "win32";
    // The token has to exist before a single client is accepted, and on Windows its
    // directory is not the socket's, so it is created and checked here rather than
    // inside the server.
    await ensureRuntimeDirectory(path.dirname(location.tokenPath), !onWindows);
    const token = await loadOrCreateToken(location.tokenPath, !onWindows);

    const sessions = new Sessions({
      token,
      registry: buildRegistry({ app: this.app, settings: () => this.settings }),
      describe: () => ({
        plugin_version: this.manifest.version,
        obsidian_version: apiVersion,
        vault: { id: location.id, name: location.name, path: location.base },
      }),
    });
    this.#sessions = sessions;

    return new SocketServer({
      socketPath: location.socketPath,
      directory: runtimeDirectory(location.environment),
      onConnection: (socket) => {
        sessions.accept(socket);
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

  #locate(): Location {
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
    const id = vaultId(base, environment.platform);
    return {
      environment,
      id,
      name: this.app.vault.getName(),
      base,
      socketPath: deriveSocketPath(environment, id),
      tokenPath: tokenPath(environment, id),
    };
  }
}
