"""Builds CBIO_Home_Visit_Register_User_Manual.pdf from the screenshots in docs/shots.
Run: python3 make_manual.py <folder with PNG screenshots> [output.pdf]"""
import sys, os, io
from PIL import Image as PI, ImageChops
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem

SRC = sys.argv[1] if len(sys.argv) > 1 else "shots"
OUT = sys.argv[2] if len(sys.argv) > 2 else "CBIO_Home_Visit_Register_User_Manual.pdf"
HERE = os.path.dirname(os.path.abspath(__file__)); JPG = os.path.join(HERE, "shots"); os.makedirs(JPG, exist_ok=True)
VER, DATE = "0.7.3", "14 November 2026"
URL = "https://tdavismph.github.io/cbio-home-visit-register/"
INK, MUTED, LINE, BAND, ACC = colors.HexColor("#16302b"), colors.HexColor("#5b6b68"), colors.HexColor("#c9d3d1"), colors.HexColor("#e6eeec"), colors.HexColor("#1f66a8")
st = lambda n, **k: ParagraphStyle(n, fontName=k.pop("font", "Helvetica"), textColor=k.pop("color", INK), **k)
T0 = st("t0", font="Helvetica-Bold", fontSize=24, leading=29, spaceAfter=6)
T1 = st("t1", fontSize=12, leading=16, color=MUTED, spaceAfter=14)
H1 = st("h1", font="Helvetica-Bold", fontSize=15, leading=19, spaceBefore=6, spaceAfter=6, keepWithNext=1)
H2 = st("h2", font="Helvetica-Bold", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=4, keepWithNext=1)
P = st("p", fontSize=9.6, leading=13.4, spaceAfter=6)
LI = st("li", fontSize=9.6, leading=13.2)
CAP = st("cap", fontSize=8.2, leading=10.5, color=MUTED, spaceBefore=3, spaceAfter=10)
C = st("c", fontSize=8.6, leading=11.2)
TH = st("th", font="Helvetica-Bold", fontSize=8.2, leading=10.5)
NOTE = st("note", fontSize=9.2, leading=12.6, backColor=BAND, borderPadding=7, spaceBefore=6, spaceAfter=12, leftIndent=7, rightIndent=7)
TOC = st("toc", fontSize=10, leading=15)
FIG = [0]

def jpg(name, crop=None):
    """crop = (top, bottom) in CSS pixels of the 820-wide screen; blank space at the bottom is trimmed."""
    im = PI.open(os.path.join(SRC, name + ".png")).convert("RGB"); k = im.width / 820.0
    if crop: im = im.crop((0, int(crop[0] * k), im.width, min(im.height, int(crop[1] * k))))
    bg = PI.new("RGB", im.size, im.getpixel((3, im.height - 3))); box = ImageChops.difference(im, bg).getbbox()
    if box and box[3] < im.height - 30: im = im.crop((0, 0, im.width, box[3] + 24))
    path = os.path.join(JPG, name + ("_%d_%d" % crop if crop else "") + ".jpg"); im.save(path, quality=86); return path, im.size

def img(name, crop, w, maxh):
    path, (pw, ph) = jpg(name, crop); h = w * ph / pw
    if h > maxh: w, h = w * maxh / h, maxh
    i = Image(path, width=w, height=h); return i

def fig(caption, *items, w=None, maxh=150 * mm):
    """items: (name, crop) pairs placed side by side."""
    FIG[0] += 1; n = len(items); W = (w or (165 * mm if n > 1 else 120 * mm)); each = (W - (n - 1) * 5 * mm) / n
    cells = [img(nm, cr, each, maxh) for nm, cr in items]
    t = Table([cells], colWidths=[each + (5 * mm if i < n - 1 else 0) for i in range(n)],
              style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]
                               + [("BOX", (i, 0), (i, 0), 0.5, LINE) for i in range(0)]))
    t.hAlign = "LEFT"
    return KeepTogether([t, Paragraph("<b>Figure %d.</b> %s" % (FIG[0], caption), CAP)])

def steps(*xs): return ListFlowable([ListItem(Paragraph(x, LI), leftIndent=16, spaceAfter=3) for x in xs], bulletType="1", bulletFontName="Helvetica-Bold", bulletFontSize=9.6, leftIndent=16)
def bullets(*xs): return ListFlowable([ListItem(Paragraph(x, LI), leftIndent=14, spaceAfter=2.5) for x in xs], bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9)
def table(head, rows, widths):
    data = [[Paragraph(h, TH) for h in head]] + [[Paragraph(x, C) for x in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    t.hAlign = "LEFT"; return t
def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(MUTED)
    c.drawString(d.leftMargin, 9 * mm, "CBIO+ Home Visit Register | User manual | Version %s, %s" % (VER, DATE)); c.drawRightString(A4[0] - d.rightMargin, 9 * mm, "Page %d" % d.page); c.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=17 * mm, title="CBIO+ Home Visit Register: User Manual", author="Impact Global Health Alliance")
W = doc.width; S = []; A = S.append

# ------------------------------------------------------------------ cover and contents
A(Spacer(1, 30 * mm)); A(Paragraph("CBIO+ Home Visit Register", T0)); A(Paragraph("User manual for Care Group Volunteers, Community Health Workers and the Administrator", T1))
A(Paragraph("Version %s (pilot build) · %s · Kenya configuration" % (VER, DATE), P)); A(Spacer(1, 8 * mm))
A(Paragraph("<b>Status of this build.</b> Use test data only. Records of real families should not be entered until three matters are settled: where the database is hosted (it is currently in Frankfurt, "
            "which Kenyan data protection rules treat as a transfer of personal data out of the country), the Kenyan data protection requirements for the project, and an independent security review. "
            "All names in the screenshots come from the built-in example data and do not refer to real people.", NOTE))
A(Paragraph("Contents", H2))
for x in ["1. What the system does", "2. Getting started: installing, signing in, working offline", "3. Care Group Volunteer: step by step", "4. Community Health Worker: step by step",
          "5. Administrator: step by step", "6. What the reports can tell you", "7. Problems and their solutions", "8. Several partners and countries", "9. QIVC: observing the quality of work", "Annex A. Visit schedule", "Annex B. How the due list is ordered"]: A(Paragraph(x, TOC))
A(PageBreak())

# ------------------------------------------------------------------ 1
A(Paragraph("1. What the system does", H1))
A(Paragraph("The CBIO+ Home Visit Register is an app for low-cost Android tablets. It keeps a register of households that have a pregnant woman or a child under 24 months, tells each worker which "
            "home visits are due, guides her through the questions for each visit, and turns the answers into coverage, mortality and lives-saved figures for the programme. "
            "CBIO+ combines the census-based, impact-oriented approach (every household is registered and visited routinely) with Care Groups (volunteers who each visit a small number of neighbouring households).", P))
A(Paragraph("Three kinds of user", H2))
A(table(["User", "What she or he does in the app", "Sees"], [
    ["Care Group Volunteer (CGV)", "Visits each of her 12 households every 2 weeks. Each visit takes about 10 minutes. She asks the questions for the woman's or child's current stage, measures the child's upper arm (MUAC, mid-upper arm circumference) "
     "and checks for danger signs. She carries a MUAC tape and the tablet only.", "Her own 12 households"],
    ["Community Health Worker (CHW)", "One paid CHW supports one Care Group of 12 volunteers (144 households). The CHW makes 10 scheduled visits to each household: 2 in pregnancy, then at day 1-2, day 3, day 7, 6 weeks, 14 weeks, 6, 9 and 18 months. "
     "Each takes about 15 minutes and includes measurements. The CHW also manages referrals and carries out verbal autopsies (structured interviews with the family after a death).", "All 144 households of the Care Group"],
    ["Supervisor", "Observes CHWs and volunteers at work and fills out a QIVC (Quality Improvement and Verification Checklist) for each observation (section 9).", "Workers, their QIVC scores, and the Reports for the programme (read only)"],
    ["Administrator", "Creates the worker accounts, reads the dashboards and reports, and adjusts the settings of the lives-saved model.", "Everything"]], [W * .22, W * .58, W * .20]))
A(Paragraph("Main functions", H2))
A(bullets("<b>Census form.</b> Adds a household, its pregnant women and children under 24 months, a few risk questions, and a short set of questions on births and deaths in the last 5 years (used to estimate baseline mortality).",
          "<b>Due list.</b> Shows each worker who needs a visit, most urgent first.",
          "<b>Visit forms.</b> A short question set for each stage from pregnancy to 23 months, in English or Swahili.",
          "<b>Danger signs and referrals.</b> A danger sign creates a referral automatically. The CHW records whether the family reached the facility and what the facility advised (the counter-referral).",
          "<b>Births and deaths.</b> A birth record, a death record, and a verbal autopsy that identifies delays in recognising the problem, deciding to seek care, reaching care and receiving care.",
          "<b>Results for workers.</b> Each volunteer sees the percentage of her households following the practices she promotes. Each CHW sees coverage and modelled lives saved for the Care Group area.",
          "<b>Administrator dashboards and reports.</b> Coverage indicators, measured mortality, modelled lives saved and DALYs averted (disability-adjusted life years: years of healthy life gained), worker activity, and lists of women and children who need action.",
          "<b>Offline working.</b> Every record is saved on the tablet first and sent to the central database when a connection is available."))
A(Paragraph("What it does not do", H2))
A(bullets("It does not replace clinical judgment or the Ministry of Health registers. It records what the worker observes and what the family reports.",
          "It does not model maternal lives saved. The lives-saved figure covers children from birth to 23 months.",
          "It does not yet offer languages other than English and Swahili. The Swahili wording was machine-drafted and should be reviewed by a native speaker before field use."))
A(PageBreak())

# ------------------------------------------------------------------ 2
A(Paragraph("2. Getting started", H1))
A(Paragraph("Opening and installing the app", H2))
A(Paragraph("The app is a web page that the tablet stores, so after the first opening it works without a connection. Its address is <font color='#1f66a8'>%s</font>" % URL, P))
A(steps("Connect the tablet to the internet and open the address in the browser.",
        "<b>Android (Chrome):</b> tap the three-dot menu, then <b>Add to Home screen</b> (on some tablets <b>Install app</b>). <b>iPad or iPhone (Safari):</b> tap the Share button, then <b>Add to Home Screen</b>.",
        "From then on, open the app from its icon on the home screen."))
A(Paragraph("Trying it with example data", H2))
A(Paragraph("On the first screen, <b>Try it with example data</b> loads two invented programmes: one in Kenya (8 CHWs, 96 volunteers, 1,152 households) and one in Ghana (9 CHWs, 108 volunteers, 1,296 households). Nothing in example mode is sent to the database. "
            "A selector at the top right lets you look at the app as IGHA (all countries), as the Administrator of either programme, as any CHW or as any volunteer. The address <font color='#1f66a8'>%s#demo</font> always opens the example data and does not "
            "disturb a worker who is signed in on the same tablet, which makes it suitable for demonstrations." % URL, P))
A(fig("The first screen (left) and the sign-in screen (right).", ("01_welcome", (0, 215)), ("02_signin", (0, 260))))
A(Paragraph("Signing in", H2))
A(steps("Tap <b>Sign in</b>.", "Type the sign-in name and the PIN (a number of 6 or more digits) that the Administrator gave you, then tap <b>Sign in</b>. This first sign-in needs a connection.",
        "The tablet downloads your households. After that you can work offline."))
A(Paragraph("When the app is reopened it asks for the PIN again. This check works offline. After 5 wrong PINs at sign-in, the account is locked for 15 minutes. A worker who forgets her PIN asks the Administrator for a new one.", P))
A(fig("The PIN screen shown each time the app is reopened.", ("30_lock", (0, 200)), w=82 * mm))
A(Paragraph("The top bar", H2))
A(bullets("<b>Online / Offline.</b> Shows whether the tablet has a connection. If records are waiting to be sent, their number appears beside it as <b>Not synced</b>.",
          "<b>Sync now.</b> Records are sent automatically a few seconds after each save when the tablet is online. Tap <b>Sync now</b> to send and receive immediately, for example before a supervision meeting.",
          "<b>Language.</b> Switches between English and Kiswahili at any time, including in the middle of a visit."))
A(fig("The volunteer's due list in Swahili.", ("36_sw_due", (0, 560)), w=105 * mm))
A(PageBreak())

# ------------------------------------------------------------------ 3
A(Paragraph("3. Care Group Volunteer: step by step", H1))
A(Paragraph("A volunteer has five tabs: <b>Due list</b>, <b>Register</b>, <b>Referrals</b>, <b>My results</b> and <b>Settings</b>.", P))
A(Paragraph("3.1 See who to visit", H2))
A(Paragraph("The <b>Due list</b> opens first. Each card is one woman or child. The coloured labels say why she or he is on the list. Red cards are urgent (an open referral, a request for CHW support, or a baby in the first month), "
            "amber cards need attention (a visit or vaccine is overdue), and green cards are visits that are due now. Within each colour, those at highest risk come first (Annex B).", P))
A(fig("A volunteer's due list. The counts at the top right give the number of urgent, needs-attention and due cards.", ("04_cgv_due", (0, 700)), w=112 * mm))
A(Paragraph("3.2 Make a home visit", H2))
A(steps("Tap <b>Start visit</b> on the card. The form shows the questions for the stage the woman or child is in, with the number of items and the expected time.",
        "Answer each question by tapping <b>Yes</b> or <b>No</b>, tapping the choices that apply, or typing a number. For a pregnant woman, one question asks how many of 10 food groups she ate yesterday: "
        "count the groups as she lists what she ate (grains and roots; pulses; nuts and seeds; dairy; meat, poultry and fish; eggs; dark green leafy vegetables; other vitamin A-rich fruits and vegetables; other vegetables; other fruits).",
        "Where a question lists several choices (danger signs, vaccines on the card, illness in the last 2 weeks), tap every choice that applies. If none applies, tap <b>None of the above</b>. "
        "The form cannot be saved until each of these questions has an answer; this shows that the question was asked.",
        "If you want the CHW to see this household for any reason, tap <b>Ask for CHW support</b> near the bottom.",
        "Tap <b>Save</b>."))
A(fig("A volunteer's visit form for a child in the 18-month stage, before answering (left) and with a danger sign selected (right).", ("05_visit_blank", (130, 1010)), ("07_visit_danger", (130, 1010)), maxh=160 * mm))
A(Paragraph("3.3 When there is a danger sign", H2))
A(Paragraph("If you tap any danger sign, the app creates a referral when you save and marks the household for CHW support. Tell the family to go to the health facility now, and help them go. "
            "The woman or child then appears at the top of your due list and the CHW's due list with the label <b>Referral not yet completed</b> until the CHW records the outcome.", P))
A(fig("After saving a visit with a danger sign: the open referral, the request for CHW support, overdue vaccines and the date of the next visit.", ("08_after_save", (130, 610)), w=112 * mm))
A(Paragraph("3.4 Add a household, a pregnancy or a baby", H2))
A(steps("Open <b>Register</b>. It lists your households with the mother and child in each. Type in the search box to find a name or village.",
        "To add a newly pregnant woman or a child to a household that is already listed, tap <b>+ Pregnant</b> or <b>+ Child</b> on that household.",
        "To add a new household, tap <b>Census: new household</b> and fill in the form (section 4.6 describes it)."))
A(Paragraph("To report a death, open the woman or child from the Register, tap <b>Record death</b>, and enter the date and place. The CHW is then asked to visit the family for the verbal autopsy.", P))
A(Paragraph("3.5 See your results", H2))
A(Paragraph("<b>My results</b> shows the share of your fortnightly visits that were made, and the percentage of your households following each practice you promote. The bar is your households; the vertical mark is the average for "
            "your whole Care Group area. A practice where your bar is well short of the mark is a good subject for your next visits. With 12 households, one family changes a percentage by about 8 points, "
            "so small differences from the mark are not meaningful. Below these, <b>My QIVC scores</b> shows the result of each time your CHW or a supervisor observed your work (section 9).", P))
A(fig("The volunteer's results page.", ("10_cgv_dash", (130, 1215)), w=112 * mm, maxh=150 * mm))
A(PageBreak())

# ------------------------------------------------------------------ 4
A(Paragraph("4. Community Health Worker: step by step", H1))
A(Paragraph("The CHW has the same five tabs. Her lists cover all 144 households of her Care Group, and she has extra tasks: measurements, births, referrals and verbal autopsies.", P))
A(Paragraph("4.1 The due list", H2))
A(Paragraph("The CHW's due list contains her 10 scheduled visits, every open referral and request for support from her volunteers, follow-up visits after a referral, and any death that still needs a verbal autopsy. "
            "When a programme starts and every household is due at once, the order of the list is the order in which to work: referred and sick children first, then newborns, then the youngest infants and women close to delivery (Annex B).", P))
A(fig("A CHW's due list. The first card is the child referred by the volunteer in section 3.3.", ("14_chw_due", (0, 600)), w=112 * mm))
A(Paragraph("4.2 Make a scheduled visit", H2))
A(steps("Tap <b>Start visit</b>. The form is longer than the volunteer's because it includes measurements: weight, temperature and breathing rate at the newborn day 1-2 visit and at follow-up visits to a child, and blood pressure at pregnancy visit 2 and at follow-up visits to a woman.",
        "Copy the vaccines from the child's card by tapping each one that has been given.", "Tap <b>Save</b>. A danger sign creates a referral, as for the volunteer."))
A(Paragraph("A <b>Start visit</b> button appears only when a scheduled visit is within 14 days of its due date. At other times the card shows the date of the next visit, and <b>Follow-up visit</b> on the person's page records an unscheduled visit, "
            "for example to a sick child. A CHW visit also clears the volunteer's request for support.", P))
A(fig("The CHW's form for the newborn day 7 visit.", ("15_chw_visit", (150, 1000)), w=105 * mm, maxh=140 * mm))
A(Paragraph("4.3 Record a birth", H2))
A(steps("Open the pregnant woman from the <b>Register</b> or the <b>Due list</b> and tap <b>Record birth</b>.",
        "Enter the date, the outcome (live birth or stillbirth), the place, whether a skilled attendant was present, the baby's name and sex, the birth weight if known, and the four questions on care at birth.",
        "Tap <b>Save</b>. The baby is added to the register and the newborn visits (day 1-2, day 3, day 7) appear on the due list at once."))
A(fig("A pregnant woman's page (left) and the birth record (right).", ("19_person_preg", (150, 330)), ("20_birth", (150, 840)), maxh=120 * mm))
A(Paragraph("4.4 Manage referrals", H2))
A(steps("Open <b>Referrals</b>. Each open referral has three buttons.",
        "Tap <b>Confirm arrival at facility</b> when you know the family reached the facility, or <b>Family declined</b> if they did not go.",
        "When the family returns, tap <b>Record counter-referral</b> and enter the diagnosis, the treatment and instructions, and the date for a follow-up home visit. The follow-up then appears on your due list on that date."))
A(fig("The CHW's referral list (left) and the counter-referral form (right).", ("16_chw_refs", (150, 720)), ("17_counter", (150, 720)), maxh=100 * mm))
A(Paragraph("4.5 Record a death and carry out the verbal autopsy", H2))
A(Paragraph("A death recorded by a volunteer appears on the CHW's due list as <b>Verbal autopsy needed</b>. The CHW can also record a death directly from the person's page with <b>Record death</b>. "
            "Visit the family when they are ready, offer condolences, and explain that the questions help to prevent other deaths.", P))
A(steps("Enter the date and place of death, who answered and their relationship to the person who died.",
        "Write what happened from the first sign of illness until the death, in the family's words.",
        "Answer <b>Yes</b> or <b>No</b> for each delay: in recognising the problem, in deciding to seek care, in reaching a health facility, and in receiving care at the facility. Add notes on each delay.",
        "Choose the probable cause and tap <b>Save</b>."))
A(fig("The death record and verbal autopsy form (upper part).", ("22_death", (150, 1010)), w=100 * mm, maxh=135 * mm))
A(Paragraph("4.6 Census: add a new household", H2))
A(steps("In <b>Register</b>, tap <b>Census: new household</b>.",
        "Enter the village, the head of household, the number of people of all ages, the number of women aged 15 to 49, and whether the health facility is more than 1 hour away.",
        "Tap <b>+ Pregnant</b> or <b>+ Child</b> for each pregnant woman and each child under 24 months, and answer the short risk questions for each.",
        "In <b>Births and deaths in the last 5 years</b>, enter the number of children born alive, the number of stillbirths and the number of women who died in pregnancy, childbirth or within 6 weeks after. "
        "Tap <b>+ Child born alive who died in the last 5 years</b> once for each such child and enter the sex, the age at death, the place of death and the short questions on the last illness.",
        "Tap <b>Save</b>. The household's women and children appear on the due lists, ordered by risk."))
A(fig("The census form: household details (left) and births and deaths in the last 5 years (right).", ("12_census_a", (130, 1150)), ("13_census_b", (75, 650)), maxh=135 * mm))
A(Paragraph("4.7 See your results", H2))
A(Paragraph("<b>My results</b> shows the percentage of scheduled visits made on time, the modelled lives saved for the Care Group area, and current coverage of each intervention in the model beside its baseline. "
            "These figures combine the CHW's visits and her volunteers' visits. They are calculated once for the area and are not broken down by volunteer.", P))
A(fig("The CHW's results page.", ("18_chw_dash", (130, 1290)), w=105 * mm, maxh=140 * mm))
A(PageBreak())

# ------------------------------------------------------------------ 5
A(Paragraph("5. Administrator: step by step", H1))
A(Paragraph("5.1 First-time setup", H2))
A(Paragraph("The database is set up once by running the file <font face='Courier'>server/setup.sql</font> in the Supabase SQL editor (Supabase is the hosted database service the app uses). After that:", P))
A(steps("Open the app and tap <b>First-time setup (administrator only)</b>.", "Enter your name, a sign-in name and a PIN of 6 or more digits, twice. Tap <b>Save</b>.",
        "This creates the administrator account. It works once only; after an administrator exists, the link refuses further attempts."))
A(Paragraph("5.2 Add workers", H2))
A(steps("Open <b>Workers</b>.", "Under <b>Add a CHW</b>, enter the CHW's name, village, a sign-in name and a PIN, and tap <b>Save</b>. Each CHW starts a new Care Group.",
        "Under <b>Add a Care Group Volunteer</b>, enter her name and village, choose her CHW, and give her a sign-in name and PIN.",
        "Under <b>Add a supervisor</b>, enter the supervisor's name, a sign-in name and a PIN. Supervisors fill out QIVCs (section 9).",
        "Give each worker her sign-in name and PIN in person. Sign-in names must be unique. Under <b>Give a worker a new PIN</b> you can replace a forgotten PIN."))
A(Paragraph("Households are assigned to the volunteer who registers them in the census form. A CHW who registers a household holds it herself until volunteers are in place.", P))
A(fig("First-time setup (left) and the Workers page after one CHW has been added (right).", ("03_setup", (0, 380)), ("29_workers", (0, 1300)), maxh=125 * mm))
A(Paragraph("5.3 The Administrator's tabs", H2))
A(table(["Tab", "Contents"], [
    ["Overview", "Lives saved to date, households, visits on time, open referrals, measured mortality, and baseline mortality from the census. All figures are cumulative from the start."],
    ["Reports", "Six reports for a chosen period and area, with printing and downloads (section 6)."],
    ["QIVC", "Scores from observations of each CHW and volunteer, by Care Group, and the form for a new observation (section 9)."],
    ["Indicators", "Every coverage indicator, cumulative, with numerator and denominator. <b>Copy as CSV</b> copies the table for pasting into a spreadsheet."],
    ["Model", "The lives-saved calculation: each intervention with its baseline coverage, current coverage and lives saved, and the settings (baseline mortality rates, effect sizes, years of life per death averted)."],
    ["Register", "All households, with search."], ["Referrals", "All referrals and their status."], ["Workers", "CHWs and volunteers, with the number of households each holds."],
    ["Settings", "Area settings (section 5.5), languages, the visit and immunization schedules, export of this tablet's records to a file, and sign-out."]], [W * .18, W * .82]))
A(Spacer(1, 6))
A(fig("The Administrator's Overview page with the example data.", ("23_overview", (0, 1350)), w=118 * mm, maxh=165 * mm))
A(Paragraph("5.4 Produce a report", H2))
A(steps("Open <b>Reports</b>.", "Choose the <b>Period</b>: last month, last quarter, last 12 months, since start, or your own dates.",
        "Choose the <b>Area</b>: all areas, or one CHW's Care Group. When one area is chosen, the worker activity report lists each volunteer.",
        "Tap <b>Print or save as PDF</b> to print the page or save it as a PDF file through the tablet's print dialog.",
        "Tap <b>Download this table</b> under any table to save it as a CSV file (a plain table that opens in Excel or Google Sheets). Downloaded action lists contain every row, including those not shown on screen."))
A(Paragraph("5.5 Area settings", H2))
A(Paragraph("Three switches on the <b>Settings</b> tab fit the app to the programme area. Only the Administrator can change them. They are saved with the programme's settings and reach the workers' tablets at their next sync.", P))
A(bullets("<b>Malaria-endemic area.</b> When this is off, the questions on treated nets (for the pregnant woman and the baby) and on malaria testing for fever are not asked, and nets are left out of the lives-saved model. "
          "The related indicators then show a dash. Leave it on wherever malaria is transmitted. Treated nets protect mainly against mosquitoes that bite at night; the mosquitoes that carry dengue and chikungunya bite mainly by day, "
          "so those diseases are not a reason to turn the switch on.",
          "<b>Malaria vaccine.</b> Adds the four malaria vaccine doses to the immunization schedule. The dose ages entered (6, 7, 9 and 24 months for Kenya; 6, 7, 9 and 18 months for Ghana) should be checked against the national schedule before use.",
          "<b>Yellow fever vaccine.</b> Adds the yellow fever dose at 9 months. It is on in the Ghana settings and off in the Kenya settings."))
A(Paragraph("Turning a vaccine on changes which children count as fully immunized and which appear on the list of children who have missed a dose, from that moment on.", P))
A(fig("The area settings on the Administrator's Settings tab.", ("45_settings_area", (450, 740)), w=112 * mm))
A(PageBreak())

# ------------------------------------------------------------------ 6
A(Paragraph("6. What the reports can tell you", H1))
A(Paragraph("All reports use the CHW's visits and the volunteers' visits together. A report for a period uses only what was recorded in that period, with one exception: lives saved and DALYs averted are always shown to date, "
            "because the model needs the whole observation time to give a stable figure.", P))
A(Paragraph("Report 1. Programme summary", H2))
A(fig("Programme summary for all areas, last quarter.", ("24_rep_summary", (130, 1250)), w=112 * mm, maxh=128 * mm))
A(Paragraph("<b>What it shows.</b> Lives saved and DALYs averted to date, the number of households, and counts of activity in the period: births, new registrations, home visits by each tier, visits where a danger sign was found, referrals, deaths and verbal autopsies.", P))
A(Paragraph("<b>How lives saved is calculated.</b> For each intervention the app compares coverage measured in the programme with baseline coverage for the area (taken mostly from the Kenya Demographic and Health Survey 2022). "
            "It applies published estimates of how much each intervention reduces deaths from each cause, using the method of the Lives Saved Tool in simplified form, to the number of deaths that would be expected at baseline mortality "
            "among the children the programme has observed. The range uses 0.6 and 1.2 times the central estimate. DALYs averted are lives saved multiplied by the years of life gained per death averted "
            "(88.9 years without discounting; 30.8 years when future years are discounted at 3% a year).", P))
A(Paragraph("<b>What it can tell you.</b> Whether coverage has risen enough above baseline to be expected to prevent deaths, roughly how many, and which interventions contribute most (see the Model tab).", P))
A(Paragraph("<b>What it cannot tell you.</b> It is a modelled estimate and does not count actual deaths prevented. It depends on the baseline coverage values being right for the project area; values without a survey source are marked as assumptions "
            "on the Model tab and should be replaced with the project's own baseline survey. It excludes maternal deaths and stillbirths. In one Care Group area the figure is a fraction of one life.", P))
A(Paragraph("Report 2. Coverage and practices", H2))
A(fig("Coverage and practices. For each indicator the upper bar is the chosen period, the lower bar is the period before it, and the vertical mark is baseline coverage.", ("25_rep_cov", (75, 1010)), w=118 * mm, maxh=150 * mm))
A(Paragraph("<b>What it shows.</b> Each indicator as a percentage with its numerator and denominator, for the chosen period and for the period of equal length just before it. Indicators that feed the lives-saved model also show baseline coverage.", P))
A(Paragraph("<b>How each group is counted.</b> Birth indicators cover births in the period. Practices asked at home visits (breastfeeding, nets, handwashing, care for illness) are counted per visit in the period, so a household visited six times contributes six answers. "
            "Immunization is the status at the end of the period among children whose card has been seen.", P))
A(Paragraph("<b>What it can tell you.</b> Which practices are improving, which are static or falling, and which remain furthest from full coverage. These point to the Care Group lessons that need repeating.", P))
A(Paragraph("<b>What it cannot tell you.</b> Most practices are reported by the mother and may be overstated; items marked card or seen are observed. A difference of a few percentage points between periods is within chance variation when the denominator is small: "
            "treat any percentage with a denominator under about 30 as indicative only. Illness indicators (ORS, zinc, care for pneumonia, malaria test) include only children reported ill, so their denominators are small in a single area.", P))
A(Paragraph("Report 3. Mortality", H2))
A(fig("Mortality: deaths by age compared with the number expected at baseline mortality, probable causes, delays and place of death.", ("26_rep_mort", (75, 760)), w=118 * mm))
A(Paragraph("<b>What it shows.</b> Deaths recorded in the period by age group, maternal deaths and stillbirths. <b>Deaths expected at baseline mortality</b> is the number that would have occurred among the same children and births "
            "if mortality had stayed at the baseline rate. Below are the probable causes from verbal autopsies, the delays found, and the place of death.", P))
A(Paragraph("<b>What it can tell you.</b> Whether recorded deaths are below, near or above the baseline expectation, when in the first two years deaths occur, and which delays recur. "
            "A recurring delay in recognising the problem calls for teaching on danger signs; delay in reaching the facility calls for transport arrangements and birth plans; delay in receiving care is a matter to raise with the facility.", P))
A(Paragraph("<b>What it cannot tell you.</b> Numbers are small. In the example programme of 1,152 households, about 3 neonatal deaths are expected in a quarter, so recording 1 or 5 is compatible with no change. "
            "Use the last 12 months or since start for any comparison with baseline. Deaths that workers do not learn of are missing, which makes mortality look lower than it is. "
            "The probable cause is the CHW's judgment from the family's account and has not been confirmed by a clinician.", P))
A(Paragraph("Report 4. Worker activity", H2))
A(fig("Worker activity for one Care Group, listing the CHW and each volunteer.", ("27_rep_activity", (75, 640)), w=118 * mm))
A(Paragraph("<b>What it shows.</b> For each CHW: households, scheduled visits made on time out of those that fell due in the period, volunteers' fortnightly visits made out of those expected, referrals that reached the facility out of those made, "
            "and verbal autopsies completed out of deaths. A scheduled visit counts as on time if it was made within the allowed number of days after its due date (Annex A). When one area is chosen, each volunteer has her own row.", P))
A(Paragraph("<b>What it can tell you.</b> Where visits are being missed, and so where supervision, a lighter workload or a replacement is needed. Low completion of referrals points to barriers between the household and the facility.", P))
A(Paragraph("<b>What it cannot tell you.</b> It measures whether visits were recorded and not how well they were done. A worker whose tablet has not synced appears inactive, so check the sync status before drawing conclusions. "
            "The table is for supportive supervision; it does not show lives saved by worker, because that cannot be estimated reliably for 12 households.", P))
A(Paragraph("Report 5. Quality of work (QIVC)", H2))
A(fig("Quality of work: scores by Care Group for the period.", ("55_rep_q1", (75, 640)), w=118 * mm))
A(Paragraph("<b>What it shows.</b> Three tables built from the QIVCs (section 9). The first gives, for each Care Group, the CHW's mean score in the period, how many volunteers were observed, the volunteers' mean score, and how many volunteers scored below 70%. "
            "When one area is chosen, each volunteer has her own row.", P))
A(Paragraph("<b>Steps most often not done.</b> Every step of the two checklists, ranked by the share of observations in which it applied and was not done, separately for CHWs and volunteers. "
            "The steps at the top are the subjects for refresher training and for the next supervision visits.", P))
A(fig("Steps most often not done (left) and workers who need the most support (right).", ("56_rep_q2", (130, 900)), ("57_rep_q3", (130, 900)), maxh=120 * mm))
A(Paragraph("<b>Workers who need the most support.</b> Each worker is judged on whichever checklist has her lower latest score. She is listed when that score is below target (70% for volunteers, 80% for CHWs) or has fallen by 10 points or more. "
            "The table gives her first, previous and latest scores on that checklist and the change. Those below target and not improving come first, lowest score first; not improving means the latest score is less than 5 points above the one before, or there has been only one observation.", P))
A(Paragraph("<b>What it cannot tell you.</b> A QIVC records one observed visit or session, and a worker may perform differently when watched. Scores from different observers are comparable only if the observers mark the steps the same way, "
            "so observers should practise together on the same visit before scores are compared across areas. One low score is a reason to observe again and coach.", P))
A(Paragraph("Report 6. Action lists", H2))
A(fig("Action lists: open referrals and children who have missed vaccines.", ("31_rep_actions", (75, 760)), w=118 * mm))
A(Paragraph("<b>What it shows.</b> Four lists of named women and children, each with village and volunteer: those with no home visit in the period; open referrals with the number of days open; "
            "children who have had no vaccine (zero-dose) or have missed a dose that is more than 2 weeks overdue; and children aged 6 months or more whose last MUAC was under 12.5 cm (under 11.5 cm is marked severe). "
            "The last three lists show the position today, whatever period is chosen.", P))
A(Paragraph("<b>How to use it.</b> Download the lists and give each CHW the rows for her area. The screen shows the first 25 rows of each list; the download has all of them.", P))
A(Paragraph("Other pages that support the reports", H2))
A(bullets("<b>Overview, measured mortality.</b> The same comparison as report 3 for the whole programme since the start, expressed as rates.",
          "<b>Overview, baseline mortality from the census.</b> Mortality rates calculated from the births and deaths that families reported for the last 5 years. Once the census has recorded at least 500 live births, "
          "the button <b>Use the census rates as the model baseline</b> replaces the national rates in the model with the project's own.",
          "<b>Model.</b> Lives saved by intervention. The settings can be edited there and restored with the reset button."))
A(fig("The Indicators tab (left) and the Model tab (right).", ("32_ind", (75, 900)), ("33_model", (75, 900)), maxh=120 * mm))
A(PageBreak())

# ------------------------------------------------------------------ 7
A(Paragraph("7. Problems and their solutions", H1))
A(table(["Problem", "What to do"], [
    ["The app does not show a recent change (for example the Reports tab is missing).", "The tablet loads a new version in the background and uses it the next time the app is opened. With a connection, open the app, close it completely, and open it again."],
    ["Sign-in fails with \"Wrong sign-in name or PIN\".", "Check the sign-in name (it is not the worker's full name) and the PIN. After 5 wrong attempts the account is locked for 15 minutes. The Administrator can set a new PIN under Workers."],
    ["A worker cannot sign in on a new tablet.", "The first sign-in on each tablet needs a connection."],
    ["\"Not synced\" stays beside the connection status.", "The tablet has records that have not reached the database. Connect to the internet and tap Sync now. Nothing is lost while the records wait; they are stored on the tablet."],
    ["A visit form will not save.", "A question with several choices has no answer. Its title turns red with an asterisk. Tap the choices that apply or None of the above."],
    ["There is no Start visit button on a card.", "The next scheduled visit is not yet within 14 days of its due date (3 days for a volunteer's fortnightly visit). Open the card and use Follow-up visit if a visit is needed now."],
    ["Two workers changed the same record while offline.", "The database keeps the version saved most recently. Visits are separate records and are never overwritten by another worker's visit."],
    ["A tablet is lost or a worker leaves.", "The Administrator sets a new PIN for that worker. The old PIN then cannot sign in, and the lost tablet can no longer send or receive records. Records already synced are safe in the database. Records already stored on the lost tablet can still be opened there with the old PIN while it is offline; the app cannot erase a tablet remotely, which is a matter for the security review."],
    ["The questions on treated nets or malaria testing do not appear.", "The Malaria-endemic area switch is off for this programme. The Administrator can turn it on in Settings (section 5.5)."],
    ["The Administrator wants a copy of the data.", "Use the downloads on the Reports tab, Copy as CSV on the Indicators tab, or Export records from this tablet (file) in Settings."],
    ["The example data appears where real data is expected.", "Tap Leave example mode on the yellow bar, then sign in."]], [W * .36, W * .64]))
A(PageBreak())
A(Paragraph("8. Several partners and countries", H1))
A(Paragraph("From version 0.4 the app supports several partners in several countries. The design has three levels.", P))
A(table(["Level", "Who", "What they see"], [
    ["Programme", "A programme is one partner's work in one country. The <b>programme administrator</b> manages its CHWs and volunteers.", "The identified records of that programme only."],
    ["Country", "Each country has its own database. The <b>country administrator</b> (the account made by first-time setup) creates programmes and their administrators.", "The identified records of every programme in that country."],
    ["IGHA", "IGHA staff use a separate central database that receives a de-identified copy from each country.", "Every country, without names, villages, household details or free text."]], [W * .14, W * .5, W * .36]))
A(Paragraph("Settings by country", H2))
A(Paragraph("Each country has its own baseline mortality, baseline coverage and immunization schedule, and every figure for a country is calculated with that country's settings. The Kenya settings use the Kenya Demographic and Health Survey 2022. "
            "The Ghana settings use the Ghana Demographic and Health Survey 2022 (neonatal mortality 17 per 1,000 live births), the Ghana Maternal Health Survey 2017 (maternal mortality 310 per 100,000 live births) and the Ghana Health Service schedule, "
            "which adds a hepatitis B birth dose, yellow fever at 9 months and meningitis A at 18 months. The causes of death used in the Ghana model are still the Kenya values and need to be replaced with Ghana estimates, particularly for malaria. "
            "A programme can save its own settings on the Model tab when its area differs from the national picture; otherwise it uses the country's. The area switches of section 5.5 (malaria-endemic area, malaria vaccine, yellow fever vaccine) are saved the same way. "
            "The Ghana example is in English only.", P))
A(Paragraph("The IGHA view", H2))
A(Paragraph("In the example data, choose <b>IGHA · all countries</b> in the selector at the top right (the address ending in #demo opens there). The <b>Countries</b> tab shows each country in its own column for a chosen period: "
            "programme size and activity, mortality compared with that country's baseline, delays found in verbal autopsies, and the behaviour and coverage indicators with a bar for each country and a mark at that country's baseline. "
            "Each table can be downloaded. The <b>Reports</b> tab gives reports 1 to 4 of section 6 for one country at a time; Care Groups are numbered and no worker is named, and the action lists are not shown because they name women and children.", P))
A(fig("The IGHA Countries tab: programmes (left) and mortality by country (right).", ("40_igha_a", (0, 1250)), ("41_igha_b", (75, 1010)), maxh=125 * mm))
A(fig("The IGHA Countries tab: behaviour and coverage indicators for each country, with each country's baseline.", ("42_igha_c", (75, 1250)), w=118 * mm, maxh=150 * mm))
A(Paragraph("<b>Reading the comparison.</b> The two columns describe different populations with different baselines, so the useful comparison is each country against its own baseline and its own earlier periods, and only then between countries. "
            "With about 1,000 to 1,300 households per country, the recorded and expected deaths are in single figures, and a difference between countries can be chance.", P))
A(Paragraph("How records are de-identified", H2))
A(bullets("Names, heads of household, villages and all free text (the verbal autopsy account, diagnosis and treatment notes) are removed.",
          "Every record number is replaced by a code that cannot be traced back to the original, while the links between a household, its women and children, their visits and their worker are kept.",
          "All dates belonging to one household are moved by the same number of days, between 14 earlier and 14 later. Ages and intervals stay exact, so the indicators are unaffected, but a date of birth no longer matches the real one.",
          "De-identified records are not anonymous: a death in a small Care Group may still be recognisable to someone who knows the community. The central copy therefore still needs controlled access and a data-sharing agreement with each partner."))
A(Paragraph("Setting up a country and its programmes", H2))
A(steps("Create a database for the country and run <font face='Courier'>server/setup.sql</font> in it. Add the country's entry to the list of databases in the app. The country's address is the app address followed by <font face='Courier'>?c=</font> and its code, for example <font face='Courier'>?c=gh</font> for Ghana; Kenya is the default.",
        "Open that address and use <b>First-time setup</b> to create the country administrator.",
        "On the <b>Workers</b> tab, under <b>Programmes</b>, add each programme with its partner, then add a programme administrator for each and give that person the sign-in name and PIN.",
        "Each programme administrator signs in and adds the programme's CHWs and volunteers as in section 5.2. Care Groups are numbered within each programme."))
A(fig("The country administrator's Workers tab with two programmes.", ("44_programmes", (0, 700)), w=112 * mm))
A(Paragraph("<b>What is not yet in place.</b> The central IGHA database and the scheduled job that copies each country's de-identified records into it have not been set up, so the IGHA view works only with the example data. "
            "No database exists yet for Ghana. A database created before version 0.4 needs the setup file run again to gain the programme functions; until then the app works as before and hides them.", NOTE))
A(PageBreak())
A(Paragraph("9. QIVC: observing the quality of work", H1))
A(Paragraph("A QIVC (Quality Improvement and Verification Checklist) is a list of steps that an observer marks while watching a worker. It serves two purposes: the worker receives specific feedback straight after the observation, "
            "and the programme can see which steps are being missed and which workers need more support. The app has two checklists.", P))
A(table(["Checklist", "Used when", "Steps"], [
    ["Home visit", "The observer accompanies a CHW or a volunteer on a home visit.", "39 steps: starting the visit, using the visit form correctly (asking every question, checking danger signs, looking at the card, measuring MUAC, saving), counselling methods, discussion, and the summary at the end. "
     "A few steps apply only to CHWs (other measurements, referrals) or only to volunteers (asking for CHW support)."],
    ["Group session", "The observer watches a volunteer lead a practice promotion session, or a CHW lead a Care Group meeting.", "42 steps: set-up, overall communication, beginning, middle and end of the session."]], [W * .16, W * .34, W * .5]))
A(Paragraph("Who can observe whom", H2))
A(bullets("A <b>CHW</b> observes the volunteers of her own Care Group.", "A <b>Supervisor</b> observes CHWs and volunteers. The Supervisor has a separate sign-in with three working tabs: Due list (the CHWs to observe next), QIVC, and Reports for the programme (section 6), which the Supervisor can read but not change.",
          "The <b>Administrator</b> can observe any worker. No worker can fill out or change a QIVC about herself."))
A(Paragraph("Whom to observe next: the supervision schedule", H2))
A(Paragraph("The <b>Due list</b> tells each observer whom to observe next. The schedule is one home-visit QIVC and one group-session QIVC for every worker in each period:", P))
A(table(["Observer", "Workers observed", "Period", "QIVCs in the period", "Routine pace", "Most the list asks for"],
        [["CHW", "The volunteers of her Care Group (12 in the example)", "6 months", "24", "About 1 a week", "2 a week"],
         ["Supervisor", "The CHWs of the programme (8 in the Kenya example)", "3 months", "16", "1 to 2 a week", "3 a week and 12 a month"]], [W * .12, W * .28, W * .11, W * .14, W * .15, W * .20]))
A(bullets("A QIVC is <b>due</b> when the worker has had none of that kind (home visit or group session) within the period. A QIVC filled out by any observer counts.",
          "Workers never observed come first. Their order is arbitrary, differs from one observer to another, and does not change from day to day. After that, the list offers the worker whose last QIVC of that kind is oldest.",
          "<b>Workers below target come before the others.</b> A volunteer whose latest score on a checklist is below 70%, or a CHW whose latest score is below 80%, is offered again for the same checklist once 4 weeks have passed since that QIVC, lowest score first. Her card is marked in red and shows the score. She stays on this 4-week cycle until a QIVC on that checklist reaches the target.",
          "When a worker below target is waiting, the list asks for more visits that week (up to the limit in the table), and one visit a week is still kept for the routine schedule so that workers not yet observed are not pushed back indefinitely.",
          "The list shows only as many supervision visits as the pace requires. The chips at the right give the number of follow-up observations waiting for workers below target, the number of routine QIVCs still due, and the number done in the last 7 days.",
          "When the week's supervision is done, or nothing is due, the list still names the next worker and the date her QIVC falls due.",
          "On a CHW's Due list, the supervision visits appear below the home visits marked Urgent or Needs attention and above the other home visits that are due. The link <b>Skip to supervision list</b> under the Due list heading scrolls straight to them. The Supervisor's Due list holds supervision visits only.",
          "<b>Observe</b> opens the checklist with the worker and the kind of observation already chosen."))
A(fig("Priority supervision visits on a CHW's Due list. Two volunteers below target are offered first.", ("58_due_sup_chw", (405, 775)), maxh=70 * mm))
A(fig("Priority supervision visits on the Supervisor's Due list.", ("59_due_sup", (285, 640)), maxh=70 * mm))
A(Paragraph("Filling out a QIVC", H2))
A(steps("Tap <b>Observe</b> on the Due list, or open the <b>QIVC</b> tab and tap <b>Observe</b> beside the worker, or <b>New QIVC</b>.", "Choose what was observed (home visit or group session) and the date.",
        "Watch the whole visit or session without interrupting. Mark each step <b>Yes</b>, <b>No</b>, or <b>N/A</b> where the step did not apply (for example, no danger sign was found).",
        "Give the ratings from 1 to 10 for the content and the overall performance, and write recommendations in the comments box.",
        "Tap <b>Save</b>. Every step must be marked first; any still unmarked turn red.", "Go through the result with the worker straight away: begin with what she did well, then the steps not done, and agree what she will practise."))
A(fig("The supervisor's QIVC tab (left) and the start of the home-visit checklist (right).", ("50_qivc_list", (0, 1250)), ("51_qform_blank", (0, 1250)), maxh=125 * mm))
A(Paragraph("The score", H2))
A(Paragraph("The score is the number of steps marked Yes divided by the number marked Yes or No. Steps marked N/A are left out, and the 1-to-10 ratings are kept beside the score without entering it, as on the paper forms. "
            "Scores below 70% for volunteers and below 80% for CHWs are shown in red.", P))
A(Paragraph("Where the results appear", H2))
A(bullets("<b>The worker</b> sees her own QIVCs under <b>My results</b>: each score, the steps not done, the ratings and the observer's comments.",
          "<b>The QIVC tab</b> lists each Care Group with its CHW and volunteers: the latest home-visit and group-session scores, the number of QIVCs, the change, and a status. <b>Open</b> shows the worker's full history.",
          "<b>Reports</b>, report 5, gives scores by Care Group for the period, the steps most often not done, and the workers who need the most support (section 6).",
          "<b>The IGHA Countries tab</b> shows the mean score of CHWs and of volunteers for each country. Worker names and observers' comments are removed from the de-identified copy."))
A(fig("A volunteer's QIVC history as the supervisor sees it (left) and as she sees it under My results (right).", ("53_qw", (0, 1250)), ("54_qmine", (75, 1250)), maxh=125 * mm))
A(Paragraph("The checklists follow the Quality Improvement and Verification Checklists for practice promotion sessions and for individual counselling developed at Food for the Hungry. The home-visit checklist adds the steps on using this app's visit form. "
            "The checklists are in English only in this version. A database set up before version 0.6 needs the setup file run again before supervisors can be added and QIVCs synced.", NOTE))
A(Spacer(1, 10))
A(Paragraph("Annex A. Visit schedule (Kenya configuration)", H1))
A(table(["CHW visit", "Due", "Counts as on time if made within", "Volunteer asks the same question set every 2 weeks while the woman or child is at"], [
    ["1. Pregnancy visit 1", "At registration", "30 days", "Enrolment to 31 weeks of pregnancy"], ["2. Pregnancy visit 2 (birth plan)", "6 weeks before the due date", "35 days", "32 weeks to birth"],
    ["3. Newborn day 1-2", "Day 1 after birth", "2 days", "Days 0 to 2"], ["4. Newborn day 3", "Day 3", "2 days", "Days 3 to 5"], ["5. Newborn day 7", "Day 7", "5 days", "Days 6 to 27"],
    ["6. 6 weeks", "Day 42", "28 days", "4 to 9 weeks"], ["7. 14 weeks", "Day 98", "42 days", "10 weeks to 5 months"], ["8. 6 months", "Day 183", "60 days", "6 to 8 months"],
    ["9. 9 months", "Day 274", "90 days", "9 to 17 months"], ["10. 18 months", "Day 548", "150 days", "18 to 23 months"]], [W * .25, W * .22, W * .18, W * .35]))
A(Spacer(1, 10))
A(Paragraph("Annex B. How the due list is ordered", H1))
A(Paragraph("Cards are grouped as urgent, needs attention and due. Within each group they are ordered by a risk score, highest first. The points below are added together. "
            "The weights reflect the relative risk of death in each situation; they are judgments made for this app and were not derived from a statistical model.", P))
A(table(["Situation", "Points"], [
    ["Open referral; open request for CHW support", "80 each"], ["Child reported sick on census day and not yet seen by the CHW", "70"], ["Child in the first week of life", "60"], ["Child aged 7 to 27 days", "50"],
    ["Woman due to deliver within 4 weeks", "40"], ["Child aged 1 to 5 months; small baby under 6 months (in addition to age)", "25 each"], ["Woman at 28 to 35 weeks of pregnancy", "20"],
    ["Child with no vaccine yet; woman with no antenatal care yet; earlier child death in the household", "15 each"], ["Child aged 6 to 11 months", "12"],
    ["Household far from the facility; first pregnancy; woman aged under 18 or 35 and over", "10 each"], ["Woman earlier in pregnancy", "8"], ["Child aged 12 to 23 months", "5"]], [W * .78, W * .22]))
# keep each heading on the same page as the figure or list that follows it
S2 = []; i = 0
while i < len(S):
    x = S[i]; nxt = S[i + 1] if i + 1 < len(S) else None
    if isinstance(x, Paragraph) and x.style.name in ("h1", "h2") and isinstance(nxt, (KeepTogether, ListFlowable)):
        S2.append(KeepTogether([x] + (list(nxt._content) if isinstance(nxt, KeepTogether) else [nxt]))); i += 2
    else: S2.append(x); i += 1
doc.build(S2, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
