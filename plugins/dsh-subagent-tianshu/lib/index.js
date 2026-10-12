// dsh-subagent-tianshu —— 天枢委派 provider（每个【星域】注册一个实例）
//
// 契约完全照 @deepseek-ai/dsh-subagent-codex（0.2.0-rc.2）实测得出：
//   export const name / inject / Config / apply(ctx, config)
//   provider: { name, capabilities, inheritsParentContext, start(request) }
//   run:      settleRunResult({ attempt })  ->  subprocessRunHandle({ id, result, signal, onAbort, requestCancel, teardown })
//
// 与 codex 版的差别：天枢是**普通 CLI**（rivet -p / --goal），不是 app-server JSON-RPC，
// 所以没有 871 行协议代码，核心引擎在 ./tianshu-run.mjs（已实测：exit 0、2.4s、拿到真实答复）。
//
// ⚠️ 已知未验证项（唯一一处）：attempt() 的**返回值形状**。DSH 的 SubagentRun 由
//    subprocessRunHandle 包装，codex 版 attempt 返回的是它自己的 wire 终态对象。
//    这里按最保守的形状返回 { stopReason: 'completed', output: [{type:'text',text}] }；
//    若在 canary profile 实测报形状错，按 @deepseek-ai/dsh-subagent 的 SubagentRun 类型微调即可
//    （改这一处，不影响其它部分）。

import { randomUUID } from 'node:crypto';
import { appendFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import z from '@deepseek-ai/schemastery';
import { NO_START_CAPABILITIES, settleRunResult, subprocessRunHandle } from '@deepseek-ai/dsh-subagent';
import { runTianshu } from './tianshu-run.mjs';

export const name = 'subagent-tianshu';
/** 与 codex 版一致：只需要共享的 subagents 与 subprocess 两个服务。 */
export const inject = ['subagents', 'subprocess'];

/** 一个星域 = 一份人设 + 一个工作目录。 */
const Domain = z.object({
  /** 星域 id（写进日志与 provider 描述，例如 exec / approve / fix / qiming） */
  id: z.string().min(1),
  /** 星域全名（例如 天枢·执行星域） */
  title: z.string().default(''),
  /** 职守/人设文本，会作为前缀注入每次委派 */
  persona: z.string().default(''),
  /** 该星域的独立工作目录（不填则用父会话的 cwd） */
  cwd: z.string().default(''),
});

export const Config = z.object({
  /** 在 ctx.subagents 上的注册名（模型通过它看到不同工具） */
  providerName: z.string().min(1).default('tianshu'),
  /** 该实例绑定的星域 */
  domain: Domain,
  /** 目标模式（--goal --budget）而不是一次性（-p） */
  goalMode: z.boolean().default(false),
  /** goal 模式的预算轮数 */
  budget: z.number().default(4),
  /** 单次调用超时（毫秒） */
  timeoutMs: z.number().default(900000),
  /** 额外环境变量（会覆盖继承环境；DEEPSEEK_API_KEY 会自动从用户环境补） */
  env: z.dict(z.string()).default({}),
});

/** 把请求里的内容块拼成纯文本任务。 */
function taskText(prompt) {
  if (typeof prompt === 'string') return prompt;
  if (!Array.isArray(prompt)) return String(prompt ?? '');
  return prompt
    .map((b) => (typeof b === 'string' ? b : (b && (b.text ?? b.content ?? '')) || ''))
    .filter(Boolean)
    .join('\n');
}

class TianshuProvider {
  capabilities = NO_START_CAPABILITIES;
  inheritsParentContext = false;

  constructor(providerName, ctx, config) {
    this.name = providerName;
    this.ctx = ctx;
    this.config = config;
  }

  start(request) {
    const cfg = this.config;
    const domain = cfg.domain || {};
    const parentCwd = request?.parent?.session?.header?.cwd;
    const cwd = domain.cwd || parentCwd;
    if (!cwd) throw new Error('subagent-tianshu: 没有工作目录（请在星域配置里给 cwd，或从有 cwd 的父会话委派）');

    const body = taskText(request?.prompt).trim();
    if (!body) throw new Error('subagent-tianshu: 空任务');
    const persona = domain.persona
      ? `【星域】${domain.title || domain.id}\n${domain.persona}\n（以上是你的独立身份，请始终以该身份作答，不要与其他星域混同。）\n\n`
      : '';
    const prompt = persona + body;

    const controller = new AbortController();
    const onAbort = () => controller.abort();
    if (request?.signal) {
      if (request.signal.aborted) controller.abort();
      else request.signal.addEventListener('abort', onAbort, { once: true });
    }
    const cleanup = () => request?.signal?.removeEventListener?.('abort', onAbort);

    const attempt = async () => {
      this.ctx.logger?.info?.(`subagent-tianshu[${domain.id || this.name}]: 启动（cwd=${cwd}）`);
      const r = await runTianshu(prompt, {
        goal: cfg.goalMode,
        budget: cfg.budget,
        cwd,
        env: cfg.env,
        timeoutMs: cfg.timeoutMs,
        abortSignal: controller.signal,
      });
      if (r.exitCode !== 0) {
        throw new Error(`subagent-tianshu[${domain.id || this.name}]: 天枢退出码 ${r.exitCode} :: ${(r.answer || r.raw || '').slice(0, 300)}`);
      }
      return {
        stopReason: 'completed',
        output: [{ type: 'text', text: r.answer }],
        usage: null,
        meta: { domain: domain.id || '', elapsedMs: r.elapsedMs, argv: r.argv },
      };
    };

    const result = settleRunResult({ attempt });
    return subprocessRunHandle({
      id: randomUUID(),
      result,
      signal: request?.signal,
      onAbort,
      requestCancel: () => controller.abort(),
      teardown: async () => { cleanup(); controller.abort(); },
    });
  }
}

/** 注册一个星域 provider。要多个星域就在 cordis.patch.yml 里 insert 多份配置。 */
export function apply(ctx, config) {
  const providerName = config?.providerName ?? 'tianshu';
  const resolved = {
    providerName,
    domain: config?.domain ?? { id: 'default', title: '', persona: '', cwd: '' },
    goalMode: config?.goalMode ?? false,
    budget: config?.budget ?? 4,
    timeoutMs: config?.timeoutMs ?? 900000,
    env: config?.env ?? {},
  };
  ctx.subagents.registerProvider(new TianshuProvider(providerName, ctx, resolved));
  ctx.logger?.info?.(`subagent-tianshu: 已注册星域 provider "${providerName}"（domain=${resolved.domain.id}，cwd=${resolved.domain.cwd || '(继承父会话)'}）`);
  // 加载凭证：写一行到插件目录旁的 load-proof.log —— 用于事后证明"插件确实被 apply 了"
  try {
    const proof = fileURLToPath(new URL('../load-proof.log', import.meta.url));
    appendFileSync(proof, `${new Date().toISOString()}\tprovider=${providerName}\tdomain=${resolved.domain.id}\tpid=${process.pid}\n`);
  } catch {
    /* 写不了就算了，不影响功能 */
  }
}
