#!/usr/bin/env node
/**
 * package-extension.js
 * ---------------------
 * Builds a distributable .zip of the TrustLens Chrome extension that can be:
 *   - uploaded to the Chrome Web Store, or
 *   - hosted for manual ("Load unpacked" after unzip) installs.
 *
 * Usage:
 *   node package-extension.js
 *
 * Output:
 *   dist/trustlens-extension-v<version>.zip   (version read from manifest.json)
 *   ../frontend/public/trustlens-extension.zip (stable name, served for direct
 *                                               download from /get-extension)
 *
 * No external npm dependencies — uses the OS-native zip tool:
 *   - Windows: PowerShell Compress-Archive
 *   - macOS/Linux: the `zip` CLI
 */

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = __dirname;
const DIST_DIR = path.join(ROOT, "dist");
// Stable, version-less copy the website serves for one-click download.
const PUBLIC_ZIP = path.join(
  ROOT,
  "..",
  "frontend",
  "public",
  "trustlens-extension.zip"
);


// Files/dirs that make up the shippable extension.
const INCLUDE = ["manifest.json", "background", "content", "popup", "icons"];
// Never ship these even if they exist inside included dirs.
const EXCLUDE_NAMES = new Set([
  "dist",
  "node_modules",
  "package-extension.js",
  "gen-icons.js",
  ".DS_Store",
  "Thumbs.db",
]);

function readVersion() {
  const manifest = JSON.parse(
    fs.readFileSync(path.join(ROOT, "manifest.json"), "utf8")
  );
  if (!manifest.version) throw new Error("manifest.json is missing a version.");
  return manifest.version;
}

function rimraf(target) {
  if (fs.existsSync(target)) {
    fs.rmSync(target, { recursive: true, force: true });
  }
}

function ensureSourcesExist() {
  const missing = INCLUDE.filter((p) => !fs.existsSync(path.join(ROOT, p)));
  if (missing.length) {
    throw new Error(`Missing extension assets: ${missing.join(", ")}`);
  }
}

function copyInto(stageDir) {
  fs.mkdirSync(stageDir, { recursive: true });
  for (const item of INCLUDE) {
    const src = path.join(ROOT, item);
    const dest = path.join(stageDir, item);
    fs.cpSync(src, dest, {
      recursive: true,
      filter: (s) => !EXCLUDE_NAMES.has(path.basename(s)),
    });
  }
}

function zipDir(stageDir, outFile) {
  rimraf(outFile);
  if (process.platform === "win32") {
    // Compress the *contents* of stageDir so manifest.json sits at zip root.
    execFileSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-Command",
        `Compress-Archive -Path '${path.join(stageDir, "*")}' -DestinationPath '${outFile}' -Force`,
      ],
      { stdio: "inherit" }
    );
  } else {
    execFileSync("zip", ["-r", "-q", outFile, "."], {
      cwd: stageDir,
      stdio: "inherit",
    });
  }
}

function main() {
  ensureSourcesExist();
  const version = readVersion();

  fs.mkdirSync(DIST_DIR, { recursive: true });
  const stageDir = path.join(DIST_DIR, "_stage");
  rimraf(stageDir);
  copyInto(stageDir);

  const outFile = path.join(DIST_DIR, `trustlens-extension-v${version}.zip`);
  zipDir(stageDir, outFile);
  rimraf(stageDir);

  // Publish a stable-named copy the website serves for one-click download.
  fs.mkdirSync(path.dirname(PUBLIC_ZIP), { recursive: true });
  fs.copyFileSync(outFile, PUBLIC_ZIP);

  const sizeKb = (fs.statSync(outFile).size / 1024).toFixed(1);
  console.log(`\n✅ Packaged TrustLens extension v${version}`);
  console.log(`   → ${path.relative(process.cwd(), outFile)} (${sizeKb} KB)`);
  console.log(`   → ${path.relative(process.cwd(), PUBLIC_ZIP)} (served at /trustlens-extension.zip)`);
  console.log(`\nNext steps:`);
  console.log(`   • Manual install: unzip → chrome://extensions → Load unpacked`);
  console.log(`   • Web Store: upload the .zip at https://chrome.google.com/webstore/devconsole`);

}

try {
  main();
} catch (err) {
  console.error(`\n❌ Packaging failed: ${err.message}`);
  process.exit(1);
}
