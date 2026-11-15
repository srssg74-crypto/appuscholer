import fs from 'fs';import {createRequire} from 'module';const require=createRequire(import.meta.url);
const P=require('./pagenums.js');const pdfjs=await import(process.env.PDFJS);
for(const f of process.argv.slice(2)){
  const pdf=await pdfjs.getDocument({data:new Uint8Array(fs.readFileSync(f)),useSystemFonts:true}).promise;const pages=[],edges=[];
  for(let k=1;k<=pdf.numPages;k++){const pg=await pdf.getPage(k),tc=await pg.getTextContent();edges.push(P.edgesOf(tc.items,pg.view));pages.push(tc.items.map(i=>i.str).join('\n'))}
  const r=P.label(pages,edges);console.log(f.split('/').pop(),'confident',r.confident,'offset',r.offset,'votes',r.votes+'/'+pdf.numPages,'\n ',r.labels.map((l,i)=>(i+1)+'→'+(l||'-')+(r.how[i]?'('+r.how[i][0]+')':'')).join(' '),r.notes.join(' '));
  console.log('  edges p1:',JSON.stringify(edges[0]),'p2:',JSON.stringify(edges[1]||[]));
}
