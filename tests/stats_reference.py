"""Builds the fixed dataset for the Statistics Lab check and the reference answers.
Reference values come from SciPy and NumPy only (statsmodels is not installed here); formulas
that SciPy lacks (Welch ANOVA, Cochran's Q, repeated-measures and mixed ANOVA, alpha, regression
standard errors, logistic regression) are written out below from their textbook definitions.
Run: python3 tests/stats_reference.py  -> writes tests/stats_data.csv and tests/stats_ref.json"""
import json, numpy as np
from scipy import stats
rng=np.random.default_rng(20261020)
n=60
g2=np.array(['A','B']*30); g3=np.array(['X','Y','Z']*20); f2=np.array(['P']*30+['Q']*30)
# balanced 2x3 for two-way ANOVA: f2 x g3 = 10 per cell
pre=rng.normal(50,10,n).round(1)
post=(pre+rng.normal(3,6,n)).round(1)
t3=(post+rng.normal(2,6,n)).round(1)
score=(rng.normal(20,4,n)+np.where(g2=='B',2.5,0)+np.select([g3=='Y',g3=='Z'],[1.5,3.0],0)+np.where(f2=='Q',1.0,0)).round(2)
x=rng.normal(10,3,n).round(2); m=(0.5*x+rng.normal(0,2,n)).round(2); w=rng.normal(5,2,n).round(2)
y=(2+0.4*x+0.6*m+0.15*x*w-0.2*w+rng.normal(0,2.5,n)).round(2)
p=1/(1+np.exp(-(-3+0.25*x+0.1*w))); out=(rng.random(n)<p).astype(int)
b1=(rng.random(n)<0.4).astype(int); b2=np.where(rng.random(n)<0.7,b1,1-b1); b3=(rng.random(n)<0.6).astype(int)
cat=np.where(rng.random(n)<np.where(g2=='A',0.3,0.6),'yes','no')
colour=rng.choice(['red','green','blue'],n,p=[0.5,0.3,0.2])
lat=rng.normal(0,1,n); items=np.clip(np.round(3+lat[:,None]*0.9+rng.normal(0,0.8,(n,5))),1,5).astype(int)
cols={'id':np.arange(1,n+1),'g2':g2,'g3':g3,'f2':f2,'pre':pre,'post':post,'t3':t3,'score':score,'x':x,'m':m,'w':w,'y':y,'out':out,'b1':b1,'b2':b2,'b3':b3,'cat':cat,'colour':colour}
for i in range(5): cols['q%d'%(i+1)]=items[:,i]
names=list(cols)
with open('tests/stats_data.csv','w') as f:
    f.write(','.join(names)+'\n')
    for r in range(n): f.write(','.join(str(cols[k][r]) for k in names)+'\n')
R={}
def ols(Y,Xs):
    X=np.column_stack([np.ones(len(Y))]+Xs);b,_,_,_=np.linalg.lstsq(X,Y,rcond=None);res=Y-X@b;df=len(Y)-X.shape[1]
    s2=res@res/df;se=np.sqrt(np.diag(s2*np.linalg.inv(X.T@X)));t=b/se;pv=2*stats.t.sf(abs(t),df)
    r2=1-res@res/((Y-Y.mean())@(Y-Y.mean()));return dict(b=b.tolist(),se=se.tolist(),t=t.tolist(),p=pv.tolist(),r2=r2,df=df,k=X.shape[1]-1)
R['desc']=dict(n=n,m=score.mean(),sd=score.std(ddof=1),median=float(np.median(score)))
r=stats.ttest_1samp(score,20);R['ttest1']=dict(t=r.statistic,df=n-1,p=r.pvalue)
a,b=score[g2=='A'],score[g2=='B'];r=stats.ttest_ind(a,b,equal_var=False);rs=stats.ttest_ind(a,b)
v1,v2=a.var(ddof=1),b.var(ddof=1);dfw=(v1/30+v2/30)**2/((v1/30)**2/29+(v2/30)**2/29)
R['ttestInd']=dict(t=r.statistic,df=dfw,p=r.pvalue,tS=rs.statistic,pS=rs.pvalue)
r=stats.ttest_rel(pre,post);R['ttestPaired']=dict(t=r.statistic,df=n-1,p=r.pvalue)
gs=[score[g3==k] for k in 'XYZ'];r=stats.f_oneway(*gs);R['anova1']=dict(F=r.statistic,df1=2,df2=n-3,p=r.pvalue)
k=3;ns=np.array([len(q) for q in gs]);ms=np.array([q.mean() for q in gs]);vs=np.array([q.var(ddof=1) for q in gs]);wt=ns/vs;mw=(wt*ms).sum()/wt.sum()
A=(wt*(ms-mw)**2).sum()/(k-1);lam=((1-wt/wt.sum())**2/(ns-1)).sum();Fw=A/(1+2*(k-2)*lam/(k*k-1));df2w=(k*k-1)/(3*lam)
R['welchAnova']=dict(F=Fw,df1=k-1,df2=df2w,p=stats.f.sf(Fw,k-1,df2w))
tk=stats.tukey_hsd(*gs);R['tukey']=dict(p_XY=tk.pvalue[0,1],p_XZ=tk.pvalue[0,2],p_YZ=tk.pvalue[1,2])
lr=stats.linregress(x,y);R['regression']=dict(b=lr.slope,a=lr.intercept,r2=lr.rvalue**2,p=lr.pvalue,t=lr.slope/lr.stderr,df=n-2)
r=stats.mannwhitneyu(a,b,method='asymptotic');R['mannwhitney']=dict(U=min(r.statistic,30*30-r.statistic),p=r.pvalue)
r=stats.wilcoxon(pre,post,method='approx');R['wilcoxon']=dict(Wmin=r.statistic,p=r.pvalue)
r=stats.kruskal(*gs);R['kruskal']=dict(H=r.statistic,df=2,p=r.pvalue)
r=stats.pearsonr(x,y);R['pearson']=dict(r=r.statistic,df=n-2,p=r.pvalue)
r=stats.spearmanr(x,y);R['spearman']=dict(rho=r.statistic,p=r.pvalue)
tab=np.array([[((g2==gg)&(cat==cc)).sum() for cc in ['no','yes']] for gg in ['A','B']])
c=stats.chi2_contingency(tab,correction=False);cy=stats.chi2_contingency(tab,correction=True)
R['chisq']=dict(chi2=c.statistic,df=1,p=c.pvalue,chi2_yates=cy.statistic,p_yates=cy.pvalue)
cnt=[(colour==k).sum() for k in ['blue','green','red']];r=stats.chisquare(cnt);R['gof']=dict(chi2=r.statistic,df=2,p=r.pvalue)
bb=int(((b1==1)&(b2==0)).sum());cc=int(((b1==0)&(b2==1)).sum());R['mcnemar']=dict(b=bb,c=cc,p_exact=stats.binomtest(min(bb,cc),bb+cc,0.5).pvalue)
B=np.column_stack([b1,b2,b3]);kk=3;G=B.sum(0);L=B.sum(1);Q=(kk-1)*(kk*(G**2).sum()-G.sum()**2)/(kk*L.sum()-(L**2).sum())
R['cochran']=dict(Q=Q,df=2,p=stats.chi2.sf(Q,2))
r=stats.friedmanchisquare(pre,post,t3);R['friedman']=dict(chi2=r.statistic,df=2,p=r.pvalue)
Yrm=np.column_stack([pre,post,t3]);gm=Yrm.mean();ssT=((Yrm.mean(0)-gm)**2).sum()*n;ssS=((Yrm.mean(1)-gm)**2).sum()*3;ssE=((Yrm-gm)**2).sum()-ssT-ssS
F=(ssT/2)/(ssE/(2*(n-1)));R['rmanova']=dict(F=F,df1=2,df2=2*(n-1),p=stats.f.sf(F,2,2*(n-1)))
# mixed: g2 between, pre/post/t3 within
grp=g2;lv=['A','B'];nj=np.array([(grp==l).sum() for l in lv]);T=3
ssTot=((Yrm-gm)**2).sum();subj=Yrm.mean(1);ssBS=((subj-gm)**2).sum()*T
ssG=sum(nj[i]*T*(Yrm[grp==l].mean()-gm)**2 for i,l in enumerate(lv));ssSw=ssBS-ssG
ssTime=n*((Yrm.mean(0)-gm)**2).sum();cellm=np.array([Yrm[grp==l].mean(0) for l in lv])
ssGT=sum(nj[i]*((cellm[i]-Yrm[grp==l].mean()-Yrm.mean(0)+gm)**2).sum() for i,l in enumerate(lv));ssWres=ssTot-ssBS-ssTime-ssGT
dfG,dfSw,dfT,dfGT,dfW=1,n-2,2,2,2*(n-2)
R['mixed']=dict(F_group=(ssG/dfG)/(ssSw/dfSw),F_time=(ssTime/dfT)/(ssWres/dfW),F_inter=(ssGT/dfGT)/(ssWres/dfW),df_group=[dfG,dfSw],df_time=[dfT,dfW])
# two-way ANOVA, balanced f2 x g3
gmS=score.mean();ssA=sum(((f2==a_).sum())*(score[f2==a_].mean()-gmS)**2 for a_ in 'PQ');ssB=sum(((g3==b_).sum())*(score[g3==b_].mean()-gmS)**2 for b_ in 'XYZ')
ssCells=sum(((f2==a_)&(g3==b_)).sum()*(score[(f2==a_)&(g3==b_)].mean()-gmS)**2 for a_ in 'PQ' for b_ in 'XYZ');ssAB=ssCells-ssA-ssB;ssW=((score-gmS)**2).sum()-ssCells;dfW2=n-6
R['anova2']=dict(F_A=(ssA/1)/(ssW/dfW2),F_B=(ssB/2)/(ssW/dfW2),F_AB=(ssAB/2)/(ssW/dfW2),dfW=dfW2)
o=ols(y,[x,m,w]);R['mregress']=dict(b=o['b'],p=o['p'],r2=o['r2'],df=o['df'])
xc,wc=x-x.mean(),w-w.mean();o=ols(y,[xc,wc,xc*wc]);R['moderate']=dict(b_int=o['b'][3],p_int=o['p'][3],t_int=o['t'][3])
oa=ols(m,[x]);ob=ols(y,[x,m]);R['mediate']=dict(a=oa['b'][1],b=ob['b'][2],cprime=ob['b'][1],ab=oa['b'][1]*ob['b'][2],c=ols(y,[x])['b'][1])
X=np.column_stack([np.ones(n),x,w]);bet=np.zeros(3)
for _ in range(50):
    pr=1/(1+np.exp(-X@bet));Wd=pr*(1-pr);H=X.T@(X*Wd[:,None]);bet=bet+np.linalg.solve(H,X.T@(out-pr))
se=np.sqrt(np.diag(np.linalg.inv(H)));R['logistic']=dict(b=bet.tolist(),se=se.tolist(),p=(2*stats.norm.sf(abs(bet/se))).tolist(),OR=np.exp(bet).tolist())
it=items.astype(float);kI=it.shape[1];R['alpha']=dict(alpha=kI/(kI-1)*(1-it.var(0,ddof=1).sum()/it.sum(1).var(ddof=1)))
json.dump(R,open('tests/stats_ref.json','w'),indent=1,default=float)
print('ok',len(R),'tests')
