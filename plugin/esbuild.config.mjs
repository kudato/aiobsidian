import { builtinModules } from "node:module";

import esbuild from "esbuild";

const production = process.argv.includes("production");

/**
 * Obsidian supplies `obsidian` and Electron at runtime, and the plugin runs in a
 * Node context, so nothing in this list may be bundled.
 */
const external = [
  "obsidian",
  "electron",
  ...builtinModules,
  ...builtinModules.map((name) => `node:${name}`),
];

const context = await esbuild.context({
  entryPoints: ["src/main.ts"],
  outfile: "main.js",
  bundle: true,
  format: "cjs",
  platform: "node",
  target: "es2022",
  external,
  treeShaking: true,
  minify: production,
  sourcemap: production ? false : "inline",
  logLevel: "info",
});

if (production) {
  await context.rebuild();
  await context.dispose();
} else {
  await context.watch();
}
