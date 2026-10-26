"""Janani cohort: entirely made-up data for testing Appuscholar end to end. No real person."""
import numpy as np, csv
rng=np.random.default_rng(20261026)
N=1240
age=np.clip(rng.normal(24.5,4.0,N).round(),18,42).astype(int)
parity=np.where(rng.random(N)<0.42,'First pregnancy','Second or later')
edu=rng.choice(['Up to class 8','Class 9-12','Graduate or above'],N,p=[.32,.43,.25])
res=np.where(rng.random(N)<0.55,'Urban','Rural')
hb16=np.clip(rng.normal(10.9,1.2,N),6.8,14.5)
ifa=np.clip(rng.normal(118,38,N),0,180).round().astype(int)          # IFA tablets taken of 180
hb34=np.clip(hb16+0.009*(ifa-90)+rng.normal(0.15,0.55,N),6.5,14.8)
ferr=np.clip(np.exp(rng.normal(np.log(22)+0.18*(hb16-10.9),0.6,N)),3,180)
tsh=np.clip(np.exp(rng.normal(np.log(2.1),0.5,N)),0.2,12)
anaemia=np.where(hb34<11,'Yes','No')
# anxiety latent: higher with anaemia, lower Hb, first pregnancy, rural
lat=rng.normal(0,1,N)+0.35*(hb34<11)+0.12*(parity=='First pregnancy')+0.10*(res=='Rural')
gad=np.zeros((N,7),int)
for j in range(7):
    p=1/(1+np.exp(-(lat*1.25-1.85+rng.normal(0,0.55,N))))
    gad[:,j]=np.clip((p*3.6+rng.normal(0,0.45,N)).round(),0,3)
gt=gad.sum(1)
# self-esteem (RSES 0-3 coding, reverse items 2,5,6,8,9) lower with anxiety
se=rng.normal(0,1,N)-0.30*(gt-gt.mean())/gt.std()
rses=np.zeros((N,10),int)
for j in range(10):
    v=np.clip((1.9+0.55*se+rng.normal(0,0.6,N)).round(),0,3)       # higher = more self-esteem
    rses[:,j]=(3-v) if (j+1) in (2,5,6,8,9) else v                  # raw answers: SA=3 ... SD=0
swls=np.zeros((N,5),int)
ls=0.45*se-0.25*(gt-gt.mean())/gt.std()+rng.normal(0,0.85,N)
for j in range(5):
    swls[:,j]=np.clip((4.6+0.9*ls+rng.normal(0,0.7,N)).round(),1,7)
ids=[f'M{i+1:04d}' for i in range(N)]
with open('janani_mothers.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['participant_id','age','parity','education','residence','hb_16wk','hb_34wk','ferritin_16wk','tsh_16wk','ifa_tablets_taken','anaemia_34wk']+[f'GAD7_{j+1:02d}' for j in range(7)]+[f'RSES_{j+1:02d}' for j in range(10)]+[f'SWLS_{j+1:02d}' for j in range(5)])
    for i in range(N):
        miss=lambda v: '' if rng.random()<0.01 else v
        w.writerow([ids[i],age[i],parity[i],edu[i],res[i],f'{hb16[i]:.1f}',f'{hb34[i]:.1f}',miss(f'{ferr[i]:.0f}'),miss(f'{tsh[i]:.2f}'),ifa[i],anaemia[i]]+list(gad[i])+list(rses[i])+list(swls[i]))
# fathers: a subset of couples
fi=np.sort(rng.choice(N,612,replace=False))
with open('janani_fathers.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['participant_id','father_age','mother_GAD7_total','father_GAD7_total']+[f'GAD7_{j+1:02d}' for j in range(7)])
    for i in fi:
        fl=0.45*lat[i]+rng.normal(-0.55,0.9)
        it=[int(np.clip(round((1/(1+np.exp(-(fl*1.2-1.3))))*3.4+rng.normal(0,0.45)),0,3)) for _ in range(7)]
        w.writerow([ids[i],int(np.clip(round(age[i]+rng.normal(4,2.5)),20,55)),int(gt[i]),sum(it)]+it)
# infants: live births (some losses / moved away)
alive=np.sort(rng.choice(N,1198,replace=False))
with open('janani_infants.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['infant_id','mother_id','infant_sex','gestational_weeks','birth_weight_g','apgar_5min','nicu_admission','low_birth_weight','maternal_hb_34wk','maternal_GAD7_total','mr1_given_9mo','measles_igg_miu_ml','seroconverted','fever_after_vaccine','paracetamol_given'])
    for k,i in enumerate(alive):
        sex='Boy' if rng.random()<0.515 else 'Girl'
        ga=float(np.clip(rng.normal(38.6-0.25*(hb34[i]<11),1.5),30,42))
        bw=2850+130*(ga-38.6)+75*(hb34[i]-11)-14*(gt[i]-gt.mean())+(85 if sex=='Boy' else 0)+rng.normal(0,330)
        bw=int(np.clip(bw,1100,4600))
        apg=int(np.clip(round(rng.normal(8.6+0.0006*(bw-2800),0.8)),3,10))
        nicu='Yes' if (bw<2000 or rng.random()<0.06+0.10*(bw<2500)) else 'No'
        given='Yes' if rng.random()<0.94 else 'No'
        if given=='Yes':
            fever=rng.random()<0.22
            para=fever and rng.random()<0.65 or (rng.random()<0.05)
            igg=np.exp(rng.normal(np.log(420)+0.00018*(bw-2850)-0.25*para,0.85))
            sero='Yes' if igg>=120 else 'No'
            w.writerow([f'I{k+1:04d}',ids[i],sex,f'{ga:.1f}',bw,apg,nicu,'Yes' if bw<2500 else 'No',f'{hb34[i]:.1f}',int(gt[i]),'Yes',f'{igg:.0f}',sero,'Yes' if fever else 'No','Yes' if para else 'No'])
        else:
            w.writerow([f'I{k+1:04d}',ids[i],sex,f'{ga:.1f}',bw,apg,nicu,'Yes' if bw<2500 else 'No',f'{hb34[i]:.1f}',int(gt[i]),'No','','','',''])
print('mothers',N,'fathers',len(fi),'infants',len(alive),'total',N+len(fi)+len(alive))
