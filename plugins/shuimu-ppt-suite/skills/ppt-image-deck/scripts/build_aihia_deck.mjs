import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(SCRIPT_DIR, "..");
const DEFAULT_REFERENCE = path.resolve(SKILL_DIR, "../../styles/aihia/assets/reference.pptx");
const REORDER_SCRIPT = path.join(SCRIPT_DIR, "reorder_aihia_body_layers.py");
const COVER_SOURCE_INDEX = 0;
const CONTENT_SOURCE_INDEX = 5;
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

function optionalString(value, label, maxLength) {
  if (value === undefined) {
    return "";
  }
  if (typeof value !== "string") {
    throw new Error(`${label} must be a string`);
  }
  const result = value.trim();
  if (/\r|\n/.test(result)) {
    throw new Error(`${label} must stay on one line`);
  }
  if (Array.from(result).length > maxLength) {
    throw new Error(`${label} must be ${maxLength} characters or fewer`);
  }
  return result;
}

function requiredString(value, label, maxLength) {
  const result = optionalString(value, label, maxLength);
  if (!result) {
    throw new Error(`${label} is required`);
  }
  return result;
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
  if (parsed.slides[0]?.role !== "cover") {
    throw new Error('slides[0].role must be "cover"');
  }

  const seenImages = new Set();
  let coverCount = 0;
  let contentCount = 0;
  const slides = [];

  for (let index = 0; index < parsed.slides.length; index += 1) {
    const entry = parsed.slides[index];
    const label = `slides[${index}]`;
    if (!entry || typeof entry !== "object") {
      throw new Error(`${label} must be an object`);
    }

    if (entry.role === "cover") {
      coverCount += 1;
      slides.push({
        role: "cover",
        title: requiredString(entry.title, `${label}.title`, 18),
        subtitle: optionalString(entry.subtitle, `${label}.subtitle`, 48),
        presenter: optionalString(entry.presenter, `${label}.presenter`, 30),
        date: optionalString(entry.date, `${label}.date`, 30),
      });
      continue;
    }

    if (entry.role === "content") {
      contentCount += 1;
      if (typeof entry.image !== "string" || entry.image.trim() === "") {
        throw new Error(`${label}.image must be a non-empty string`);
      }
      if (path.basename(entry.image) !== entry.image) {
        throw new Error(`${label}.image must be a file name inside --images, not a path`);
      }
      if (!/\.(png|jpe?g|webp)$/i.test(entry.image)) {
        throw new Error(`${label}.image must be PNG, JPEG, or WebP`);
      }
      if (seenImages.has(entry.image)) {
        throw new Error(`${label}.image is duplicated: ${entry.image}`);
      }
      seenImages.add(entry.image);

      const imagePath = path.resolve(imagesDir, entry.image);
      const stat = await fs.stat(imagePath).catch(() => undefined);
      if (!stat?.isFile()) {
        throw new Error(`${label}.image does not exist: ${imagePath}`);
      }
      slides.push({
        role: "content",
        image: entry.image,
        imagePath,
        title: requiredString(entry.title, `${label}.title`, 20),
      });
      continue;
    }

    throw new Error(`${label}.role must be "cover" or "content"`);
  }

  if (coverCount !== 1) {
    throw new Error(`manifest.json must contain exactly one cover; found ${coverCount}`);
  }
  if (contentCount === 0) {
    throw new Error("manifest.json must contain at least one content slide");
  }
  return slides;
}

function textOf(shape) {
  return shape.text?.toString?.() ?? "";
}

function replaceWholeText(shape, replacement) {
  const current = textOf(shape);
  shape.text.replace(current, replacement);
}

function isCoverTitle(shape) {
  return shape.name === "AutoShape 8" && textOf(shape).includes("超级AI医院运营方案");
}

function isCoverSubtitle(shape) {
  return shape.name === "AutoShape 9" && textOf(shape).includes("SUPRA AI HOSPITAL");
}

function isCoverInfo(shape) {
  const text = textOf(shape);
  return shape.name === "AutoShape 10" && text.includes("汇报人：") && text.includes("时间：");
}

function isCoverBackground(image) {
  const position = image.position ?? {};
  return (
    image.name === "Picture 6" &&
    position.left <= 1 &&
    position.top <= 1 &&
    position.width > 1200 &&
    position.height > 700
  );
}

function isCoverLogo(image) {
  const position = image.position ?? {};
  return (
    image.name === "Picture 7" &&
    position.left < 200 &&
    position.top < 100 &&
    position.width < 300
  );
}

function editNativeCover(slide, entry) {
  let titleShape;
  let subtitleShape;
  let infoShape;

  for (const shape of [...slide.shapes.items]) {
    if (isCoverTitle(shape)) {
      titleShape = shape;
      continue;
    }
    if (isCoverSubtitle(shape)) {
      subtitleShape = shape;
      continue;
    }
    if (isCoverInfo(shape)) {
      infoShape = shape;
      continue;
    }
    shape.delete();
  }

  let backgroundCount = 0;
  let logoCount = 0;
  for (const image of [...slide.images.items]) {
    if (isCoverBackground(image)) {
      backgroundCount += 1;
      continue;
    }
    if (isCoverLogo(image)) {
      logoCount += 1;
      continue;
    }
    image.delete();
  }

  if (!titleShape || !subtitleShape || !infoShape || backgroundCount !== 1 || logoCount !== 1) {
    throw new Error(
      `Could not isolate native AIHIA cover (title=${Boolean(titleShape)}, subtitle=${Boolean(subtitleShape)}, info=${Boolean(infoShape)}, background=${backgroundCount}, logo=${logoCount})`,
    );
  }

  replaceWholeText(titleShape, entry.title);
  replaceWholeText(subtitleShape, entry.subtitle);
  replaceWholeText(infoShape, `汇报人：${entry.presenter}\n时间：${entry.date}`);
}

function isHeaderBackground(shape) {
  const position = shape.position ?? {};
  return (
    shape.name === "AutoShape 19" &&
    position.top < 2 &&
    position.height > 70 &&
    position.height < 85
  );
}

function isHeaderTitle(shape) {
  const position = shape.position ?? {};
  return (
    textOf(shape).includes("输入修改文字") &&
    position.top < 20 &&
    position.left < 100
  );
}

function isHeaderLogo(image) {
  const position = image.position ?? {};
  return (
    image.name === "Picture 21" &&
    position.top < 30 &&
    position.left > 900 &&
    position.height < 55
  );
}

function keepOnlyNativeHeader(slide, title) {
  let backgroundShape;
  let titleShape;

  for (const shape of [...slide.shapes.items]) {
    if (isHeaderBackground(shape)) {
      if (backgroundShape) {
        throw new Error("Found more than one candidate AIHIA header background");
      }
      backgroundShape = shape;
      continue;
    }
    if (isHeaderTitle(shape)) {
      if (titleShape) {
        throw new Error("Found more than one candidate AIHIA header title");
      }
      titleShape = shape;
      continue;
    }
    shape.delete();
  }

  let logoCount = 0;
  for (const image of [...slide.images.items]) {
    if (isHeaderLogo(image)) {
      logoCount += 1;
      continue;
    }
    image.delete();
  }

  if (!backgroundShape || !titleShape || logoCount !== 1) {
    throw new Error(
      `Could not isolate native AIHIA header (background=${Boolean(backgroundShape)}, title=${Boolean(titleShape)}, logo=${logoCount})`,
    );
  }
  replaceWholeText(titleShape, title);
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
    alt: `Generated AIHIA slide body: ${path.basename(imagePath)}`,
    fit: "cover",
    position: { left: 0, top: 0, width: SLIDE_WIDTH, height: SLIDE_HEIGHT },
  };
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
    throw new Error(`Missing retained AIHIA reference PPTX: ${referencePath}`);
  }

  const slidesPlan = await readManifest(manifestPath, imagesDir);
  const { FileBlob, PresentationFile } = await loadArtifactTool(workspace);
  const presentation = await PresentationFile.importPptx(await FileBlob.load(referencePath));
  const originals = [...presentation.slides.items];
  const coverSource = originals[COVER_SOURCE_INDEX];
  const contentSource = originals[CONTENT_SOURCE_INDEX];
  if (!coverSource || !contentSource) {
    throw new Error("Reference PPTX must contain source slides 1 and 6");
  }

  const outputs = slidesPlan.map((entry) => ({
    entry,
    slide: entry.role === "cover" ? coverSource.duplicate() : contentSource.duplicate(),
  }));
  for (const slide of originals) {
    slide.delete();
  }

  for (let index = 0; index < outputs.length; index += 1) {
    const { entry, slide } = outputs[index];
    slide.moveTo(index);
    if (entry.role === "cover") {
      editNativeCover(slide, entry);
    } else if (entry.role === "content") {
      keepOnlyNativeHeader(slide, entry.title);
      slide.images.add(await imageConfig(entry.imagePath));
    }
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
    throw new Error(`Failed to reorder full-slide images below native AIHIA objects:\n${details}`);
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
      coverSlides: outputs.filter(({ entry }) => entry.role === "cover").length,
      contentSlides: outputs.filter(({ entry }) => entry.role === "content").length,
      coverSourceSlide: COVER_SOURCE_INDEX + 1,
      headerSourceSlide: CONTENT_SOURCE_INDEX + 1,
      layerReorder: JSON.parse(reorder.stdout),
    }),
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : error);
  process.exitCode = 1;
});
