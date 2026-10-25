/* Optional dev QA: requires Playwright + Chromium, not a site runtime dependency.
   Run a local HTTP server first. No credentials, no external domain requests. */
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const base=process.env.QA_SITE_URL||'http://127.0.0.1:8765/course/research/';
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||require('child_process').execFileSync('which',['chromium'],{encoding:'utf8'}).trim(),args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1280,height:900}});
 const page=await context.newPage();const external=[],errors=[],responses=[];
 await context.route('**/*',route=>{
  const u=new URL(route.request().url());
  if(['127.0.0.1','localhost'].includes(u.hostname))return route.continue();
  external.push(u.href);return route.abort();
 });
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)responses.push({url:r.url(),status:r.status()})});
 const home=await page.goto(base);if(home.status()!==200)throw Error('home HTTP !=200');
 if(!(await page.content()).includes('RESEARCH-SITE-OK'))throw Error('home marker missing');
 await page.screenshot({path:path.join(root,'evidence/home-desktop.png'),fullPage:true});
 const results=await page.goto(base+'generated/results.html');
 if(results.status()!==200)throw Error('results HTTP !=200');
 await page.locator('iframe').waitFor();
 const frame=page.frames().find(f=>f.url().endsWith('/generated/home-wins.html'));
 await frame.waitForFunction(()=>typeof Chart!=='undefined'&&Chart.getChart(document.querySelector('canvas')));
 await page.waitForTimeout(700);
 const chart=await frame.evaluate(()=>{
  const canvas=document.querySelector('canvas'),c=Chart.getChart(canvas);
  return {points:c.data.datasets[0].data.length,first:c.data.datasets[0].data[0],last:c.data.datasets[0].data.at(-1),
    unsafe:document.querySelector('[data-audit-unsafe]')?.getAttribute('data-audit-unsafe')||null,
    policy:document.querySelector('[data-audit-policy]')?.getAttribute('data-audit-policy')||null,
    overflow:document.documentElement.scrollWidth>innerWidth,localLibrary:!!document.querySelector('script[src="../assets/vendor/chart.umd.js"]'),
    caption:document.querySelector('.figure-title').textContent};
 });
 if(chart.points!==13||chart.unsafe||chart.policy||chart.overflow||!chart.localLibrary)throw Error('chart QA failed '+JSON.stringify(chart));
 const formula=await page.locator('math').evaluate(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,fraction:!!el.querySelector('mfrac')}));
 if(!formula.fraction||formula.height<10)throw Error('MathML not rendered');
 await page.screenshot({path:path.join(root,'evidence/results-desktop.png'),fullPage:true});
 // Локальный русский поиск должен работать при заблокированных внешних доменах.
 await page.locator('.md-search__input').click();
 await page.locator('.md-search__input').fill('кэш');
 await page.locator('.md-search__input').press('Space');
 await page.locator('.md-search__input').press('Backspace');
 await page.waitForFunction(()=>document.querySelectorAll('.md-search-result__item').length>0,null,{timeout:10000});
 const search={query:'кэш',items:await page.locator('.md-search-result__item').count(),text:(await page.locator('.md-search-result__meta').innerText()).trim()};
 await page.waitForTimeout(350);
 await page.screenshot({path:path.join(root,'evidence/search-ru.png'),fullPage:false,animations:'disabled'});
 await page.keyboard.press('Escape');
 const widths=[];
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});await page.goto(base+'generated/results.html');await page.waitForTimeout(700);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  const f=page.frames().find(f=>f.url().endsWith('/generated/home-wins.html'));
  const chartOverflow=await f.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  widths.push({width,documentOverflow:overflow,chartOverflow});
  if(overflow||chartOverflow)throw Error('mobile overflow '+width);
  await page.screenshot({path:path.join(root,`evidence/results-mobile-${width}.png`),fullPage:true});
 }
 const proof={scope:'local HTTP under /course/research/, external domains blocked; NOT a remote deployment',
  http:{home:home.status(),results:results.status(),marker:true},chart,formula,search,mobile:widths,
  externalRequestsAttempted:external,consoleErrors:errors,httpErrors:responses};
 fs.writeFileSync(path.join(root,'evidence/browser-qa.json'),JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof));
 if(errors.length||responses.length||external.length)throw Error('unexpected external request or browser error');
 await browser.close();process.exit(0);
})().catch(e=>{console.error(e.stack);process.exit(1)});
