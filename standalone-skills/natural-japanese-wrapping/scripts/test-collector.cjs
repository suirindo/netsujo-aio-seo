/* Contract test with synthetic geometry, NOT an actual browser. MIT License. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');

function harness(text, split, extra = {}) {
  const node = { data: text };
  const style = { writingMode:'horizontal-tb', columnCount:'auto', columnWidth:'auto', webkitLineClamp:'none', textOverflow:'clip', transform:'none', display:'block', visibility:'visible', opacity:'1', fontSize:'20px', verticalAlign:'baseline', font:'20px sans-serif', wordBreak:'normal', lineBreak:'strict', whiteSpace:'normal', ...extra };
  const el = { id:'sample', tagName:'P', dataset:{}, parentElement:null, querySelector:()=>null, querySelectorAll:()=>[], getBoundingClientRect:()=>({left:0,top:0,right:1000,bottom:100,width:1000,height:100}), scrollWidth:1000, clientWidth:1000, scrollHeight:100, clientHeight:100, contains:()=>false };
  let start=0, end=0;
  const context = { Intl, innerWidth:375, innerHeight:800, devicePixelRatio:1, NodeFilter:{SHOW_TEXT:4}, requestAnimationFrame:fn=>fn(), getComputedStyle:(_,pseudo)=>pseudo ? { content:'none' } : style,
    document:{ fonts:{ready:Promise.resolve()}, querySelectorAll:()=>[el], createTreeWalker:()=>{let done=false;return {nextNode:()=>done?null:(done=true,node)};}, createRange:()=>({setStart:(_,s)=>start=s,setEnd:(_,e)=>end=e,getClientRects:()=>[{left:0,right:20,width:20,height:20,top:start<split?0:30,bottom:start<split?20:50}]}) }
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'collect-rendered-lines.js'),'utf8'),context);
  return { context, el };
}

(async()=>{
  let {context} = harness('3つの事例を、ご覧ください。',5);
  let result = await context.collectJapaneseLines('p',{protected:['3つの事例を、']});
  assert.equal(result.elements[0].lines.length,2);
  assert.equal(result.elements[0].lines[1].text,'を、ご覧ください。');
  assert.equal(result.elements[0].protectedSpans[0].end,7);
  assert.equal(result.elements[0].text,result.elements[0].lines.map(x=>x.text).join(''));
  assert.equal(result.elements[0].unsupported.length,0);
  ({context}=harness('🚀月額7万円です。',2));
  result=await context.collectJapaneseLines('p',{protected:['月額7万円']});
  assert.equal(result.elements[0].lines[0].end,2);
  assert.equal(result.elements[0].protectedSpans[0].start,2);
  ({context}=harness('テスト',2,{writingMode:'vertical-rl'}));
  assert.ok((await context.collectJapaneseLines('p')).elements[0].unsupported.includes('non-horizontal writing'));
  ({context}=harness('テスト',2));
  await assert.rejects(()=>context.collectJapaneseLines('p',{minElements:2}),/Matched/);
  context.document.querySelectorAll=()=>[];
  await assert.rejects(()=>context.collectJapaneseLines('missing'),/Matched/);
  let h=harness('テスト',2); h.el.dataset.jaProtect='["存在しない"]';
  assert.ok((await h.context.collectJapaneseLines('p')).elements[0].unsupported.includes('declared local protected phrase missing'));
  h=harness('テスト',2); h.el.scrollWidth=1100;
  assert.equal((await h.context.collectJapaneseLines('p')).elements[0].overflow,true);
  console.log('Collector contract: 7 scenarios PASS (synthetic geometry only).');
})().catch(e=>{console.error(e);process.exitCode=1;});
