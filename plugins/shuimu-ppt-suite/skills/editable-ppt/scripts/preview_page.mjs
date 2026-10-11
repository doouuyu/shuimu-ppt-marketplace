#!/usr/bin/env node
/** Validate a complete design, assemble one real native slide, render and publish. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { publishProgress } from '../../../shared/live_progress.mjs';

const scripts = path.dirname(fileURLToPath(import.meta.url));
const hash = data => createHash('sha256').update(data).digest('hex');

function parseArgs(argv) {
  const options = {};
  for (let i = 0; i < argv.length; i++) {
    const name = argv[i];
    if (name === '--no-publish') { options.noPublish = true; continue; }
    if (!['--plan', '--page', '--renderer', '--out', '--project', '--python'].includes(name) || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`未知参数或缺少值：${name}`);
    options[name.slice(2)] = argv[++i];
  }
  for (const name of ['plan', 'page', 'renderer', 'out']) if (!options[name]) throw new Error(`缺少 --${name}`);
  if (!options.out.toLowerCase().endsWith('.png')) throw new Error('--out 必须为 PNG 文件');
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const planPath = path.resolve(options.plan);
  const project = path.resolve(options.project || path.dirname(path.dirname(planPath)));
  const publishing = args => options.noPublish ? Promise.resolve({ skipped: true }) : publishProgress([...args, '--project', project]);
  const python = options.python || process.env.PPT_LIVE_PYTHON || 'python3';
  const planBytes = await fs.readFile(planPath);
  const check = spawnSync(python, [path.join(scripts, 'validate_deck.py'), planPath, '--require-assets', '--page', options.page], { encoding: 'utf8' });
  if (check.error || check.status !== 0) {
    const message = check.error?.message || check.stdout || check.stderr || '单页依赖检查失败';
    await publishing(['error', '--page', options.page, '--message', message.trim().slice(0, 1000)]);
    throw new Error(message);
  }
  process.stderr.write(check.stdout);
  if (hash(await fs.readFile(planPath)) !== hash(planBytes)) throw new Error('校验期间 layout.json 已变化，请重新运行单页预览');
  const plan = JSON.parse(planBytes);
  const slideIndex = plan.slides.findIndex(s => s.id === options.page);
  const selectedSlide = plan.slides[slideIndex];
  const dependencies = {};
  for (const element of selectedSlide.elements.filter(e => e.type === 'image')) {
    const asset = plan.assets.find(a => a.id === element.asset_id);
    dependencies[asset.id] = hash(await fs.readFile(path.resolve(path.dirname(planPath), asset.path)));
  }
  const templateDependencies = {};
  for (const reference of [plan.style?.reference_path, selectedSlide.template_source?.reference_path].filter(Boolean)) {
    templateDependencies[reference] = hash(await fs.readFile(path.resolve(path.dirname(planPath), reference)));
  }
  const started = await publishing(['start', '--page', options.page, '--stage', '整页组装']);
  if (started.failed) process.stderr.write(`PPT Live 同步未完成：${JSON.stringify(started)}\n`);
  try {
    const renderer = await import(pathToFileURL(path.resolve(options.renderer)).href);
    if (typeof renderer.assembleSlide !== 'function') throw new Error('renderer 须导出与最终构建共用的 assembleSlide({plan, slide, slideIndex, planPath, baseDir})');
    const result = await renderer.assembleSlide({ plan, slide: selectedSlide, slideIndex, planPath, baseDir: path.dirname(planPath) });
    if (!result?.presentation?.export || !result.slide) throw new Error('assembleSlide 须返回实际原生对象 {presentation, slide}，不能返回截图路径');
    const png = await result.presentation.export({ slide: result.slide, format: 'png', scale: 1 });
    const bytes = Buffer.from(await png.arrayBuffer());
    if (!bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) throw new Error('原生渲染未返回有效 PNG');
    // Reject concurrent edits instead of publishing a preview under newer text.
    if (hash(await fs.readFile(planPath)) !== hash(planBytes)) throw new Error('渲染期间 layout.json 已变化，请重新运行单页预览');
    for (const [id, digest] of Object.entries(dependencies)) {
      const asset = plan.assets.find(a => a.id === id);
      if (hash(await fs.readFile(path.resolve(path.dirname(planPath), asset.path))) !== digest) throw new Error(`渲染期间素材 ${id} 已变化，请重试`);
    }
    for (const [reference, digest] of Object.entries(templateDependencies)) {
      if (hash(await fs.readFile(path.resolve(path.dirname(planPath), reference))) !== digest) throw new Error('渲染期间模板源文件已变化，请重试');
    }
    const snapshot = spawnSync(python, [path.join(scripts, 'design_snapshot.py'), 'verify', planPath], { encoding: 'utf8' });
    if (snapshot.error || snapshot.status !== 0) throw new Error(snapshot.error?.message || snapshot.stdout || snapshot.stderr || '渲染期间设计快照已变化');
    const output = path.resolve(options.out);
    await fs.mkdir(path.dirname(output), { recursive: true });
    await fs.writeFile(output, bytes);
    const provenance = { pageId: selectedSlide.id, order: slideIndex + 1, planSha256: hash(planBytes), imageSha256: hash(bytes), dependencies, templateDependencies, kind: 'page', reviewed: false, renderedAt: new Date().toISOString() };
    await fs.writeFile(`${output}.json`, JSON.stringify(provenance, null, 2) + '\n');
    const progress = await publishing(['preview', '--page', selectedSlide.id, '--file', output, '--kind', 'page']);
    console.log(JSON.stringify({ pageId: selectedSlide.id, preview: output, provenance: `${output}.json`, progress }));
  } catch (error) {
    await publishing(['error', '--page', options.page, '--message', error.message]);
    throw error;
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
