/**
 * SafeHaven TAY — public community feedback survey.
 * Run createSafeHavenCommunityForm() once at https://script.google.com
 * using admin@eporth.org. The script creates a Form and a separate
 * private responses spreadsheet owned by the executing Google account.
 * It deliberately does NOT collect medical, youth intake, or case records.
 */
function createSafeHavenCommunityForm() {
  const props = PropertiesService.getScriptProperties();
  const existing = props.getProperty('SAFEHAVEN_FORM_ID');
  if (existing) {
    const saved = FormApp.openById(existing);
    Logger.log('Existing responder URL: ' + saved.getPublishedUrl());
    Logger.log('Existing edit URL: ' + saved.getEditUrl());
    Logger.log('Responses spreadsheet ID: ' + props.getProperty('SAFEHAVEN_RESPONSE_SHEET_ID'));
    return;
  }

  const form = FormApp.create('SafeHaven TAY — Community Feedback | November 24, 2026');
  form.setDescription(
    'Voluntary community feedback on SafeHaven TAY planning. Do not enter youth intake data, ' +
    'medical information, or identifying information about another person.'
  );
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('Thank you for helping shape SafeHaven TAY. Your feedback will inform community planning.');

  form.addCheckboxItem()
    .setTitle('Which areas should SafeHaven TAY prioritize? Select up to two.')
    .setChoiceValues([
      'Low-barrier intake and human support',
      'Housing navigation',
      'Health and recovery coordination',
      'Privacy and safeguarding',
      'Community oversight and accountability'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('How useful is the proposed approach?')
    .setChoiceValues(['Very useful', 'Somewhat useful', 'Not sure', 'Not useful'])
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('What is the biggest barrier facing transition-age youth locally?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('What should SafeHaven change or improve before a pilot?')
    .setRequired(false);

  form.addCheckboxItem()
    .setTitle('Would you like to participate? (Optional)')
    .setChoiceValues(['Advisory Team', 'Development Team', 'Action Team', 'Organizational partnership', 'Feedback only'])
    .setRequired(false);

  form.addTextItem()
    .setTitle('Name or alias, and preferred contact method (optional)')
    .setHelpText('Only if you would like a reply. Do not provide information about youth or clients.')
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('May the SafeHaven organizing team contact you?')
    .setChoiceValues(['Yes', 'No'])
    .setRequired(true);

  const ss = SpreadsheetApp.create('SafeHaven TAY — Community Survey Responses — 2026-11-24 (Private)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // Form settings and publication availability can vary by Workspace policy.
  // Do not claim the form is public until tested in an incognito browser.
  if (typeof form.setPublished === 'function') {
    form.setPublished(true);
  }
  form.setAcceptingResponses(true);

  props.setProperty('SAFEHAVEN_FORM_ID', form.getId());
  props.setProperty('SAFEHAVEN_RESPONSE_SHEET_ID', ss.getId());

  Logger.log('Responder URL: ' + form.getPublishedUrl());
  Logger.log('Form edit URL: ' + form.getEditUrl());
  Logger.log('Private response spreadsheet: ' + ss.getUrl());
  Logger.log('Copy the RESPONDER URL into the SafeHaven presentation page; never publish the spreadsheet URL.');
}
