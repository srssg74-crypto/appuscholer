// AppuScholar Module 1 backend adapter. Firebase Web SDK 11.10.0 (official gstatic CDN).
// Configure with init({apiKey, authDomain, projectId, appId, ...}). Never expose service-account credentials.
import { initializeApp, getApps } from 'https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js';
import {
  getAuth, createUserWithEmailAndPassword, sendEmailVerification, signInWithEmailAndPassword,
  signOut as firebaseSignOut, onAuthStateChanged, reload, getIdToken,
  EmailAuthProvider, reauthenticateWithCredential, deleteUser, sendPasswordResetEmail
} from 'https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js';
import {
  getFirestore, doc, getDoc, getDocs, collection, query, where, orderBy, limit,
  writeBatch, runTransaction, serverTimestamp, Timestamp, increment, deleteDoc, setDoc
} from 'https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js';

const CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
const CODE_RE = /^[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{10}$/;
const USER_KEYS = ['displayName','email','institution','course','plan','status','inviteCode','accessExpiresAt','consent','createdAt','schemaVersion'];
const TOMBSTONE_KEYS = ['status','deletionRequestedAt','schemaVersion'];
const errorMap = {
  'auth/email-already-in-use':'EMAIL_IN_USE','auth/invalid-email':'INVALID_EMAIL','auth/weak-password':'WEAK_PASSWORD',
  'auth/invalid-credential':'SIGN_IN_FAILED','auth/user-not-found':'SIGN_IN_FAILED','auth/wrong-password':'SIGN_IN_FAILED',
  'auth/too-many-requests':'TRY_LATER','auth/network-request-failed':'NETWORK','auth/requires-recent-login':'REAUTH_REQUIRED',
  'permission-denied':'NOT_ALLOWED','unavailable':'NETWORK','failed-precondition':'NOT_ALLOWED'
};
let app, auth, db, config, sessionUnsubscribe = null;
const pendingSignup = { email: '', displayName: '', institution: '', course: '', inviteCode: '', consentVersion: '', ageConfirmed18: false };
function fail(code='UNKNOWN') { const e = new Error(code); e.code = code; return e; }
function wrapError(e) { if (e?.code && /^[A-Z_]+$/.test(e.code)) return e; const code = errorMap[e?.code] || (e?.code?.startsWith('auth/') ? 'AUTH_ERROR' : 'OPERATION_FAILED'); return fail(code); }
function requireInit() { if (!auth || !db) throw fail('NOT_INITIALIZED'); }
function normalizeCode(value) { return String(value || '').toUpperCase().replace(/[\s-]/g, ''); }
function validCode(value) { return CODE_RE.test(normalizeCode(value)); }
function nowTimestamp(date) { return Timestamp.fromDate(date); }
function safeProfile(s) { return s ? { ...s, accessExpired: s.accessExpiresAt?.toDate ? s.accessExpiresAt.toDate().getTime() <= Date.now() : true } : null; }
function sessionState(user, profile) {
  if (!user) return { state: 'signedOut', profile: null };
  if (!user.emailVerified) return { state: 'unverified', profile: null };
  if (!profile) return { state: 'needsInvite', profile: null };
  if (profile.status === 'deleting') return { state: 'deletionPending', profile: null };
  if (profile.status === 'suspended' || !profile.accessExpiresAt || profile.accessExpiresAt.toMillis() <= Date.now()) return { state: 'blocked', profile: safeProfile(profile) };
  return { state: 'ready', profile: safeProfile(profile) };
}
async function currentProfile(user=auth?.currentUser) { if (!user) return null; const snap = await getDoc(doc(db,'users',user.uid)); return snap.exists() ? snap.data() : null; }
async function emitSession(callback, user) { try { const p = user?.emailVerified ? await currentProfile(user) : null; callback(sessionState(user,p)); } catch { callback({state:user ? 'blocked':'signedOut',profile:null}); } }
function generateCode() { const bytes = new Uint8Array(10); crypto.getRandomValues(bytes); let out=''; for (const b of bytes) out += CODE_ALPHABET[b % CODE_ALPHABET.length]; return out; }
async function adminUser() { requireInit(); const u=auth.currentUser; if(!u) throw fail('NOT_SIGNED_IN'); const a=await getDoc(doc(db,'admins',u.uid)); if(!a.exists()) throw fail('ADMIN_ONLY'); return u; }

export const appuBackend = {
  init(firebaseConfig) {
    if (!firebaseConfig || !firebaseConfig.apiKey || !firebaseConfig.projectId || !firebaseConfig.appId) throw fail('BAD_CONFIG');
    config = firebaseConfig; app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig); auth=getAuth(app); db=getFirestore(app); return Promise.resolve();
  },
  signUp({email,password,displayName,institution='',course='',inviteCode,consentVersion}) {
    return (async()=>{ try { requireInit(); if(!email||!password||password.length<10) throw fail('INVALID_INPUT'); if(!String(displayName||'').trim()||String(displayName).trim().length>80||String(institution).length>120||String(course).length>80) throw fail('INVALID_INPUT'); if(!validCode(inviteCode)) throw fail('INVALID_CODE'); Object.assign(pendingSignup,{email,displayName:String(displayName).trim(),institution,course,inviteCode:normalizeCode(inviteCode),consentVersion,ageConfirmed18:true}); const cred=await createUserWithEmailAndPassword(auth,email,password); /* No name in Firebase Auth: Auth data is processed in the US; the name lives only in Firestore (Mumbai). */ await sendEmailVerification(cred.user); return {uid:cred.user.uid,verificationSent:true}; } catch(e){throw wrapError(e);} })();
  },
  resendVerification() { return (async()=>{try{requireInit();if(!auth.currentUser)throw fail('NOT_SIGNED_IN');await sendEmailVerification(auth.currentUser);return true;}catch(e){throw wrapError(e);}})(); },
  signIn(email,password) { return (async()=>{try{requireInit();const c=await signInWithEmailAndPassword(auth,email,password);await c.user.reload();if(c.user.emailVerified)await c.user.getIdToken(true);return sessionState(c.user, c.user.emailVerified ? await currentProfile(c.user) : null);}catch(e){throw wrapError(e);}})(); },
  signOut() { return (async()=>{try{requireInit();await firebaseSignOut(auth);}catch(e){throw wrapError(e);}})(); },
  async redeemInvite(inviteCode, profileDetails) {
    try {
      requireInit(); const user=auth.currentUser; if(!user)throw fail('NOT_SIGNED_IN'); await user.reload(); await user.getIdToken(true); if(!user.emailVerified)throw fail('EMAIL_NOT_VERIFIED');
      const code=normalizeCode(inviteCode); if(!validCode(code))throw fail('INVALID_CODE');
      let d;
      if(!profileDetails && (!pendingSignup.displayName || !pendingSignup.consentVersion)) { try { const saved=JSON.parse(sessionStorage.getItem('appuSignupDraft')||'null'); if(saved) Object.assign(pendingSignup,{displayName:saved.displayName||'',institution:saved.institution||'',course:saved.course||'',inviteCode:saved.inviteCode||'',consentVersion:saved.consentVersion||'',ageConfirmed18:saved.ageConfirmed18===true}); } catch {} }
      if(profileDetails) { d={displayName:String(profileDetails.displayName||'').trim(),institution:String(profileDetails.institution||''),course:String(profileDetails.course||''),consentVersion:String(profileDetails.consentVersion||''),ageConfirmed18:profileDetails.ageConfirmed18===true}; }
      else { d={displayName:pendingSignup.displayName,institution:pendingSignup.institution,course:pendingSignup.course,consentVersion:pendingSignup.consentVersion,ageConfirmed18:pendingSignup.ageConfirmed18}; }
      if(!d.displayName||d.displayName.length>80||d.institution.length>120||d.course.length>80||!d.consentVersion||!d.ageConfirmed18)throw fail('INVALID_INPUT');
      const inviteRef=doc(db,'invites',code), userRef=doc(db,'users',user.uid), redemptionRef=doc(db,'invites',code,'redemptions',user.uid);
      const invSnap=await getDoc(inviteRef); if(!invSnap.exists())throw fail('INVALID_CODE'); const inv=invSnap.data();
      const existing=await getDoc(userRef); if(existing.exists()) { if(existing.data().status==='deleting')throw fail('DELETION_PENDING'); throw fail('ALREADY_REDEEMED'); }
      /* One hour short of the full period, so a device clock running fast cannot push the date past what the rules allow. */ const expiresAt=Timestamp.fromMillis(Date.now()+Number(inv.accessDays)*86400000-3600000);
      const batch=writeBatch(db);
      batch.set(userRef,{displayName:d.displayName,email:user.email,institution:d.institution,course:d.course,plan:'free',status:'active',inviteCode:code,accessExpiresAt:expiresAt,consent:{version:d.consentVersion,acceptedAt:serverTimestamp(),ageConfirmed18:true},createdAt:serverTimestamp(),schemaVersion:1});
      batch.set(redemptionRef,{uid:user.uid,redeemedAt:serverTimestamp()}); batch.update(inviteRef,{usedCount:increment(1)});
      await batch.commit(); Object.assign(pendingSignup,{email:'',displayName:'',institution:'',course:'',inviteCode:'',consentVersion:'',ageConfirmed18:false}); return await this.getMyProfile();
    } catch(e) { if(['INVALID_CODE','permission-denied','failed-precondition','ALREADY_REDEEMED'].includes(e?.code)) throw fail('INVALID_CODE'); throw wrapError(e); }
  },
  getMyProfile() { return (async()=>{try{requireInit();const u=auth.currentUser;if(!u)throw fail('NOT_SIGNED_IN');const p=await currentProfile(u);return safeProfile(p);}catch(e){throw wrapError(e);}})(); },
  updateMyProfile({displayName,institution='',course=''}) { return (async()=>{try{requireInit();const u=auth.currentUser;if(!u)throw fail('NOT_SIGNED_IN');if(!String(displayName||'').trim()||String(displayName).trim().length>80||String(institution).length>120||String(course).length>80)throw fail('INVALID_INPUT');const ref=doc(db,'users',u.uid);await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).updateDoc(ref,{displayName:String(displayName).trim(),institution,course});return await this.getMyProfile();}catch(e){throw wrapError(e);}})(); },
  acceptNewConsent(version) { return (async()=>{try{requireInit();const u=auth.currentUser;if(!u)throw fail('NOT_SIGNED_IN');if(!version)throw fail('INVALID_INPUT');const ref=doc(db,'users',u.uid);const s=await getDoc(ref);if(!s.exists())throw fail('NO_PROFILE');await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).updateDoc(ref,{consent:{...s.data().consent,version,acceptedAt:serverTimestamp()}});return await this.getMyProfile();}catch(e){throw wrapError(e);}})(); },
  deleteMyAccount(password) { return (async()=>{try{requireInit();const u=auth.currentUser;if(!u||!u.email)throw fail('NOT_SIGNED_IN');const cred=EmailAuthProvider.credential(u.email,password);await reauthenticateWithCredential(u,cred);const userRef=doc(db,'users',u.uid);const snap=await getDoc(userRef);if(!snap.exists())throw fail('NO_PROFILE');if(snap.data().status==='deleting')throw fail('DELETION_PENDING');const code=snap.data().inviteCode;const redRef=doc(db,'invites',code,'redemptions',u.uid);const batch=writeBatch(db);batch.delete(redRef);batch.set(userRef,{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1});await batch.commit();try{await deleteUser(u);}catch(e){await firebaseSignOut(auth);throw fail('DELETION_PENDING');}return true;}catch(e){throw wrapError(e);}})(); },
  finishDeletion(password) { return (async()=>{try{requireInit();const u=auth.currentUser;if(!u||!u.email)throw fail('NOT_SIGNED_IN');await reauthenticateWithCredential(u,EmailAuthProvider.credential(u.email,password));const snap=await getDoc(doc(db,'users',u.uid));if(!snap.exists()||snap.data().status!=='deleting')throw fail('NO_PENDING_DELETION');await deleteUser(u);return true;}catch(e){throw wrapError(e);}})(); },
  async onSessionChange(callback) { requireInit(); if(sessionUnsubscribe)sessionUnsubscribe(); sessionUnsubscribe=onAuthStateChanged(auth,u=>{void emitSession(callback,u);});return ()=>{if(sessionUnsubscribe)sessionUnsubscribe();sessionUnsubscribe=null;}; },
  createInvite({label,redeemBy,accessDays=180,maxUses}) { return (async()=>{try{const u=await adminUser();if(!String(label||'').trim()||String(label).length>120||!Number.isInteger(accessDays)||accessDays<1||accessDays>366||!Number.isInteger(maxUses)||maxUses<1)throw fail('INVALID_INPUT');const date=redeemBy instanceof Date?redeemBy:new Date(redeemBy);if(!Number.isFinite(date.getTime())||date.getTime()<=Date.now())throw fail('INVALID_INPUT');let code,ref;for(let i=0;i<5;i++){code=generateCode();ref=doc(db,'invites',code);if(!(await getDoc(ref)).exists())break;code=null;}if(!code)throw fail('TRY_AGAIN');await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).setDoc(ref,{label:String(label).trim(),createdBy:u.uid,createdAt:serverTimestamp(),redeemBy:Timestamp.fromDate(date),accessDays,maxUses,usedCount:0,active:true});return code.match(/.{5}/g).join('-');}catch(e){throw wrapError(e);}})(); },
  listInvites() { return (async()=>{try{await adminUser();const s=await getDocs(collection(db,'invites'));return s.docs.map(x=>({code:x.id.match(/.{5}/g).join('-'),...x.data()}));}catch(e){throw wrapError(e);}})(); },
  setInviteActive(code,active) { return (async()=>{try{await adminUser();const c=normalizeCode(code);if(!validCode(c)||typeof active!=='boolean')throw fail('INVALID_INPUT');await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).updateDoc(doc(db,'invites',c),{active});}catch(e){throw wrapError(e);}})(); },
  setUserStatus(uid,status) { return (async()=>{try{await adminUser();if(!['active','suspended'].includes(status))throw fail('INVALID_INPUT');await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).updateDoc(doc(db,'users',uid),{status});}catch(e){throw wrapError(e);}})(); },
  extendAccess(uid,newExpiry) { return (async()=>{try{await adminUser();const d=newExpiry instanceof Date?newExpiry:new Date(newExpiry);if(!Number.isFinite(d.getTime()))throw fail('INVALID_INPUT');await (await import('https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js')).updateDoc(doc(db,'users',uid),{accessExpiresAt:Timestamp.fromDate(d)});}catch(e){throw wrapError(e);}})(); },
  listExpiredUsers(minDaysAfterExpiry=88) { return (async()=>{try{await adminUser();if(!Number.isInteger(minDaysAfterExpiry)||minDaysAfterExpiry<0)throw fail('INVALID_INPUT');const cutoff=Timestamp.fromMillis(Date.now()-minDaysAfterExpiry*86400000);const s=await getDocs(query(collection(db,'users'),where('accessExpiresAt','<',cutoff)));return s.docs.filter(x=>x.data().status!=='deleting').map(x=>{const d=x.data();return{uid:x.id,displayName:d.displayName,email:d.email,accessExpiresAt:d.accessExpiresAt.toDate(),daysSinceExpiry:Math.floor((Date.now()-d.accessExpiresAt.toMillis())/86400000)}});}catch(e){throw wrapError(e);}})(); },
  eraseExpiredUser(uid) { return (async()=>{try{await adminUser();if(!uid)throw fail('INVALID_INPUT');await setDoc(doc(db,'users',uid),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1});}catch(e){throw wrapError(e);}})(); },
  purgeDeletionMarkers(olderThanDays=30) { return (async()=>{try{await adminUser();if(!Number.isInteger(olderThanDays)||olderThanDays<1)throw fail('INVALID_INPUT');const cutoff=Timestamp.fromMillis(Date.now()-olderThanDays*86400000);const q=query(collection(db,'users'),where('status','==','deleting'));const s=await getDocs(q);const targets=s.docs.filter(x=>x.data().deletionRequestedAt?.toMillis?.() < cutoff.toMillis()).slice(0,400);for(let i=0;i<targets.length;i+=400){const b=writeBatch(db);targets.slice(i,i+400).forEach(x=>b.delete(x.ref));await b.commit();}return targets.length;}catch(e){throw wrapError(e);}})(); }
};