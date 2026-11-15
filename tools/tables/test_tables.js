const T=require('./tables.js');let f=0;
const ok=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)f++};
const it=(x,y,s,sz)=>({str:s,transform:[sz||10,0,0,sz||10,x,y],width:s.length*5,height:sz||10,fontName:'g',hasEOL:false});
const row=(y,cells,sz)=>cells.map(([x,s])=>it(x,y,s,sz));
const page=(...rs)=>[].concat(...rs);
const para=y=>row(y,[[72,'Participants completed the questionnaire twice, a week apart, in the classroom of their college.']]);
function tbl(y,cap,title,hdr,data){const out=[];out.push(...row(y,[[72,cap]]));out.push(...row(y-12,[[72,title]]));out.push(...row(y-30,hdr));data.forEach((d,i)=>out.push(...row(y-45-i*13,d)));return out}
const H3=[[72,'Variable'],[250,'Mean'],[320,'SD']];
let r=T.read([page(para(740),tbl(700,'Table 1','Descriptive statistics',H3,[[[72,'Anxiety'],[250,'4.20'],[320,'1.10']],[[72,'Sleep'],[250,'6.85'],[320,'0.92']],[[72,'Stress'],[250,'3.10'],[320,'1.40']]]),row(600,[[72,'Note. N = 120.']]),para(580))]);
ok(r.tables.length===1&&r.tables[0].rows.length===3,'one table, 3 data rows (got '+JSON.stringify(r.tables.map(t=>t.rows.length))+')');
ok(r.tables[0].header.join('|')==='Variable|Mean|SD','header read: '+r.tables[0].header.join('|'));
ok(r.tables[0].title==='Descriptive statistics'&&r.tables[0].caption==='Table 1','caption and title kept apart');
ok(r.hits.length===3&&r.hits[0].text==='Anxiety, Mean: M = 4.20, SD = 1.10'&&r.hits[0].v.M===4.2&&r.hits[0].v.SD===1.1,'M and SD pairs read: '+(r.hits[0]&&r.hits[0].text));
ok(r.tables[0].rows.every(x=>x.length===3),'every row has three cells');
r=T.read([page(para(740),row(700,[[72,'Table 2 shows the means and standard deviations of all the study variables.']]),para(688),para(676))]);
ok(r.tables.length===0,'a sentence that starts with "Table 2 shows" is not a caption');
// table over two pages with the header printed again
const p1=page(tbl(300,'Table 3','Scores by group',H3,[[[72,'A'],[250,'1.10'],[320,'0.50']],[[72,'B'],[250,'2.20'],[320,'0.60']]]));
const p2=page(row(750,[[72,'Sleep and anxiety'],[500,'7']]),row(730,H3),row(715,[[72,'C'],[250,'3.30'],[320,'0.70']]),row(702,[[72,'D'],[250,'4.40'],[320,'0.80']]),row(680,[[72,'Note. Scores range 1 to 5.']]),para(650));
r=T.read([p1,p2]);
ok(r.tables.length===1&&r.tables[0].joined&&r.tables[0].pages.join('-')==='1-2','joined across pages 1 and 2');
ok(r.tables[0].rows.map(x=>x[0]).join()==='A,B,C,D','rows A to D in order, the repeated header dropped: '+r.tables[0].rows.map(x=>x[0]).join());
ok(r.hits.length===4,'M and SD read from both pages (4 hits)');
ok(r.hits.map(h=>h.page).join()==='1,1,2,2','each hit carries the page its row is on: '+r.hits.map(h=>h.page).join());
// continued caption
const p2b=page(row(750,[[72,'Table 3 (continued)']]),row(730,H3),row(715,[[72,'C'],[250,'3.30'],[320,'0.70']]),row(702,[[72,'D'],[250,'4.40'],[320,'0.80']]));
r=T.read([p1,p2b]);ok(r.tables.length===1&&r.tables[0].joined&&r.tables[0].rows.length===4,'a "(continued)" caption joins too');
// next page with a running head only: not joined
const p2c=page(row(750,[[72,'Sleep and anxiety'],[500,'7']]),para(730),para(718),para(706));
r=T.read([p1,p2c]);ok(r.tables.length===1&&!r.tables[0].joined,'a running head and text on the next page are not joined');
// M (SD) in one column, and decimal comma
r=T.read([page(tbl(700,'Table 4','Group means',[[72,'Group'],[250,'n'],[320,'M (SD)']],[[[72,'Control'],[250,'30'],[320,'4.2 (1.1)']],[[72,'Treated'],[250,'32'],[320,'5.1 (1.3)']]]))]);
ok(r.hits.length===2&&r.hits[1].v.M===5.1&&r.hits[1].v.SD===1.3,'a combined "M (SD)" column is read');
r=T.read([page(tbl(700,'Table 5','Means',[[72,'Scale'],[250,'Average'],[320,'Deviation']],[[[72,'Joy'],[250,'3,7241'],[320,'1,25062']],[[72,'Calm'],[250,'4,1379'],[320,'1,09297']]]))]);
ok(r.hits.length===2&&r.hits[0].v.M===3.7241&&r.hits[0].v.SD===1.25062&&/3,7241/.test(r.hits[0].text),'decimal commas are values, and the text keeps what is printed');
r=T.read([page(tbl(700,'Table 6','Counts',[[72,'Group'],[250,'n'],[320,'%']],[[[72,'Control'],[250,'30'],[320,'48']],[[72,'Treated'],[250,'32'],[320,'52']]]))]);
ok(r.tables.length===1&&r.hits.length===0,'a table with no mean and SD columns gives no mean and SD');
r=T.read([page(para(700),para(688))]);ok(r.tables.length===0&&r.hits.length===0,'a page of prose has no table');
r=T.read([]);ok(r.tables.length===0,'no pages is safe');
r=T.read([[{str:'Table 1',transform:[10,0,0,10,72,700]}]]);ok(r.tables.length===0,'a caption with nothing below it is not a table');
console.log(f?'FAILED '+f:'ALL TABLE TESTS PASSED');process.exit(f?1:0);
