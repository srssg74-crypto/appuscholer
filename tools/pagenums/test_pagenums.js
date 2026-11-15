const P=require('./pagenums.js');let f=0;
const ok=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)f++};
const pg=(head,foot)=>[head,'Body text here for the page. More words follow in this line.','Another body line of ordinary prose.',foot].filter(x=>x!==null).join('\n');
// 1 plain journal article starting at page 245: footer number alone
let pages=Array.from({length:8},(_,i)=>pg('Journal of Sleep 12 (3)',String(245+i)));
let r=P.label(pages);
ok(r.confident&&r.offset===244&&r.labels.join()==='245,246,247,248,249,250,251,252','footer numbers 245 to 252 are read');
ok(r.how.every(h=>h==='seen'),'every page is "seen"');
// 2 running head with number at the end or the start, alternating (book style)
pages=Array.from({length:10},(_,i)=>{const p=1998+i;return i%2?pg(p+' IADVL TEXTBOOK OF DERMATOLOGY',null):pg('CHAPTER 52: PSYCHOCUTANEOUS DISORDERS '+p,null)});
r=P.label(pages);ok(r.confident&&r.labels[0]==='1998'&&r.labels[9]==='2007','numbers at the start or end of running heads (book style)');
// 3 OCR misreads are put right
pages=Array.from({length:10},(_,i)=>pg('Head',String(2001+i)));pages[4]=pg('Head','200S');pages[6]=pg('Head','lOlO');pages[8]=pg('Head','2OlO');
r=P.label(pages);ok(r.labels[4]==='2005'&&r.labels[6]==='2007','"200S" and a wild misread are corrected from the sequence: '+r.labels[4]+','+r.labels[6]);
ok(r.how[6]==='fixed','a misread page is marked "fixed"');
ok(r.labels[8]==='2009'&&r.how[8]==='fixed','a number that reads one too high (2OlO on page 9) is replaced by the sequence value 2009 and marked fixed: '+r.labels[8]+' '+r.how[8]);
// 4 a page with no number is inferred between numbered pages
pages=Array.from({length:8},(_,i)=>pg('Head',i===3?null:String(10+i)));
r=P.label(pages);ok(r.labels[3]==='13'&&r.how[3]==='inferred','a page with no number between numbered pages is inferred');
// 5 an unnumbered cover far from the first numbered page gets no label
pages=[pg('Cover title',null),pg('Copyright page',null),pg('Head','149'),pg('Head','150'),pg('Head','151'),pg('Head','152')];
r=P.label(pages);ok(r.labels[0]===''&&r.labels[1]==='148'&&r.how[1]==='inferred','cover pages: one page before the first number is inferred, the cover is not');
// 6 numbers equal to the PDF page: same
pages=Array.from({length:6},(_,i)=>pg('Head',String(i+1)));r=P.label(pages);ok(r.confident&&r.same,'printed = PDF page is reported as same');
// 7 no numbers
pages=Array.from({length:6},()=>pg('Head',null));r=P.label(pages);ok(!r.confident&&r.notes.length===1,'no numbers: not confident, with a note');
// 8 too few agree
pages=Array.from({length:12},(_,i)=>pg('Head',i<2?String(30+i):null));r=P.label(pages);ok(!r.confident,'two numbers in twelve pages are not enough');
// 9 two schemes equally common (gazette "3 (2)" and footer 2): not trusted
pages=Array.from({length:8},(_,i)=>pg(String(3+i),String(i+1)));r=P.label(pages);ok(!r.confident&&/equally common/.test(r.notes[0]),'two equally common numberings: no label is used');
// 10 body numbers must not vote: a table value or year inside the first lines
pages=Array.from({length:8},(_,i)=>['Smith et al. (2021) found 45',  'Body line two.','Body line three.',String(60+i)].join('\n'));
r=P.label(pages);ok(r.confident&&r.offset===59,'an ordinary number in the text does not beat the footer');
// 11 line that is a year in a header
pages=Array.from({length:8},(_,i)=>pg('Nineteenth-Century Art Worldwide 22, no. 1 (Spring 2023)',String(149+i)));r=P.label(pages);ok(r.confident&&r.offset===148,'a volume, issue and year in the head do not vote');
// 12 empty and tiny input
ok(P.label([]).confident===false&&P.label(['a']).labels.length===1,'empty and one-page inputs are safe');
ok(P.label(['x','y','z']).confident===false,'three pages with nothing: no labels');

// 13 positions: items in the margins are found by position, whatever order the text comes in
const it=(str,x,y)=>({str:str,transform:[1,0,0,1,x,y]});
let items=[it('Body words in the middle',100,400),it('149',300,30),it('Running head',100,760),it('more body',100,380)];
let e=P.edgesOf(items,[0,0,600,800]);
ok(e.join('|')==='Running head|149'||e.includes('149')&&!e.includes('Body words in the middle'),'edgesOf keeps margin lines and drops body lines: '+JSON.stringify(e));
items=[it('CHAPTER 52: DISORDERS',50,770),it('1999',400,770)];e=P.edgesOf(items,[0,0,600,800]);ok(e[0]==='CHAPTER 52: DISORDERS 1999','items on one line are joined left to right: '+e[0]);
// 14 scrambled OCR text order: the footer is not among the last lines of the text, but the edges find it
pages=Array.from({length:6},(_,i)=>'Line one\nbody a\nbody b\n'+(60+i)+'\nbody c\nbody d\nbody e\nbody f');
let edges=Array.from({length:6},(_,i)=>['Head',String(60+i)]);
ok(!P.label(pages).confident,'text order alone misses a footer that the OCR layer put in the middle');
r=P.label(pages,edges);ok(r.confident&&r.offset===59&&r.labels[5]==='65','edges give the footer numbers: '+r.labels.join());
// 15 three pages, one number misread (35, 36, 87): the sequence puts it right
edges=[['. 35'],['36'],['87']];r=P.label(['a','b','c'],edges);ok(r.confident&&r.labels.join()==='35,36,37'&&r.how[2]==='fixed','three pages with 35, 36 and a misread 87 give 35, 36, 37');
console.log(f?'FAILED '+f:'ALL PAGE NUMBER TESTS PASSED');process.exit(f?1:0);
