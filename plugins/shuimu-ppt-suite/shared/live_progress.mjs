#!/usr/bin/env node
/** Optional, producer-neutral bridge to the user's installed PPT Live CLI. */
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export async function liveConfiguration() {
  const configPath = process.env.PPT_LIVE_CONFIG || path.join(process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'), 'ppt-live/config.json');
  let config = {};
  try { config = JSON.parse(await fs.readFile(configPath, 'utf8')); }
  catch (error) {
    if (error.code !== 'ENOENT') return { configured: false, reason: 'PPT Live 配置不可读，请重新 configure' };
  }
  const cliPath = process.env.PPT_LIVE_CLI || config.cliPath;
  if (!cliPath) return { configured: false, reason: '尚未配置 PPT Live' };
  if (!path.isAbsolute(cliPath)) return { configured: false, reason: 'PPT_LIVE_CLI / cliPath 必须为绝对路径' };
  try { await fs.access(cliPath); }
  catch { return { configured: false, reason: 'PPT Live CLI 不存在，请重新 configure' }; }
  return { configured: true, cliPath, node: process.env.PPT_LIVE_NODE || process.execPath };
}

function run(command, args) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { stdio: ['ignore', 'pipe', 'pipe'], env: process.env });
    let stdout = '', stderr = '';
    child.stdout.on('data', chunk => { stdout = (stdout + chunk).slice(-1048576); });
    child.stderr.on('data', chunk => { stderr = (stderr + chunk).slice(-16384); });
    // The publisher owns request timeouts and its durable queue. Do not kill it
    // while it is flushing earlier events or holding the project queue lock.
    child.once('error', error => resolve({ code: 1, stdout, stderr: error.message }));
    child.once('close', code => resolve({ code, stdout, stderr }));
  });
}

/** Progress failure is reported but never substitutes for a PPT quality gate. */
export async function publishProgress(args) {
  let temporary;
  try {
    const config = await liveConfiguration();
    if (!config.configured) return { skipped: true, reason: config.reason };
    const command = [...args];
    const layoutIndex = command.indexOf('--layout');
    if (layoutIndex !== -1) {
      if (!command.includes('init') || !command[layoutIndex + 1]) throw new Error('--layout 仅用于 init，且须指定完整 layout.json');
      const plan = JSON.parse(await fs.readFile(command[layoutIndex + 1], 'utf8'));
      const slides = plan.slides?.map(slide => ({
        id: slide.id,
        title: slide.title || slide.elements?.find(e => e.type === 'text' && (e.text_role === 'title' || e.text_role === 'cover_title' || e.id?.endsWith('-title')))?.text || slide.id,
      }));
      if (!slides?.length || slides.some(s => !s.id || !s.title) || new Set(slides.map(s => s.id)).size !== slides.length) throw new Error('完整设计须有非空且唯一的页面 ID 与标题');
      temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'ppt-live-plan-'));
      const manifest = path.join(temporary, 'slides.json');
      await fs.writeFile(manifest, JSON.stringify(slides), { mode: 0o600 });
      command.splice(layoutIndex, 2, '--slides', manifest);
    }
    const result = await run(config.node, [config.cliPath, ...command]);
    let output;
    try { output = JSON.parse(result.stdout.trim()); }
    catch { output = { message: result.stderr.trim() || 'PPT Live 发布工具未返回 JSON' }; }
    return result.code === 0 ? output : { ...output, failed: true, productionBlocked: false };
  } catch (error) {
    return { failed: true, productionBlocked: false, message: error.message };
  } finally {
    if (temporary) await fs.rm(temporary, { recursive: true, force: true });
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args[0] === 'status') {
    const result = await liveConfiguration();
    // Never echo config credentials or the user's private configuration path.
    console.log(JSON.stringify({ configured: result.configured, reason: result.reason }));
  } else {
    console.log(JSON.stringify(await publishProgress(args)));
  }
}
