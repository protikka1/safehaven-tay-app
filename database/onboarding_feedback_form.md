# 📋 IX1 Sentinel & SafeHaven: Developer Onboarding Feedback Survey
**Document ID**: `docs/onboarding_feedback_form.md`  
**Status**: Ready for Google Forms Deployment  
**Target Audience**: Developer Advocates & Community Contributors  

This document outlines the complete structure, question logic, and implementation guide for the **Onboarding Feedback Survey**. Collecting structured feedback from your developer advocates ensures that installation bottlenecks on macOS and mobile Termux are identified and patched immediately.

---

## 🗺️ Part 1: Survey Architecture & Questions

This survey is designed to be built in **Google Forms** and linked directly to your **Advocate Registry Spreadsheet**.

### Section 1: Contributor Metadata (Linked Fields)
These fields are used to map feedback to the original registration database.

1. **GitHub Username** (Short Answer)  
   * *Description*: "Please provide your GitHub/GitLab handle."  
   * *Validation*: Text matches pattern `^[a-zA-Z0-9](-?[a-zA-Z0-9]){0,38}$` (Standard Git username validation).  
   * *Required*: Yes.  

2. **Onboarding Date** (Date Picker)  
   * *Description*: "When did you execute the onboarding workflow?"  
   * *Required*: Yes.  

---

### Section 2: Environment & Setup Evaluation
Helps identify which environments are experiencing the most friction.

3. **What is your local development operating system?** (Multiple Choice)  
   * [ ] **macOS** (Apple Silicon - M1/M2/M3)  
   * [ ] **macOS** (Intel Core)  
   * [ ] **Android (Termux Mobile Sandbox)**  
   * [ ] **Linux** (Debian/Ubuntu/Fedora)  
   * [ ] **Other** (Specify)  
   * *Required*: Yes.  

4. **Which Technical Track did you choose to configure?** (Checkboxes - Select all that apply)  
   * [ ] **Track A: GIS Zoning Audit Engine** (API Monitor, alerts, spatial visualizer)  
   * [ ] **Track B: SRO 1:1 Replacement Ledger** (SQLite3, schema seeds, relational ledger)  
   * [ ] **Track C: Prosocial Civic Trust Portal** (NLP re-write, moderation, Streamlit frontend)  
   * [ ] **Full Suite Simulation** (`run_all_simulations.sh` orchestrator)  
   * *Required*: Yes.  

5. **Rate the clarity of the onboarding documentation (SECURITY.md, CONTRIBUTING.md, and macOS/Termux Setup scripts):** (Linear Scale)  
   * *Scale*: `1` (Extremely Confusing / Incomplete) to `5` (Extremely Clear / Seamless).  
   * *Required*: Yes.  

---

### Section 3: Installation Friction & Bug Tracking
Pins down compile-time and run-time issues.

6. **Did you encounter any compilation or environment errors during setup?** (Multiple Choice)  
   * [ ] **No, everything compiled and ran successfully on the first try!**  
   * [ ] **Yes, I ran into dependency/pip installation errors** (e.g., NumPy, Pandas, Geopandas, Shapely)  
   * [ ] **Yes, I had database issues** (e.g., SQLite3 schema missing, seed script failures)  
   * [ ] **Yes, I had path or script execution permissions issues** (e.g., Permission Denied for `run_all_simulations.sh`)  
   * [ ] **Other** (Specify)  
   * *Required*: Yes.  

7. **How long did it take you to get a green status on the local test suite?** (Multiple Choice)  
   * [ ] Under 5 minutes  
   * [ ] 5 to 15 minutes  
   * [ ] 15 to 30 minutes  
   * [ ] More than 30 minutes  
   * [ ] I was unable to get a green status / the test suite failed  
   * *Required*: Yes.  

8. **Describe any specific errors or friction points you experienced:** (Paragraph Long Answer)  
   * *Description*: "If you encountered errors, please paste the terminal trace or describe what was confusing. Your feedback directly helps us patch our bootstrap scripts!"  
   * *Required*: No (Conditional on answering 'Yes' to Question 6).  

---

### Section 4: Prosocial Engagement & Civic Alignment
Evaluates how well the onboarding process communicates the human-led mission of the project.

9. **Do you feel the onboarding materials effectively communicated our ethical guardrails (e.g., protecting unhoused PII, avoiding automated caseworker replacement, and mitigating the Sense of Misinformation)?** (Multiple Choice)  
   * [ ] Yes, the connection between the code and civic ethics was very clear.  
   * [ ] Somewhat, I understand the rules but want more context on how they apply to my commits.  
   * [ ] No, the technical setup overshadowed the ethical principles.  
   * *Required*: Yes.  

10. **Would you be willing to mentor or peer-onboard incoming developer advocates?** (Multiple Choice)  
    * [ ] Yes, add me to the peer-support roster!  
    * [ ] No, but I will stay active in the GitHub Discussions and Issue boards.  
    * [ ] Not at this time.  
    * *Required*: Yes.  

---

## 🔗 Part 2: Google Apps Script Automatic Integration

To tie this feedback form directly into your automated advocacy pipeline, you can add this Apps Script function to your existing `Code.gs` script. It automatically triggers whenever a developer submits this feedback form, flags setups that encountered errors, and alerts you via email so you can assist them.

```javascript
/**
 * Triggers automatically when a developer submits the Onboarding Feedback Survey.
 * It parses the feedback, logs it to a separate 'Feedback' tab in your Sheet,
 * and alerts the admin if a developer is blocked by setup errors.
 */
function handleFeedbackFormSubmit(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Feedback Logs");
    if (!sheet) {
      // Create the sheet if it doesn't exist
      sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("Feedback Logs");
      sheet.appendRow([
        "Timestamp", "GitHub Username", "Onboarding Date", "Operating System", 
        "Track Selected", "Documentation Clarity Rating", "Setup Errors", 
        "Setup Duration", "Error Details", "Ethical Alignment", "Mentor Volunteer"
      ]);
      sheet.getRange(1, 1, 1, 11).setFontWeight("bold").setBackground("#e6f2ff");
    }

    // Extract submission data
    var responses = e.values; // Array of values in order of the Form questions
    var timestamp = responses[0];
    var gitUsername = responses[1];
    var onboardingDate = responses[2];
    var os = responses[3];
    var track = responses[4];
    var clarityRating = responses[5];
    var setupErrors = responses[6];
    var duration = responses[7];
    var errorDetails = responses[8];
    var ethicalAlignment = responses[9];
    var mentorVolunteer = responses[10];

    // Append to sheet
    sheet.appendRow([
      timestamp, gitUsername, onboardingDate, os, track, 
      clarityRating, setupErrors, duration, errorDetails, 
      ethicalAlignment, mentorVolunteer
    ]);

    // Check if the developer is blocked by errors
    if (setupErrors !== "No, everything compiled and ran successfully on the first try!") {
      sendDeveloperBlockAlert(gitUsername, os, track, errorDetails);
    }
    
  } catch (error) {
    Logger.log("Error in handleFeedbackFormSubmit: " + error.toString());
  }
}

/**
 * Sends an email alert to the core management team when a developer is blocked.
 */
function sendDeveloperBlockAlert(username, os, track, errorDetails) {
  var adminEmail = "admin@safehaven-recovery.org"; // Replace with your admin email
  var subject = "⚠️ [DEVELOPER BLOCKED] Setup Failure Reported by @" + username;
  
  var htmlBody = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; border: 1px solid #ffccd5; border-radius: 8px; padding: 20px; background-color: #fffafb;">
      <h2 style="color: #d9534f; margin-top: 0;">🔧 Developer Setup Alert</h2>
      <p>An onboarding developer has reported installation or compilation barriers on their local machine.</p>
      
      <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; width: 30%;">GitHub Handle:</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee; color: #0066cc;">@${username}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Operating System:</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee;">${os}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Selected Track:</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee;">${track}</td>
        </tr>
      </table>
      
      <div style="background-color: #f7f7f7; border-left: 4px solid #d9534f; padding: 12px; margin: 15px 0; font-family: monospace; font-size: 13px; white-space: pre-wrap;">
        <strong>Reported Error Details:</strong><br><br>${errorDetails || "No terminal error pasted. See survey logs for manual review."}
      </div>
      
      <p style="font-size: 14px; margin-top: 20px;">
        <strong>Action Required:</strong> Reach out to this developer on GitHub to troubleshoot, or check if the latest macOS/Termux bootstrap scripts need to be updated in the main repository.
      </p>
      
      <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
      <p style="font-size: 11px; color: #777; text-align: center;">IX1 Sentinel Automated Developer Registry System &bull; SafeHaven TAY Platform</p>
    </div>
  `;

  MailApp.sendEmail({
    to: adminEmail,
    subject: subject,
    htmlBody: htmlBody
  });
}
```

---

## 🛠️ Step-by-Step Deployment Guide

Follow these steps to deploy and activate the survey workflow in under 3 minutes:

### Step 1: Create the Google Form
1. Go to [Google Forms](https://forms.google.com) and click **Blank Form**.
2. Title the form: `"IX1 Sentinel: Developer Onboarding Feedback Survey"`.
3. Add the **10 questions** exactly as structured in **Part 1** of this guide.

### Step 2: Link to Your Master Spreadsheet
1. Inside the Google Form, click on the **Responses** tab at the top.
2. Click **Link to Sheets** (the green spreadsheet icon).
3. Select **"Select existing spreadsheet"** and choose your active **Advocate Registry Spreadsheet**. This adds a new tab to your spreadsheet specifically for the feedback responses.

### Step 3: Insert the Apps Script Code
1. Open your master **Advocate Registry Spreadsheet**.
2. Click **Extensions** in the top menu, then select **Apps Script**.
3. Copy the script from **Part 2** above and paste it at the bottom of your existing `Code.gs` script.
4. Replace `admin@safehaven-recovery.org` with your actual email address.
5. Click **Save** (the floppy disk icon).

### Step 4: Configure the Form Submission Trigger
1. In the Apps Script sidebar on the left, click **Triggers** (the clock icon ⏰).
2. Click **+ Add Trigger** in the bottom-right corner.
3. Configure the dropdowns exactly as follows:
   * **Choose which function to run**: `handleFeedbackFormSubmit`
   * **Choose which deployment should run**: `Head`
   * **Select event source**: `From spreadsheet`
   * **Select event type**: `On form submit`
4. Click **Save**. Google will prompt you to authorize permissions—allow them so the script can log responses and send emails securely.

---

*This document has been archived in the repository index under `docs/onboarding_feedback_form.md` for permanent reference.*
