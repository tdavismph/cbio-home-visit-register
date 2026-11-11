"""Builds CBIO_Behaviours_by_Visit.pdf. Run: python3 make_behaviours_pdf.py [output.pdf]"""
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

OUT = sys.argv[1] if len(sys.argv) > 1 else "CBIO_Behaviours_by_Visit.pdf"
DATE = "12 November 2026"
INK, MUTED, LINE, BAND = colors.HexColor("#16302b"), colors.HexColor("#5b6b68"), colors.HexColor("#c9d3d1"), colors.HexColor("#e6eeec")
st = lambda n, **k: ParagraphStyle(n, fontName=k.pop("font", "Helvetica"), textColor=k.pop("color", INK), **k)
H1 = st("h1", font="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=4)
H2 = st("h2", font="Helvetica-Bold", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=4)
P = st("p", fontSize=8.6, leading=11.5, spaceAfter=5)
C = st("c", fontSize=7.9, leading=10)
CB = st("cb", font="Helvetica-Bold", fontSize=7.9, leading=10)
TH = st("th", font="Helvetica-Bold", fontSize=7.6, leading=9.5)
SEC = st("sec", font="Helvetica-Bold", fontSize=8.4, leading=11)

V = {1: "Visit 1 · first pregnancy visit, at registration", 2: "Visit 2 · 34 weeks of pregnancy", 3: "Visit 3 · day 1-2", 4: "Visit 4 · day 3", 5: "Visit 5 · day 7",
     6: "Visit 6 · 6 weeks", 7: "Visit 7 · 14 weeks", 8: "Visit 8 · 6 months", 9: "Visit 9 · 9 months", 10: "Visit 10 · 18 months"}
# number, behaviour, promote during, promote prior to CHW visit, measured at, lesson block
ROWS = [
 "A. Enrolment to 31 weeks of pregnancy (before the early-pregnancy question set)",
 (1, "Start antenatal care early and attend every contact", "From enrolment, throughout pregnancy", V[2], "Early pregnancy; late pregnancy (contacts on the card)", "1"),
 (2, "Take iron-folic acid every day", "From enrolment, throughout pregnancy", V[2], "Early pregnancy; late pregnancy", "1"),
 (3, "Get two tetanus (Td) doses", "From enrolment; before 28 weeks", V[2], "Early pregnancy; late pregnancy (doses on the card)", "1"),
 (4, "Have an HIV test in this pregnancy", "At enrolment", V[1] + " (the only visit that measures it)", "Early pregnancy (card)", "1"),
 (5, "Sleep under a treated net every night (pregnant woman)", "From enrolment", V[2], "Early pregnancy; late pregnancy", "5"),
 (6, "Know the danger signs in pregnancy and go to the facility at once", "From enrolment, repeated", V[2], "Early and late pregnancy (names 3 signs); danger-sign check at every visit", "1"),
 (7, "Eat an extra meal each day and a varied diet", "From enrolment", V[2], "Early pregnancy; late pregnancy (extra meal or snack yesterday); woman's MUAC at early pregnancy", "1"),
 (8, "Keep a handwashing place with soap and water; wash at key times", "Before enrolment visit, then repeated", V[5] + "; again before visits 8 and 10", "Early pregnancy; day 7; 6 months; 18 months (observed)", "6"),
 (9, "Treat drinking water or use a safe source", "Before enrolment visit, then before 6 months", V[8], "Early pregnancy; 6 months", "6"),
 (10, "Use a latrine", "Before enrolment visit, then repeated", V[8] + "; again before visit 10", "Early pregnancy; 6 months; 18 months", "6"),
 "B. 24 to 36 weeks of pregnancy (before the late-pregnancy question set and the birth)",
 (11, "Make a birth plan: choose the facility, arrange transport, save money, name a companion", "24 to 34 weeks", V[2], "Late pregnancy (items ready)", "2"),
 (12, "Give birth in a health facility with a skilled attendant", "24 weeks to birth", V[3], "Birth record", "2"),
 (13, "Dry the baby, keep skin-to-skin, delay the first bath 24 hours", "28 weeks to birth", V[3], "Birth record; day 1-2; day 3", "2"),
 (14, "Put the baby to the breast within 1 hour; give colostrum", "28 weeks to birth", V[3], "Birth record", "3"),
 (15, "Clean cord care: chlorhexidine, nothing else on the cord", "28 weeks to birth", V[3], "Birth record; day 1-2; day 3; day 7", "2"),
 (16, "Know newborn danger signs and seek care the same day", "28 weeks to birth, repeated in week 1", V[3], "Day 1-2; day 3; day 7 (danger-sign check); referrals that reach the facility", "2"),
 (17, "Know danger signs for the mother after birth", "28 weeks to birth", V[3], "Day 1-2; day 3; day 7; 6 weeks", "2"),
 (18, "Mother and baby checked by a health worker within 48 hours", "28 weeks to birth", V[4], "Day 3", "2"),
 "C. Birth to 6 weeks (before the day 1-2, 3, 7 and 6-week question sets)",
 (19, "Give only breast milk: no water, tea, porridge or other milk", "Late pregnancy; every visit to 6 months", V[3], "Day 1-2; day 3; day 7; 6 weeks; 14 weeks", "3"),
 (20, "Kangaroo care day and night for a small or early baby", "At birth, for small babies", V[3], "Day 1-2; day 3; day 7", "2"),
 (21, "Take the baby for BCG and polio at birth, then vaccines at 6, 10 and 14 weeks", "Late pregnancy; weeks 1 to 5", V[5] + " (birth doses); visits 6 and 7 (later doses)", "Day 7; 6 weeks; 14 weeks (card)", "5"),
 (22, "Baby sleeps under a treated net every night", "From birth", V[5], "Day 7; 14 weeks; 6, 9 and 18 months", "5"),
 (23, "Start a modern family planning method by 6 weeks", "Late pregnancy; weeks 1 to 6", V[6], "6 weeks; 14 weeks; 6, 9 and 18 months", "7"),
 "D. 6 weeks to 5 months (before the 14-week and 6-month question sets)",
 (24, "Know child danger signs and seek care the same day", "Weeks 4 to 10, then repeated", V[6], "6 weeks onward (danger-sign check); referrals that reach the facility", "4"),
 (25, "Give ORS and zinc for diarrhoea; keep feeding", "Weeks 6 to 14", V[7], "6 weeks onward, whenever diarrhoea in the last 2 weeks is reported", "4"),
 (26, "Take a child with cough and fast or difficult breathing to a health worker", "Weeks 6 to 14", V[7], "6 weeks onward, whenever reported", "4"),
 (27, "Have a child with fever tested for malaria the same or next day", "Weeks 6 to 14", V[7], "6 weeks onward, whenever fever is reported", "4"),
 (28, "Continue only breast milk until 6 months", "Weeks 6 to 24", V[7], "6 weeks; 14 weeks", "3"),
 (29, "Start soft foods at 6 months, not before", "Months 4 to 6", V[8], "6 months", "8"),
 (30, "Bring the child for vitamin A at 6 months, then every 6 months", "Months 4 to 6", V[9] + "; again before visit 10", "9 months; 18 months (card)", "5"),
 "E. 6 to 17 months (before the 9-month and 18-month question sets)",
 (31, "Feed at least 5 of 8 food groups each day; right amount and frequency for age", "Months 6 to 9, repeated to 18", V[9] + "; again before visit 10", "9 months; 18 months (food groups yesterday); MUAC at 6, 9, 18 months", "8"),
 (32, "Continue breastfeeding to 24 months", "Months 6 to 18", V[9] + "; again before visit 10", "9 months; 18 months", "8"),
 (33, "Take the child for measles-rubella at 9 and 18 months", "Months 7 to 9; months 16 to 18", V[9] + " (first dose); " + V[10] + " (second dose)", "9 months; 18 months (card)", "5"),
 (34, "Keep the handwashing place and latrine in use; put child faeces in the latrine", "Months 4 to 6; months 15 to 18", V[8] + "; again before visit 10", "6 months; 18 months (handwashing place, latrine, child's last stool)", "6"),
]
BLOCKS = [("1", "Healthy pregnancy", "Antenatal care, iron-folic acid, tetanus doses, HIV test, diet, danger signs in pregnancy", "1-4, 6, 7"),
 ("2", "Birth and the first week", "Birth plan, facility delivery, drying and skin-to-skin, cord care, kangaroo care, newborn and maternal danger signs, check within 48 hours", "11-13, 15-18, 20"),
 ("3", "Breastfeeding", "Breast within 1 hour, only breast milk to 6 months", "14, 19, 28"),
 ("4", "When a child is sick", "Danger signs, ORS and zinc, care for fast breathing, malaria test for fever", "24-27"),
 ("5", "Preventing illness", "Vaccines on time, vitamin A, treated nets", "5, 21, 22, 30, 33"),
 ("6", "Water, sanitation and hygiene", "Handwashing place with soap, safe water, latrine, child faeces into the latrine", "8-10, 34"),
 ("7", "Family planning", "Method started by 6 weeks; spacing of at least 2 years", "23"),
 ("8", "Feeding from 6 months", "Soft foods at 6 months, food groups, continued breastfeeding", "29, 31, 32")]
SETS = [("Early pregnancy", "Visit 1 · pregnancy visit 1", "Enrolment to 31 weeks of pregnancy"), ("Late pregnancy", "Visit 2 · pregnancy visit 2", "32 weeks to birth"),
 ("Birth record", "Recorded once, when the birth is reported", "At birth"), ("Day 1-2", "Visit 3", "Days 0 to 2"), ("Day 3", "Visit 4", "Days 3 to 5"), ("Day 7", "Visit 5", "Days 6 to 27"),
 ("6 weeks", "Visit 6", "4 to 9 weeks"), ("14 weeks", "Visit 7", "10 weeks to 5 months"), ("6 months", "Visit 8", "6 to 8 months"), ("9 months", "Visit 9", "9 to 17 months"), ("18 months", "Visit 10", "18 to 23 months")]

def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(MUTED)
    c.drawString(d.leftMargin, 8 * mm, "CBIO+ Home Visit Register | Behaviours to promote before each visit | Draft for review, " + DATE)
    c.drawRightString(d.pagesize[0] - d.rightMargin, 8 * mm, "Page %d" % d.page); c.restoreState()

def table(head, rows, widths, sections=()):
    data = [[Paragraph(h, TH) for h in head]] + rows
    ts = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for r in sections:
        ts += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), BAND)]
    return Table(data, colWidths=widths, repeatRows=1, style=TableStyle(ts))

doc = SimpleDocTemplate(OUT, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=11 * mm, bottomMargin=14 * mm,
                        title="Behaviours to promote before each visit", author="CBIO+ Home Visit Register")
W = doc.width
S = [Paragraph("Behaviours to promote before each visit", H1),
     Paragraph("For sequencing Care Group lessons against the indicators in the CBIO+ Home Visit Register (Kenya configuration). Each behaviour is listed in the period when it should be promoted, "
               "so that the household has heard it before the visit at which it is measured. The column <b>Promote prior to CHW visit # / child age</b> gives the scheduled CHW visit (1 to 10) "
               "by which promotion should already have happened, with the age of the child or the stage of pregnancy at that visit. Visit 1 takes place at registration and records the starting level, "
               "so a behaviour that is first measured at visit 1 shows the next CHW visit that measures it.", P)]
rows, secs = [], []
for r in ROWS:
    if isinstance(r, str):
        secs.append(len(rows) + 1); rows.append([Paragraph(r, SEC)] + [""] * 5)
    else:
        rows.append([Paragraph(str(r[0]), C), Paragraph(r[1], C), Paragraph(r[2], C), Paragraph(r[3], CB), Paragraph(r[4], C), Paragraph(r[5], C)])
S.append(table(["#", "Behaviour to promote", "Promote during", "Promote prior to CHW visit # / child age", "Measured at (question set)", "Lesson block"], rows,
               [W * x for x in (.03, .27, .17, .215, .26, .055)], secs))
S += [Paragraph("Suggested lesson blocks", H2),
      Paragraph("A Care Group meets as one group, but its households are at different stages: some women are pregnant while others have a child of 18 months. The table above therefore cannot be followed "
                "as a single calendar. Two things together cover it. First, the group lessons run in the block order below, which places the periods with the most deaths first (pregnancy, birth and the "
                "first week, then breastfeeding and care of the sick child). Second, at each fortnightly home visit the volunteer repeats the behaviours for that household's own stage, using the "
                "'Promote during' and 'Promote prior to CHW visit' columns. The block order is a proposal for discussion.", P),
      table(["Block", "Theme", "Content", "Behaviours"], [[Paragraph(x, C) for x in b] for b in BLOCKS], [W * x for x in (.06, .2, .58, .16)]),
      Paragraph("When each question set is asked", H2),
      Paragraph("The CHW asks a question set once, at her scheduled visit. The Care Group Volunteer asks the same set at every fortnightly visit while the woman or child is in the matching stage, "
                "so most behaviours are measured several times.", P),
      table(["Question set", "Asked by the CHW at", "Asked by the Care Group Volunteer every 2 weeks while the woman or child is at"], [[Paragraph(x, C) for x in b] for b in SETS], [W * x for x in (.2, .35, .45)]),
      Spacer(1, 6),
      Paragraph("Notes. (1) The questions for behaviour 7 (extra meal or snack yesterday) and behaviour 34 (child's last stool put in a latrine) were added to the app in version 0.3.1. "
                "(2) Illness behaviours 25 to 27 are measured only in households that report the illness in the last 2 weeks, so their denominators are small in any one Care Group. "
                "(3) The malaria vaccine and yellow fever vaccine are not in this configuration; they apply only in designated Kenyan counties.", P)]
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
