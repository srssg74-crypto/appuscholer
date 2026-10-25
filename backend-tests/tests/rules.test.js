import {initializeTestEnvironment, assertSucceeds, assertFails} from '@firebase/rules-unit-testing';
import {doc, setDoc, getDoc, getDocs, collection, query, where, updateDoc, deleteDoc, writeBatch, Timestamp, serverTimestamp, increment} from 'firebase/firestore';
import fs from 'node:fs';
import {before, after, beforeEach, test} from 'node:test';
import assert from 'node:assert/strict';

const PROJECT_ID='appuscholar-rules-tests';
let env;
const future = days => Timestamp.fromMillis(Date.now()+days*86400000);
const inviteData = (overrides={}) => ({label:'MA Psych 2026 trial',createdBy:'admin1',createdAt:serverTimestamp(),redeemBy:future(10),accessDays:180,maxUses:3,usedCount:0,active:true,...overrides});
const userData = (uid,code='ABCDEFGHJK',overrides={}) => ({displayName:'Test Student',email:`${uid}@example.test`,institution:'',course:'',plan:'free',status:'active',inviteCode:code,accessExpiresAt:future(100),consent:{version:'2026-10-v1',acceptedAt:serverTimestamp(),ageConfirmed18:true},createdAt:serverTimestamp(),schemaVersion:1,...overrides});
const context = (uid, claims={}) => env.authenticatedContext(uid,{email:`${uid}@example.test`,email_verified:true,...claims});
async function seedInvite(code='ABCDEFGHJK',data={}) { await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),`invites/${code}`),inviteData(data))); }
async function seedAdmin(uid='admin1') { await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),`admins/${uid}`),{createdAt:Timestamp.now()})); }
async function seedUser(uid='student1',code='ABCDEFGHJK',overrides={}) { await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),`users/${uid}`),userData(uid,code,overrides))); }
async function seedRedemption(uid='student1',code='ABCDEFGHJK') { await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),`invites/${code}/redemptions/${uid}`),{uid,redeemedAt:Timestamp.now()})); }
async function redeem(uid='student1',code='ABCDEFGHJK',overrides={}) {
  const db=context(uid).firestore(); const b=writeBatch(db);
  b.set(doc(db,`users/${uid}`),userData(uid,code,overrides));
  b.set(doc(db,`invites/${code}/redemptions/${uid}`),{uid,redeemedAt:serverTimestamp()});
  b.update(doc(db,`invites/${code}`),{usedCount:increment(1)});
  return b.commit();
}
async function tombstoneBatch(uid='student1',code='ABCDEFGHJK',overrides={}) {
  const db=context(uid).firestore(); const b=writeBatch(db);
  b.delete(doc(db,`invites/${code}/redemptions/${uid}`));
  b.set(doc(db,`users/${uid}`),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1,...overrides});
  return b.commit();
}
before(async()=>{env=await initializeTestEnvironment({projectId:PROJECT_ID,firestore:{rules:fs.readFileSync(new URL('../firestore.rules',import.meta.url),'utf8')}});});
after(async()=>{await env.cleanup();});
beforeEach(async()=>{await env.clearFirestore();});

test('1. Valid batch redemption succeeds',async()=>{await seedInvite();await assertSucceeds(redeem());});
test('2. Creating a users doc outside the batch fails',async()=>{await seedInvite();await assertFails(setDoc(doc(context('student1').firestore(),'users/student1'),userData('student1')));});
test('3. Redemption with an unverified email fails',async()=>{await seedInvite();const db=env.authenticatedContext('student1',{email:'student1@example.test',email_verified:false}).firestore();const b=writeBatch(db);b.set(doc(db,'users/student1'),userData('student1'));b.set(doc(db,'invites/ABCDEFGHJK/redemptions/student1'),{uid:'student1',redeemedAt:serverTimestamp()});b.update(doc(db,'invites/ABCDEFGHJK'),{usedCount:increment(1)});await assertFails(b.commit());});
test('4. Expired code fails',async()=>{await seedInvite('ABCDEFGHJK',{redeemBy:Timestamp.fromMillis(Date.now()-1000)});await assertFails(redeem());});
test('5. Inactive code fails',async()=>{await seedInvite('ABCDEFGHJK',{active:false});await assertFails(redeem());});
test('6. Code already at maxUses fails',async()=>{await seedInvite('ABCDEFGHJK',{usedCount:3,maxUses:3});await assertFails(redeem());});
test('7. usedCount + 2 fails',async()=>{await seedInvite();const db=context('student1').firestore();const b=writeBatch(db);b.set(doc(db,'users/student1'),userData('student1'));b.set(doc(db,'invites/ABCDEFGHJK/redemptions/student1'),{uid:'student1',redeemedAt:serverTimestamp()});b.update(doc(db,'invites/ABCDEFGHJK'),{usedCount:2});await assertFails(b.commit());});
test('8. accessExpiresAt beyond accessDays fails',async()=>{await seedInvite('ABCDEFGHJK',{accessDays:1});await assertFails(redeem('student1','ABCDEFGHJK',{accessExpiresAt:future(3)}));});
test('9. Extra field on users doc fails',async()=>{await seedInvite();await assertFails(redeem('student1','ABCDEFGHJK',{extra:'not allowed'}));});
test('10a. Owner changing plan fails',async()=>{await seedUser();await assertFails(updateDoc(doc(context('student1').firestore(),'users/student1'),{plan:'paid'}));});
test('10b. Owner changing status fails',async()=>{await seedUser();await assertFails(updateDoc(doc(context('student1').firestore(),'users/student1'),{status:'suspended'}));});
test('10c. Owner changing accessExpiresAt fails',async()=>{await seedUser();await assertFails(updateDoc(doc(context('student1').firestore(),'users/student1'),{accessExpiresAt:future(200)}));});
test('11. Owner updating displayName succeeds',async()=>{await seedUser();await assertSucceeds(updateDoc(doc(context('student1').firestore(),'users/student1'),{displayName:'New Name'}));});
test('12. Another user reading my users doc fails',async()=>{await seedUser();await assertFails(getDoc(doc(context('student2').firestore(),'users/student1')));});
test('13a. Student who has already joined reading an invite fails',async()=>{await seedInvite();await seedUser();await assertFails(getDoc(doc(context('student1').firestore(),'invites/ABCDEFGHJK')));});
test('13c. Verified new user reading one invite by its code succeeds',async()=>{await seedInvite();await assertSucceeds(getDoc(doc(context('newuser').firestore(),'invites/ABCDEFGHJK')));});
test('13d. Unverified user reading an invite fails',async()=>{await seedInvite();await assertFails(getDoc(doc(context('newuser',{email_verified:false}).firestore(),'invites/ABCDEFGHJK')));});
test('13b. Student listing invites fails',async()=>{await seedInvite();await assertFails(getDocs(collection(context('student1').firestore(),'invites')));});
test('14a. Admin creating an invite succeeds',async()=>{await seedAdmin();const db=context('admin1').firestore();await assertSucceeds(setDoc(doc(db,'invites/BCDEFGHJK2'),inviteData({createdBy:'admin1'})));});
test('14b. Student creating an invite fails',async()=>{const db=context('student1').firestore();await assertFails(setDoc(doc(db,'invites/BCDEFGHJK2'),inviteData({createdBy:'student1'})));});
test('15. Any client writing to admins fails',async()=>{await assertFails(setDoc(doc(context('student1').firestore(),'admins/student1'),{role:'admin'}));});
test('16. ageConfirmed18 false fails',async()=>{await seedInvite();await assertFails(redeem('student1','ABCDEFGHJK',{consent:{version:'2026-10-v1',acceptedAt:serverTimestamp(),ageConfirmed18:false}}));});
test('17. Owner deleting own users doc outside the tombstone path fails',async()=>{await seedUser();await assertFails(deleteDoc(doc(context('student1').firestore(),'users/student1')));});
test('18. Same user redeeming a second time fails',async()=>{await seedInvite();await assertSucceeds(redeem());await assertFails(redeem());});
test('19a. Owner deleting own redemption doc succeeds',async()=>{await seedInvite();await seedRedemption();await assertSucceeds(deleteDoc(doc(context('student1').firestore(),'invites/ABCDEFGHJK/redemptions/student1')));});
test('19b. Another user deleting redemption fails',async()=>{await seedInvite();await seedRedemption();await assertFails(deleteDoc(doc(context('student2').firestore(),'invites/ABCDEFGHJK/redemptions/student1')));});
test('20. Any client lowering usedCount fails',async()=>{await seedInvite('ABCDEFGHJK',{usedCount:1});await assertFails(updateDoc(doc(context('student1').firestore(),'invites/ABCDEFGHJK'),{usedCount:0}));});
test('21. Owner writing tombstone with redemption deletion in same batch succeeds',async()=>{await seedUser();await seedRedemption();await assertSucceeds(tombstoneBatch());});
test('22. Tombstone with extra field fails',async()=>{await seedUser();await seedRedemption();await assertFails(tombstoneBatch('student1','ABCDEFGHJK',{displayName:'retained'}));});
test('23. Tombstone without deleting redemption in same batch fails',async()=>{await seedUser();await seedRedemption();await assertFails(setDoc(doc(context('student1').firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1}));});
test('24. UID whose users doc is a tombstone cannot redeem again',async()=>{await seedInvite();await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:Timestamp.now(),schemaVersion:1}));await assertFails(redeem());});
test('25a. Owner updating tombstone fails',async()=>{await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:Timestamp.now(),schemaVersion:1}));await assertFails(updateDoc(doc(context('student1').firestore(),'users/student1'),{status:'active'}));});
test('25b. Owner deleting tombstone fails',async()=>{await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:Timestamp.now(),schemaVersion:1}));await assertFails(deleteDoc(doc(context('student1').firestore(),'users/student1')));});
test('25c. Admin deleting tombstone succeeds',async()=>{await seedAdmin();await env.withSecurityRulesDisabled(async c=>setDoc(doc(c.firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:Timestamp.now(),schemaVersion:1}));await assertSucceeds(deleteDoc(doc(context('admin1').firestore(),'users/student1')));});
test('26. Fresh-session redemption with profileDetails creates the same user shape',async()=>{await seedInvite();const details={displayName:'Fresh Session Student',institution:'',course:'',consentVersion:'2026-10-v1',ageConfirmed18:true};const db=context('freshuid').firestore();const b=writeBatch(db);b.set(doc(db,'users/freshuid'),{displayName:details.displayName,email:'freshuid@example.test',institution:details.institution,course:details.course,plan:'free',status:'active',inviteCode:'ABCDEFGHJK',accessExpiresAt:future(100),consent:{version:details.consentVersion,acceptedAt:serverTimestamp(),ageConfirmed18:details.ageConfirmed18},createdAt:serverTimestamp(),schemaVersion:1});b.set(doc(db,'invites/ABCDEFGHJK/redemptions/freshuid'),{uid:'freshuid',redeemedAt:serverTimestamp()});b.update(doc(db,'invites/ABCDEFGHJK'),{usedCount:increment(1)});await assertSucceeds(b.commit());const s=await getDoc(doc(db,'users/freshuid'));assert.deepEqual(Object.keys(s.data()).sort(),['accessExpiresAt','consent','course','createdAt','displayName','email','institution','inviteCode','plan','schemaVersion','status'].sort());});

const past = days => Timestamp.fromMillis(Date.now()-days*86400000);
const erase = (uid='student1') => setDoc(doc(context('admin1').firestore(),`users/${uid}`),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1});
test('27a. Admin erasing an account expired more than 90 days ago succeeds',async()=>{await seedAdmin();await seedUser('student1','ABCDEFGHJK',{accessExpiresAt:past(91)});await assertSucceeds(erase());});
test('27b. Admin erasing an account expired only 89 days ago fails',async()=>{await seedAdmin();await seedUser('student1','ABCDEFGHJK',{accessExpiresAt:past(89)});await assertFails(erase());});
test('27c. Admin erasing an active account fails',async()=>{await seedAdmin();await seedUser();await assertFails(erase());});
test('27d. Admin erasure that keeps a personal field fails',async()=>{await seedAdmin();await seedUser('student1','ABCDEFGHJK',{accessExpiresAt:past(120)});await assertFails(setDoc(doc(context('admin1').firestore(),'users/student1'),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1,email:'student1@example.test'}));});
test('27e. A student erasing another expired account fails',async()=>{await seedUser('student2','ABCDEFGHJK',{accessExpiresAt:past(120)});await assertFails(setDoc(doc(context('student1').firestore(),'users/student2'),{status:'deleting',deletionRequestedAt:serverTimestamp(),schemaVersion:1}));});
test('27f. Erased account cannot redeem again',async()=>{await seedAdmin();await seedInvite();await seedUser('student1','ABCDEFGHJK',{accessExpiresAt:past(120)});await assertSucceeds(erase());await assertFails(redeem());});
