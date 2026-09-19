export const meta = {
  name: 'plan-implement-verify',
  description: 'Plan a task, implement it, loop independent review and verification until both are clean, then commit',
  whenToUse: 'Any code change that must be planned, implemented, independently reviewed and verified before it is committed.',
  phases: [
    { title: 'Plan', detail: 'planner agent turns the task into ordered steps and acceptance criteria' },
    { title: 'Implement', detail: 'implementer agent applies the plan' },
    { title: 'Review', detail: 'reviewer agent reads the working-tree diff against the plan' },
    { title: 'Verify', detail: 'verifier agent runs every acceptance check' },
    { title: 'Fix', detail: 'implementer agent addresses blocking findings and failed checks' },
    { title: 'Commit', detail: 'committer agent commits and pushes once everything is green' },
  ],
}

// ── inputs ──────────────────────────────────────────────────────────────────
// args: {
//   taskFile?: string,      path to a markdown task description (preferred)
//   task?: string,          inline task text (used when taskFile is absent)
//   branch?: string,        branch the committer must push to
//   commit?: boolean,       commit and push when green (default false)
//   attribution?: string,   trailer lines to append verbatim to the commit message
//   maxRounds?: number,     review/verify/fix rounds before giving up (default 4)
// }
const opts = args && typeof args === 'object' ? args : {}
if (!opts.taskFile && !opts.task) {
  throw new Error('plan-implement-verify needs args.taskFile (path to a task file) or args.task (task text)')
}
const maxRounds = Number.isInteger(opts.maxRounds) && opts.maxRounds > 0 ? opts.maxRounds : 4
const wantCommit = opts.commit === true
const branch = typeof opts.branch === 'string' && opts.branch ? opts.branch : null
const attribution = typeof opts.attribution === 'string' ? opts.attribution.trim() : ''

const TASK = opts.taskFile
  ? `The task is described in the file \`${opts.taskFile}\` at the repository root. Read it in full before anything else; it is the source of truth.`
  : `The task:\n\n${opts.task}`

// ── schemas ─────────────────────────────────────────────────────────────────
const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    steps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          change: { type: 'string' },
          why: { type: 'string' },
        },
        required: ['file', 'change', 'why'],
      },
    },
    acceptanceCommands: { type: 'array', items: { type: 'string' } },
    acceptanceBehaviour: { type: 'array', items: { type: 'string' } },
    constraints: { type: 'array', items: { type: 'string' } },
    outOfScope: { type: 'array', items: { type: 'string' } },
    headAtPlan: { type: 'string' },
  },
  required: ['summary', 'steps', 'acceptanceCommands', 'acceptanceBehaviour', 'constraints', 'headAtPlan'],
}

const CHECK_SCHEMA = {
  type: 'object',
  properties: {
    command: { type: 'string' },
    passed: { type: 'boolean' },
    tail: { type: 'string' },
  },
  required: ['command', 'passed', 'tail'],
}

const IMPL_SCHEMA = {
  type: 'object',
  properties: {
    changedFiles: { type: 'array', items: { type: 'string' } },
    checks: { type: 'array', items: CHECK_SCHEMA },
    unresolved: { type: 'array', items: { type: 'string' } },
  },
  required: ['changedFiles', 'checks', 'unresolved'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'integer' },
          severity: { type: 'string', enum: ['blocking', 'nit'] },
          summary: { type: 'string' },
          failure: { type: 'string' },
          proposedFix: { type: 'string' },
        },
        required: ['file', 'line', 'severity', 'summary', 'failure', 'proposedFix'],
      },
    },
  },
  required: ['findings'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    checks: { type: 'array', items: CHECK_SCHEMA },
    allPassed: { type: 'boolean' },
  },
  required: ['checks', 'allPassed'],
}

const COMMIT_SCHEMA = {
  type: 'object',
  properties: {
    commit: { type: 'string' },
    branch: { type: 'string' },
    pushed: { type: 'boolean' },
    notes: { type: 'string' },
  },
  required: ['commit', 'branch', 'pushed', 'notes'],
}

// ── helpers ─────────────────────────────────────────────────────────────────
const fmtChecks = (checks) =>
  checks.map((c) => `- ${c.passed ? 'PASS' : 'FAIL'} \`${c.command}\`\n\`\`\`\n${c.tail}\n\`\`\``).join('\n')

const fmtFindings = (findings) =>
  findings
    .map((f, i) => `${i + 1}. [${f.severity}] ${f.file}:${f.line} — ${f.summary}\n   fails how: ${f.failure}\n   proposed fix: ${f.proposedFix}`)
    .join('\n')

// Canonical signature of what a round asks the fix stage to do: the failed check commands and
// the blocking finding summaries, each trimmed, sorted and deduplicated. Two rounds with the
// same signature mean the fix stage changed nothing that review or verification can see.
const roundSignature = (blocking, failed) => {
  const norm = (items) => Array.from(new Set(items.map((s) => String(s).trim()))).sort()
  return JSON.stringify({
    failedChecks: norm(failed.map((c) => c.command)),
    blockingFindings: norm(blocking.map((f) => f.summary)),
  })
}

// ── Plan ────────────────────────────────────────────────────────────────────
phase('Plan')
const plan = await agent(
  `Mode: plan.\n\n${TASK}\n\nProduce the implementation plan as structured data.`,
  { agentType: 'planner', phase: 'Plan', schema: PLAN_SCHEMA, label: 'plan' },
)
if (!plan) throw new Error('Planner produced no plan')
const planText = JSON.stringify(plan, null, 2)
log(`Plan: ${plan.steps.length} steps, ${plan.acceptanceCommands.length} acceptance commands, ${plan.constraints.length} constraints, HEAD at plan ${plan.headAtPlan}`)
const HEAD_NOTE = `HEAD when the plan was produced: ${plan.headAtPlan}. No stage before the commit stage may commit; if HEAD differs from this, an earlier stage committed.`

// ── Implement ───────────────────────────────────────────────────────────────
phase('Implement')
const implementation = await agent(
  `Mode: Implement.\n\n${TASK}\n\nApproved plan (JSON):\n${planText}\n\nImplement every step in order. Do not commit.`,
  { agentType: 'implementer', phase: 'Implement', schema: IMPL_SCHEMA, label: 'implement' },
)
if (!implementation) throw new Error('Implementer produced no result')
log(`Implemented: ${implementation.changedFiles.length} files changed, ${implementation.unresolved.length} unresolved items`)

// ── Review + Verify, then Fix, until green or out of rounds ─────────────────
// The reviewer deliberately never sees the implementer's report: only the task, the plan
// and (from round 2 on) the findings it must confirm resolved.
const history = []
let review = null
let verification = null
let previousBlocking = []
let previousSignature = null
let green = false
let repeated = false
let round = 0

while (round < maxRounds) {
  round++
  const previous = previousBlocking.length
    ? `\n\nFindings from the previous round that the implementer was asked to fix. Confirm each is resolved; report any that remain as blocking:\n${fmtFindings(previousBlocking)}`
    : ''

  const [reviewResult, verifyResult] = await parallel([
    () =>
      agent(
        `Mode: review (round ${round}).\n\n${TASK}\n\n${HEAD_NOTE}\n\nApproved plan (JSON):\n${planText}${previous}\n\nReview the complete working-tree change against the plan and the task's constraints. Report findings as structured data.`,
        { agentType: 'reviewer', phase: 'Review', schema: REVIEW_SCHEMA, label: `review r${round}` },
      ),
    () =>
      agent(
        `Mode: verify (round ${round}).\n\n${TASK}\n\nAcceptance commands, run in this order:\n${plan.acceptanceCommands.map((c) => `- ${c}`).join('\n')}\n\nBehaviour that must hold (run the end-to-end checks the task describes for these):\n${plan.acceptanceBehaviour.map((b) => `- ${b}`).join('\n')}\n\nReport every check with its real output.`,
        { agentType: 'verifier', phase: 'Verify', schema: VERIFY_SCHEMA, label: `verify r${round}` },
      ),
  ])
  review = reviewResult
  verification = verifyResult

  const blocking = review ? review.findings.filter((f) => f.severity === 'blocking') : []
  const nits = review ? review.findings.filter((f) => f.severity === 'nit') : []
  const failed = verification ? verification.checks.filter((c) => !c.passed) : []
  const agentLost = !review || !verification
  const roundGreen = !agentLost && blocking.length === 0 && failed.length === 0 && verification.allPassed === true

  const signature = agentLost ? null : roundSignature(blocking, failed)
  repeated = !roundGreen && signature !== null && previousSignature !== null && signature === previousSignature

  history.push({
    round,
    blocking: blocking.length,
    nits: nits.length,
    failedChecks: failed.length,
    failedCheckCommands: failed.map((c) => c.command),
    blockingSummaries: blocking.map((f) => f.summary),
    reviewerLost: !review,
    verifierLost: !verification,
    green: roundGreen,
    repeatedPreviousRound: repeated,
  })
  log(`Round ${round}: ${blocking.length} blocking, ${nits.length} nits, ${failed.length} failed checks${agentLost ? ' (an agent was lost, round not trusted)' : ''}`)

  if (roundGreen) {
    green = true
    break
  }
  if (repeated) {
    // The fix stage changed nothing review or verification can see. Another fix round would
    // receive the identical prompt and most likely produce the identical result; stop now
    // rather than spend the remaining rounds.
    log(`Round ${round} repeated round ${round - 1} verbatim (same failed checks and blocking findings); stopping with status red.`)
    break
  }
  if (round === maxRounds) break
  previousSignature = signature

  if (agentLost && blocking.length === 0 && failed.length === 0) {
    // Nothing concrete to fix; re-run review and verification.
    previousBlocking = []
    continue
  }

  phase('Fix')
  const fix = await agent(
    `Mode: Fix (round ${round}).\n\n${TASK}\n\nApproved plan (JSON):\n${planText}\n\nBlocking review findings to fix:\n${blocking.length ? fmtFindings(blocking) : '(none)'}\n\nFailed verification checks to fix:\n${failed.length ? fmtChecks(failed) : '(none)'}\n\nOptional nits, carry them along only if trivial:\n${nits.length ? fmtFindings(nits) : '(none)'}\n\nFix every blocking finding and failed check. Do not commit.`,
    { agentType: 'implementer', phase: 'Fix', schema: IMPL_SCHEMA, label: `fix r${round}` },
  )
  if (fix) log(`Fix round ${round}: ${fix.changedFiles.length} files changed, ${fix.unresolved.length} unresolved items`)
  previousBlocking = blocking
}

// ── Commit, only when green and asked for ───────────────────────────────────
let commitResult = null
if (green && wantCommit) {
  phase('Commit')
  commitResult = await agent(
    `${TASK}\n\n${HEAD_NOTE}\n\nPlan summary: ${plan.summary}\n\nReview reported no blocking findings and every verification check passed. Commit the working-tree changes and push${branch ? ` to branch \`${branch}\`` : ' to the branch the task names'}.${attribution ? `\n\nAppend these trailer lines verbatim at the end of the commit message:\n${attribution}` : ''}`,
    { agentType: 'committer', phase: 'Commit', schema: COMMIT_SCHEMA, label: 'commit' },
  )
  if (commitResult) log(`Committed ${commitResult.commit} on ${commitResult.branch}, pushed=${commitResult.pushed}`)
} else if (green) {
  log('Green. Commit not requested (args.commit is not true); working tree left uncommitted.')
} else if (repeated) {
  log(`Stopped after ${round} round(s): the last round repeated the previous one verbatim. Nothing committed.`)
} else {
  log(`Not green after ${round} round(s). Nothing committed.`)
}

return {
  status: green ? 'green' : 'red',
  stopReason: green ? 'green' : repeated ? 'round repeated verbatim' : 'out of rounds',
  rounds: round,
  history,
  plan,
  implementation,
  lastReview: review,
  lastVerification: verification,
  nits: review ? review.findings.filter((f) => f.severity === 'nit') : [],
  commit: commitResult,
}
