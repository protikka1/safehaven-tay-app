# TAY Recovery Mobile App: Interactive User Interface Design & User Flows

This document details the user interface (UI) architecture, wireframe layouts, and interactive user flows for the mobile application designed to connect unhoused **Transition-Age Youth (TAY) aged 18–24** in Skid Row to Medications for Addiction Treatment (MAT), detox beds, and supportive services with zero administrative "hassle."

---

## 1. App Design Philosophy: Eliminating the "Hassle"

Vulnerable, unhoused youth face severe psychological, emotional, and cognitive barriers when attempting to seek help. Traditional systems require physical visits, long wait times, and extensive, intimidating paperwork. 

The **TAY Recovery App** is designed around three non-negotiable principles:
1. **Anonymity and Trust First**: Registration requires only a street alias and a SafeLink phone number. No government ID, Social Security Number, or legal names are requested during initial touchpoints.
2. **One-Tap Capacity Triage**: Real-time bed availability is visualized on a simplified map. A single tap reserves a bed and pre-authorizes a MAT consultation.
3. **No Dead Ends**: If a facility is full, the app dynamically routes the youth to the nearest partner site with open beds (e.g., from the fully occupied Midnight Mission to the Substance Use Health Hub).

---

## 2. Interactive App Screen Wireframes

### Screen 1: The Landing Portal (Low-Barrier Registration)
Designed to be clean, non-intimidating, and highly encouraging.

```text
+-------------------------------------------------+
|  [Logo: SafeHaven]                  9:41 AM     |
|                                                 |
|  Welcome to SafeHaven.                          |
|  A safe space to heal, completely on your terms.|
|                                                 |
|  What should we call you?                       |
|  [ Street Alias (e.g., Sky)                 ]   |
|                                                 |
|  What is your date of birth?                    |
|  [ MM / DD / YYYY                           ]   |
|  *Used only to match you with youth-specific services  |
|                                                 |
|  Your SafeLink Phone Number:                    |
|  [ (213) 555 - XXXX                         ]   |
|                                                 |
|  +-------------------------------------------+  |
|  |           ENTER SAFEHAVEN                 |  |
|  +-------------------------------------------+  |
|                                                 |
|  By continuing, you remain completely anonymous |
|  and no data is shared with law enforcement.     |
+-------------------------------------------------+
```

---

### Screen 2: Real-Time Services Dashboard (Ecosystem Map)
This screen is populated dynamically by querying our `facilities` table (e.g., `database/query_services.py`).

```text
+-------------------------------------------------+
|  Hello, Sky.                        9:41 AM     |
|  Your Care Advocate: Marcus Henderson (Peer)    |
|                                                 |
|  [ Search Map for Open Services            [Q] ]|
|                                                 |
|  --- AVAILABLE NEAR YOU RIGHT NOW -----------   |
|                                                 |
|  +-------------------------------------------+  |
|  |  Skid Row Substance Use Health Hub        |  |
|  |  * 7 Detox Beds Available                 |  |
|  |  * On-site MAT (Buprenorphine, Methadone) |  |
|  |  * Distance: 0.2 miles away               |  |
|  |                                           |  |
|  |  [ TAP TO CLAIM BED & MAT SCRIPT ]        |  |
|  +-------------------------------------------+  |
|                                                 |
|  +-------------------------------------------+  |
|  |  Hilda L. Solis Care First Village        |  |
|  |  * 15 Beds Available                      |  |
|  |  * Distance: 0.8 miles away               |  |
|  |  [ View Details ]                         |  |
|  +-------------------------------------------+  |
|                                                 |
|  +-------------------------------------------+  |
|  |  Weingart Tower PSH (Seniors/Veterans)    |  |
|  |  * 2 Housing Units Available              |  |
|  |  [ Locked - Referral Required ]           |  |
|  +-------------------------------------------+  |
|                                                 |
|  [Home]      [Inbox]      [My Pass]     [Help]  |
+-------------------------------------------------+
```

---

### Screen 3: "One-Click" Booking & Warm Hand-Off
Appears when Sky taps "Claim Bed & MAT Script" on Screen 2. It performs an atomic backend transaction to reserve the bed.

```text
+-------------------------------------------------+
|  < Back                             9:41 AM     |
|  CONFIRM YOUR BOOKING                           |
|                                                 |
|  You are booking a space at:                    |
|  **Skid Row Substance Use Health Hub**          |
|  600 San Pedro St, Los Angeles, CA 90013        |
|                                                 |
|  WHAT YOU GET ON ARRIVAL:                       |
|  * A guaranteed, clean detox bed for tonight.   |
|  * Warm meal, shower, and clean clothing.       |
|  * Immediate consultation for MAT treatment.    |
|                                                 |
|  WHO WILL MEET YOU:                             |
|  Marcus Henderson (Peer Support Specialist)     |
|  "Hey Sky, I've got your bed locked in. Just    |
|   show up and ask for me. We got you."          |
|                                                 |
|  +-------------------------------------------+  |
|  |       LOCK IN MY CHECK-IN PASS            |  |
|  +-------------------------------------------+  |
|                                                 |
|  *This will temporarily decrease the hub's bed  |
|   count by 1 to hold your spot for 3 hours.     |
+-------------------------------------------------+
```

---

### Screen 4: Your Digital Check-In Pass
Sky's golden ticket to bypass the front-desk intake hassle. The QR code contains the secure, UUID-based placement token.

```text
+-------------------------------------------------+
|  SafeHaven Pass                     9:41 AM     |
|  HOLDING SPOT FOR: SKY                          |
|                                                 |
|  +-------------------------------------------+  |
|  |                                           |  |
|  |                 [ QR ]                    |  |
|  |                [ CODE ]                   |  |
|  |                                           |  |
|  +-------------------------------------------+  |
|  Show this to the front desk or scan at portal  |
|                                                 |
|  PASS DETAILS:                                  |
|  * Destination: Skid Row Substance Use Hub     |
|  * Reserved Bed: Bed #12 (Detox Section)        |
|  * Assessor Assigned: Marcus Henderson          |
|  * Telehealth Doctor: Dr. Karen Gill, M.D.      |
|  * Pre-Authorized: Buprenorphine Treatment     |
|                                                 |
|  DIRECTIONS:                                    |
|  Walk 3 blocks South down San Pedro St.         |
|                                                 |
|  [ Call Marcus ]            [ Cancel Booking ]  |
+-------------------------------------------------+
```

---

## 3. Interactive User Flow & Backend API Mapping

```
YOUTH ACTIONS                             BACKEND TRANSATIONS
================================================================================
1. Opens App, enters alias "Sky"  ---->  POST /api/v1/profiles
   and Date of Birth                     Creates record in `youth_profiles`
                                         Returns secure JWT.

2. Views dashboard, sees "7 beds" ---->  GET /api/v1/facilities/beds
   open at Health Hub                    Queries `facilities` table.
                                         Dynamically filters by capacity > 0.

3. Taps "Lock In My Pass"          ---->  POST /api/v1/intake/quick-booking
                                         Wraps 4 steps in an atomic SQL Transaction:
                                         a) Decrements `available_beds` by 1.
                                         b) Inserts record into `program_placements`.
                                         c) Maps caseworker to `care_assignments`.
                                         d) Pre-allocates record in `mat_prescriptions`.

4. Arrives at facility, scans QR   ---->  PUT /api/v1/placements/confirm
                                         Updates `program_placements` status to 'Enrolled'.
                                         Triggers SMS alert to Care Team.
                                         Launches clinician screen for MAT dispensing.
```

---

## 4. Addressing the Mobile "GPS Tracker" & Harm Reduction Edge Cases

To ensure the safety of youth and maintain operational integrity, the mobile client implements several unique client-side features:
*   **Geofenced Comfort Zones**: Using GPS data, the app alerts the user when they are nearing the boundaries of the historic "Containment Zone" (e.g., crossing West over Main Street), notifying them of localized legal differences regarding sidewalk sleeping and property searches established under *Jones v. City of Los Angeles*.
*   **Preventative Drop-In Routing**: If a youth's GPS trace or activity log remains static inside an active SRO building with documented code violations (like the *Renato Apartments*), the system pushes a proactive "Care Check-In" prompt to the youth and alerts their Peer Support Specialist to perform a physical welfare check.
