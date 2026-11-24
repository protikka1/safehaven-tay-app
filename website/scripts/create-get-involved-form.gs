/**
 * SafeHaven TAY — Get Involved form setup.
 * Run ONCE using Apps Script while signed in as admin@eporth.org.
 * Creates a separate Google Form and linked response spreadsheet.
 * Never publish the response spreadsheet or participant contact details.
 */
function createSafeHavenGetInvolved() {
  const form = FormApp.create("SafeHaven TAY — Get Involved");
  form.setDescription("Help build SafeHaven TAY. Please do not submit medical, housing-intake, government ID, or other sensitive information. This form is for volunteers and organizational partnerships only.");
  form.setConfirmationMessage("Thank you for your interest. Our organizing team will review your message and contact you using your preferred method.");
  form.setCollectEmail(false);
  form.addTextItem().setTitle("Preferred name").setRequired(true);
  form.addTextItem().setTitle("Email address (optional)").setRequired(false);
  form.addTextItem().setTitle("Phone number (optional)").setRequired(false);
  form.addMultipleChoiceItem().setTitle("Preferred way to contact you").setChoiceValues(["Email","Phone","Either"]).setRequired(true);
  form.addCheckboxItem().setTitle("How would you like to participate?").setChoiceValues([
    "Advisory Team — community guidance and ethics",
    "Development Team — website, code, testing, data",
    "Action Team — outreach, meetings, community events",
    "Organizational partnership",
    "Donations or fundraising discussion"
  ]).setRequired(true);
  form.addParagraphTextItem().setTitle("Skills, experience, or ideas (optional)").setRequired(false);
  form.addMultipleChoiceItem().setTitle("Availability").setChoiceValues(["Weekdays","Weekends","Evenings","Flexible","Not sure yet"]).setRequired(false);
  form.addMultipleChoiceItem().setTitle("I agree to be contacted about SafeHaven TAY using the contact information I provided.").setChoiceValues(["Yes","No"]).setRequired(true);
  const sheet = SpreadsheetApp.create("SafeHaven TAY — Get Involved (Private Responses)");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  const tracking = sheet.insertSheet("Organizer Follow-Up");
  tracking.getRange(1,1,1,9).setValues([["Received date","Preferred name / reference","Team","Assigned organizer","Status","Follow-up date","Contact preference","Notes (non-sensitive)","Source response row"]]);
  tracking.getRange("E2:E500").setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(["New","Review","Contacted","Orientation invited","Assigned","Closed"],true).build());
  tracking.setFrozenRows(1);
  tracking.autoResizeColumns(1,9);
  console.log("Form to share: "+form.getPublishedUrl());
  console.log("Organizer edit form: "+form.getEditUrl());
  console.log("Private response sheet: "+sheet.getUrl());
  console.log("Move the form and private sheet into the restricted Get Involved folder using Drive; check sharing before publishing.");
}
