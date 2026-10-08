import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(SCRIPT_DIR, "..");
const DEFAULT_REFERENCE = path.resolve(SKILL_DIR, "../../styles/shuimu-qinglv/assets/reference.pptx");
const REORDER_SCRIPT = path.join(SCRIPT_DIR, "reorder_body_layers.py");
const SOURCE_SLIDE_INDEX = 3;
const SLIDE_WIDTH = 1280;
const SLIDE_HEIGHT = 720;

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected argument: ${token}`);
    }
    const key = token.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    args[key] = value;
    index += 1;
  }
  return args;
}

function requireArg(args, name) {
  const value = args[name];
  if (!value) {
    throw new Error(`Missing required argument --${name}`);
  }
  return value;
}

function isHeaderBackground(shape) {
  const position = shape.position ?? {};
  return (
    shape.name === "单圆角矩形 6" &&
    position.top < 2 &&
    position.height > 70 &&
    position.height < 85
  );
}

function isHeaderTitle(shape) {
  const text = shape.text?.toString?.() ?? "";
  const position = shape.position ?? {};
  return text.includes("此处输入小标题") && position.top < 20;
}

function isHeaderLogo(image) {
  const position = image.position ?? {};
  return position.top < 25 && position.left > 900 && position.height < 70;
}

async function loadArtifactTool(workspace) {
  const require = createRequire(import.meta.url);
  let resolved;
  try {
    resolved = require.resolve("@oai/artifact-tool", { paths: [workspace] });
  } catch {
    throw new Error(
      `Cannot resolve @oai/artifact-tool from ${workspace}. Run setup_artifact_tool_workspace.mjs first.`,
    );
  }
  return import(pathToFileURL(resolved).href);
}

async function readManifest(manifestPath, imagesDir) {
  const parsed = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  if (!parsed || !Array.isArray(parsed.slides) || parsed.slides.length === 0) {
    throw new Error("manifest.json must contain a non-empty slides array");
  }

  const seen = new Set();
  const slides = [];
  for (let index = 0; index < parsed.slides.length; index += 1) {
    const entry = parsed.slides[index];
    const label = `slides[${index}]`;
    if (!entry || typeof entry !== "object") {
      throw new Error(`${label} must be an object`);
    }
    if (typeof entry.image !== "string" || entry.image.trim() === "") {
      throw new Error(`${label}.image must be a non-empty string`);
    }
    if (path.basename(entry.image) !== entry.image) {
      throw new Error(`${label}.image must be a file name inside --images, not a path`);
    }
    if (!/\.(png|jpe?g|webp)$/i.test(entry.image)) {
      throw new Error(`${label}.image must be PNG, JPEG, or WebP`);
    }
    if (seen.has(entry.image)) {
      throw new Error(`${label}.image is duplicated: ${entry.image}`);
    }
    seen.add(entry.image);

    const header = entry.header === true;
    if (entry.header !== true && entry.header !== false) {
      throw new Error(`${label}.header must be true or false`);
    }
    const title = typeof entry.title === "string" ? entry.title.trim() : "";
    if (header && title === "") {
      throw new Error(`${label}.title is required when header is true`);
    }
    if (header && /[\r\n]/.test(title)) {
      throw new Error(`${label}.title must stay on one line`);
    }
    if (header && Array.from(title).length > 24) {
      throw new Error(`${label}.title must be 24 characters or fewer to avoid the original logo area`);
    }

    const imagePath = path.resolve(imagesDir, entry.image);
    const stat = await fs.stat(imagePath).catch(() => undefined);
    if (!stat?.isFile()) {
      throw new Error(`${label}.image does not exist: ${imagePath}`);
    }
    slides.push({
      image: entry.image,
      imagePath,
      role: typeof entry.role === "string" ? entry.role : "content",
      header,
      title,
    });
  }
  return slides;
}

async function imageConfig(imagePath) {
  const extension = path.extname(imagePath).toLowerCase();
  const contentTypes = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
  };
  const bytes = await fs.readFile(imagePath);
  return {
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: contentTypes[extension],
    alt: `Generated slide body: ${path.basename(imagePath)}`,
    fit: "cover",
    position: { left: 0, top: 0, width: SLIDE_WIDTH, height: SLIDE_HEIGHT },
  };
}

function keepOnlyHeader(slide, keepHeader, title) {
  let titleShape;
  let backgroundShape;

  for (const shape of [...slide.shapes.items]) {
    if (keepHeader && isHeaderBackground(shape)) {
      if (backgroundShape) {
        throw new Error("Found more than one candidate header background");
      }
      backgroundShape = shape;
      continue;
    }
    if (keepHeader && isHeaderTitle(shape)) {
      titleShape = shape;
      continue;
    }
    shape.delete();
  }

  let sourceLogoCount = 0;
  for (const image of [...slide.images.items]) {
    if (keepHeader && isHeaderLogo(image)) {
      sourceLogoCount += 1;
      continue;
    }
    image.delete();
  }

  if (!keepHeader) {
    return undefined;
  }
  if (!backgroundShape || sourceLogoCount !== 1 || !titleShape) {
    throw new Error(
      `Could not isolate the original header objects (background=${Boolean(backgroundShape)}, logo=${sourceLogoCount}, title=${Boolean(titleShape)})`,
    );
  }
  titleShape.text.replace("此处输入小标题", title);
  return { backgroundShape, titleShape };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const workspace = path.resolve(requireArg(args, "workspace"));
  const imagesDir = path.resolve(requireArg(args, "images"));
  const manifestPath = path.resolve(requireArg(args, "manifest"));
  const outPath = path.resolve(requireArg(args, "out"));
  const referencePath = path.resolve(args.reference ?? DEFAULT_REFERENCE);
  const pythonBin = args.python ?? process.env.PYTHON_BIN ?? "python3";

  const referenceStat = await fs.stat(referencePath).catch(() => undefined);
  if (!referenceStat?.isFile()) {
    throw new Error(`Missing retained reference PPTX: ${referencePath}`);
  }
  const slidesPlan = await readManifest(manifestPath, imagesDir);
  const { FileBlob, PresentationFile } = await loadArtifactTool(workspace);
  const presentation = await PresentationFile.importPptx(await FileBlob.load(referencePath));
  const originals = [...presentation.slides.items];
  const sourceSlide = originals[SOURCE_SLIDE_INDEX];
  if (!sourceSlide) {
    throw new Error(`Reference PPTX does not contain source slide ${SOURCE_SLIDE_INDEX + 1}`);
  }

  const outputs = slidesPlan.map((entry) => ({ entry, slide: sourceSlide.duplicate() }));
  for (const slide of originals) {
    slide.delete();
  }

  for (let index = 0; index < outputs.length; index += 1) {
    const { entry, slide } = outputs[index];
    slide.moveTo(index);
    keepOnlyHeader(slide, entry.header, entry.title);
    slide.images.add(await imageConfig(entry.imagePath));
  }

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outPath);
  const reorder = spawnSync(pythonBin, [REORDER_SCRIPT, outPath], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (reorder.status !== 0) {
    const details = [reorder.stdout, reorder.stderr].filter(Boolean).join("\n").trim();
    throw new Error(`Failed to reorder generated body images below the original header:\n${details}`);
  }
  const outputStat = await fs.stat(outPath);
  if (outputStat.size <= 0) {
    throw new Error(`Exported PPTX is empty: ${outPath}`);
  }
  console.log(
    JSON.stringify({
      output: outPath,
      bytes: outputStat.size,
      slides: outputs.length,
      headerSlides: outputs.filter(({ entry }) => entry.header).length,
      sourceSlide: SOURCE_SLIDE_INDEX + 1,
      layerReorder: JSON.parse(reorder.stdout),
    }),
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : error);
  process.exitCode = 1;
});
