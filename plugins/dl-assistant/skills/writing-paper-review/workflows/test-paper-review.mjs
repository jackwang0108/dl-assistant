// 执行真实工作流源码，用宿主stub核编排；不调用模型，不认证审稿行为。
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const code = (await readFile(new URL('./paper-review.js', import.meta.url), 'utf8')).replace('export const meta =', 'const meta =');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const workflow = new AsyncFunction('args', 'agent', 'parallel', code);
const sha = 'a'.repeat(64);
const run = () => ({ schema_version: 2, run_id: 'fixture', mode: 'independent', paper: { path: '/fixture/paper.pdf', sha256: sha }, materials: [{ id: 'paper', path: '/fixture/paper.pdf', sha256: sha, role: 'paper' }], venue: { name: null, form_status: 'not_requested', sources: [], dimensions: [] }, isolation: { status: 'context_separated', limitations: [] }, preparation_check: { status: 'clear', basis: 'AUTHOR_PRIVATE_NOTE', unknowns: [], effect: 'explicit scope' }, tasks: [{ id: 'r1', role: 'reviewer', focus: 'evidence' }, { id: 'r2', role: 'reviewer', focus: 'contribution' }, { id: 's1', role: 'synthesis', focus: 'synthesis' }], author_private: 'AUTHOR_PRIVATE_NOTE' });
const args = () => ({ run: run(), runSha256: sha, reviewDir: '/fixture/round' });
const result = id => ({ task_id: id, run_id: 'fixture', paper_sha256: sha, issues: [] });
const parallel = tasks => Promise.all(tasks.map(t => t()));
let count = 0;
async function test(name, fn) { await fn(); count++; process.stdout.write('PASS '+name+'\n'); }

await test('任务集合和身份不丢失，综合后启动', async () => {
    const calls = [];
    const output = await workflow(args(), async (_p, o) => { calls.push(o.label); if (o.label === 's1') assert.deepEqual(calls.slice(0,2).sort(), ['r1','r2']); return result(o.label); }, parallel);
    assert.deepEqual(output.tasks.map(t => t.task_id), ['r1','r2','s1']); assert.ok(output.tasks.every(t => t.status === 'returned'));
});
await test('单任务抛错仍保留其他返回和失败原因', async () => {
    const output = await workflow(args(), async (_p,o) => { if (o.label === 'r2') throw Error('tool failure'); return result(o.label); }, parallel);
    assert.equal(output.tasks[1].status, 'failed'); assert.match(output.tasks[1].error, /tool failure/); assert.equal(output.tasks[2].status,'returned');
});
await test('空返回不是被filter删除', async () => {
    const output = await workflow(args(), async (_p,o) => o.label === 'r1' ? null : result(o.label), parallel);
    assert.equal(output.tasks.length,3); assert.equal(output.tasks[0].status,'invalid');
});
await test('全部reviewer失败不伪造综合', async () => {
    const calls = [];
    const output = await workflow(args(), async (_p,o) => { calls.push(o.label); throw Error('no tools'); }, parallel);
    assert.ok(!calls.includes('s1')); assert.equal(output.tasks[2].status,'failed');
});
await test('宿主并行异常显式记录每个未完成任务', async () => {
    const output = await workflow(args(), async (_p,o) => result(o.label), async () => { throw Error('host failure'); });
    assert.equal(output.tasks.length,3); assert.ok(output.tasks.every(t=>t.status==='failed')); assert.equal(output.orchestration_error,'host failure');
});
await test('错误论文身份不被算返回成功', async () => {
    const output = await workflow(args(), async (_p,o) => ({...result(o.label),paper_sha256:'b'.repeat(64)}), parallel);
    assert.equal(output.tasks[0].status,'invalid'); assert.equal(output.tasks[2].status,'failed');
});
await test('单reviewer可运行但不假装已综合', async () => {
    const input=args();input.run.tasks=input.run.tasks.slice(0,1);
    const output = await workflow(input,async (_p,o)=>result(o.label),parallel);
    assert.equal(output.tasks.length,1); assert.equal(output.tasks[0].role,'reviewer');
});
await test('未授权模式中的旧意见不能混入独立预审', async () => {
    const input=args();input.run.materials.push({...input.run.materials[0],id:'old',role:'prior_review'});
    await assert.rejects(()=>workflow(input,async()=>null,parallel),/独立预审/);
});
await test('JSON字符串入参仍按同一契约核对', async () => {
    const output=await workflow(JSON.stringify(args()),async (_p,o)=>result(o.label),parallel);
    assert.equal(output.tasks.length,3);
});
await test('相同快照只重试失败任务，重新综合', async () => {
    const input=args();input.resume={run_id:'fixture',run_sha256:sha,tasks:[{task_id:'r1',role:'reviewer',status:'returned',result:result('r1'),error:null},{task_id:'r2',role:'reviewer',status:'failed',result:null,error:'previous error'}]};
    const calls=[];const output=await workflow(input,async (_p,o)=>{calls.push(o.label);return result(o.label);},parallel);
    assert.deepEqual(calls,['r2','s1']);assert.equal(output.tasks[0].reused,true);
});
await test('不能恢复不同输入快照',async()=>{
    const input=args();input.resume={run_id:'fixture',run_sha256:'b'.repeat(64),tasks:[]};
    await assert.rejects(()=>workflow(input,async()=>null,parallel),/不同输入/);
});
await test('准备自查有缺陷不开跑',async()=>{
    const input=args();input.run.preparation_check.status='needs_revision';
    await assert.rejects(()=>workflow(input,async()=>null,parallel),/准备自查/);
});
await test('不把作者内部附加字段/准备笔记注入reviewer',async()=>{
    await workflow(args(),async(prompt,o)=>{assert.ok(!prompt.includes('AUTHOR_PRIVATE_NOTE'));return result(o.label);},parallel);
});
await test('revision_check明确给旧问题并使用复查schema',async()=>{
    const input=args();input.run.mode='revision_check';input.run.prior_round={path:'/fixture/prior.json',sha256:sha};input.run.revision_scope=['OLD1'];
    await workflow(input,async(prompt,o)=>{assert.match(prompt,/OLD1/);assert.ok(o.schema.properties.self_check);if(o.label==='s1')assert.ok(o.schema.properties.rechecks);return result(o.label);},parallel);
});
console.log(`Ran ${count} workflow tests`);
