/**
 * SafeHaven TAY — organizer follow-up automation.
 * Paste into Apps Script opened from the existing private response spreadsheet:
 * Extensions > Apps Script. Run setupFollowupWorkflow() once as admin@eporth.org.
 *
 * No automatic emails are sent to applicants.
 * Only a daily organizer-only reminder is sent to admin@eporth.org.
 */
const SH = {
  RESPONSES: 'Form Responses 1',
  TRACKING: 'Organizer Follow-Up',
  ADMIN: 'admin@eporth.org',
  STATUS: ['New', 'Needs contact info', 'Do not contact', 'Review', 'Contacted', 'Orientation invited', 'Assigned', 'Closed'],
  TEAMS: ['Advisory Team','Development Team','Action Team','Organizational partnership','Donations or fundraising discussion']
};

function setupFollowupWorkflow() {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  const source = book.getSheetByName(SH.RESPONSES);
  const track = book.getSheetByName(SH.TRACKING);
  if (!source || !track) throw new Error('Expected response or tracking tab not found.');
  track.getRange(1,1,1,9).setValues([['Received date','Preferred name / reference','Team','Assigned organizer','Status','Follow-up date','Contact preference','Notes (non-sensitive)','Source response row']]);
  track.getRange('E2:E1000').setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(SH.STATUS,true).setAllowInvalid(false).build());
  track.getRange('C2:C1000').setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(SH.TEAMS,true).setAllowInvalid(true).build());
  track.setFrozenRows(1);
  track.getRange('F2:F1000').setNumberFormat('yyyy-mm-dd');
  track.getRange('A2:A1000').setNumberFormat('yyyy-mm-dd hh:mm');
  track.getRange('A1:I1').setFontWeight('bold').setBackground('#dcefe8');
  track.setColumnWidths(1,1,160);track.setColumnWidths(2,1,190);
  track.setColumnWidths(3,1,220);track.setColumnWidths(4,1,170);
  track.setColumnWidths(5,1,180);track.setColumnWidths(6,1,145);
  track.setColumnWidths(7,1,170);track.setColumnWidths(8,1,300);
  track.setColumnWidths(9,1,160);
  const rules = track.getConditionalFormatRules().filter(r => !r.getRanges().some(range => range.getA1Notation() === 'A2:I1000'));
  rules.push(SpreadsheetApp.newConditionalFormatRule()
     .whenFormulaSatisfied('=AND($F2<TODAY(),$F2<>"",$E2<>"Closed",$E2<>"Assigned",$E2<>"Do not contact")')
     .setBackground('#fff0dc').setRanges([track.getRange('A2:I1000')]).build());
  track.setConditionalFormatRules(rules);
  const all = ScriptApp.getProjectTriggers();
  all.filter(t => ['onSafeHavenSubmit','sendSafeHavenDailyDigest'].includes(t.getHandlerFunction()))
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('onSafeHavenSubmit').forSpreadsheet(book).onFormSubmit().create();
  ScriptApp.newTrigger('sendSafeHavenDailyDigest').timeBased().everyDays(1).atHour(9).create();
  syncExistingResponses();
  console.log('Installed new-submission trigger and daily 9 AM digest. Verify Apps Script project time zone.');
}
function onSafeHavenSubmit(e) {
  if (!e || !e.range) return;
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try { appendResponseRow_(e.range.getSheet(),e.range.getRow()); }
  finally { lock.releaseLock(); }
}
function syncExistingResponses() {
  const source = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SH.RESPONSES);
  for(let r=2;r<=source.getLastRow();r++) appendResponseRow_(source,r);
}
function appendResponseRow_(source,rowNumber) {
  if(source.getName()!==SH.RESPONSES || rowNumber<2) return;
  const tracking = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SH.TRACKING);
  const last=tracking.getLastRow();
  const known= last>=2 ? tracking.getRange(2,9,last-1,1).getValues().flat().map(String) : [];
  if(known.includes(String(rowNumber)))return; // idempotent for source-row reconciliation
  const header=source.getRange(1,1,1,source.getLastColumn()).getDisplayValues()[0];
  const values=source.getRange(rowNumber,1,1,header.length).getValues()[0];
  const find=(name)=>values[header.indexOf(name)]||'';
  const name=String(find('Preferred name')).trim() || 'Response #'+rowNumber;
  const interests=String(find('How would you like to participate?'));
  const team=SH.TEAMS.find(t=>interests.includes(t))||'Review';
  const consent=String(find('I agree to be contacted about SafeHaven TAY using the contact information I provided.')).trim().toLowerCase()==='yes';
  const email=String(find('Email address (optional)')||find('Email Address')).trim();
  const phone=String(find('Phone number (optional)')).trim();
  const preference=String(find('Preferred way to contact you')).trim();
  const contactable=Boolean(email||phone);
  const status=!consent?'Do not contact':!contactable?'Needs contact info':'New';
  const stamp=values[0]||new Date();
  const due=(consent&&contactable)?new Date(new Date(stamp).getTime()+2*86400000):'';
  tracking.appendRow([stamp,name,team,'',status,due,preference,'',rowNumber]);
}
function sendSafeHavenDailyDigest() {
  const track=SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SH.TRACKING);
  if(track.getLastRow()<2)return;
  const now=new Date();
  const rows=track.getRange(2,1,track.getLastRow()-1,9).getValues();
  const active=rows.map((r,i)=>({r,index:i+2})).filter(x=>x.r[5] instanceof Date && x.r[5] <=now && !['Closed','Assigned','Do not contact'].includes(String(x.r[4])));
  if(!active.length)return;
  const lines=active.map(x=>'Row '+x.index+' | '+x.r[4]+' | '+x.r[2]+' | Assigned: '+(x.r[3]||'Unassigned'));
  const url=SpreadsheetApp.getActiveSpreadsheet().getUrl();
  MailApp.sendEmail({to:SH.ADMIN,subject:'SafeHaven TAY — '+active.length+' follow-up(s) due',
     body:'Follow-up tasks due or overdue:\n\n'+lines.join('\n')+'\n\nOpen restricted tracking sheet: '+url+'\n\nNo participant contact details are included in this email.'});
}
