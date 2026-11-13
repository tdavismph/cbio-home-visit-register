"""Builds CBIO_Behaviours_by_Visit.pdf. Run: python3 make_behaviours_pdf.py [output.pdf]"""
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

OUT = sys.argv[1] if len(sys.argv) > 1 else "CBIO_Behaviours_by_Visit.pdf"
DATE = "13 November 2026"
INK, MUTED, LINE, BAND = colors.HexColor("#16302b"), colors.HexColor("#5b6b68"), colors.HexColor("#c9d3d1"), colors.HexColor("#e6eeec")
st = lambda n, **k: ParagraphStyle(n, fontName=k.pop("font", "Helvetica"), textColor=k.pop("color", INK), **k)
H1 = st("h1", font="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=4)
H2 = st("h2", font="Helvetica-Bold", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=4)
P = st("p", fontSize=8.6, leading=11.5, spaceAfter=5)
C = st("c", fontSize=7.3, leading=9.2)
CB = st("cb", font="Helvetica-Bold", fontSize=7.3, leading=9.2)
TH = st("th", font="Helvetica-Bold", fontSize=7.2, leading=9)
SEC = st("sec", font="Helvetica-Bold", fontSize=8.4, leading=11)

V = {1: "Visit 1 · first pregnancy visit, at registration", 2: "Visit 2 · 34 weeks of pregnancy", 3: "Visit 3 · day 1-2", 4: "Visit 4 · day 3", 5: "Visit 5 · day 7",
     6: "Visit 6 · 6 weeks", 7: "Visit 7 · 14 weeks", 8: "Visit 8 · 6 months", 9: "Visit 9 · 9 months", 10: "Visit 10 · 18 months"}
E, L = "Pregnancy, up to month 7", "pregnancy, months 8-9"
NM = "Not modelled."
EBF = "About 27% fewer diarrhoea deaths and 21% fewer pneumonia deaths at 1-23 months."
# number, behaviour, promote during, promote prior to CHW visit, measured at (age or stage), survival impact, lesson block
ROWS = [
 "A. Enrolment to 31 weeks of pregnancy",
 (1, "Start antenatal care early and attend every contact", "From enrolment, throughout pregnancy", V[2], E + "; " + L + " (contacts on the card)", "Not modelled. Gives access to tetanus doses, iron-folic acid and HIV testing.", "1"),
 (2, "Take iron-folic acid every day", "From enrolment, throughout pregnancy", V[2], E + "; " + L, NM, "1"),
 (3, "Get two tetanus (Td) doses", "From enrolment; before 28 weeks", V[2], E + "; " + L + " (doses on the card)", "About 94% fewer neonatal tetanus deaths.", "1"),
 (4, "Have an HIV test in this pregnancy", "At enrolment", V[1] + " (the only visit that measures it)", E + " (card)", NM, "1"),
 (5, "Sleep under a treated net every night (pregnant woman), in malaria-endemic areas", "From enrolment", V[2], E + "; " + L, "Not modelled (the model counts nets for children only).", "5"),
 (6, "Know the danger signs in pregnancy and go to the facility at once", "From enrolment, repeated", V[2], E + "; " + L + " (names 3 signs); danger-sign check at every visit", "Not modelled; maternal deaths are not in the model.", "1"),
 (7, "Eat an extra meal each day and a varied diet", "From enrolment", V[2], E + "; " + L + " (extra meal yesterday; number of food groups yesterday); MUAC at visit 1", NM, "1"),
 (8, "Keep a handwashing place with soap and water; wash at key times", "Before enrolment visit, then repeated", V[5] + "; again before visits 8 and 10", E + "; day 7; 6 months; 18 months (observed)", "About 48% fewer diarrhoea deaths at 1-23 months.", "6"),
 (9, "Treat drinking water or use a safe source", "Before enrolment visit, then before 6 months", V[8], E + "; 6 months", NM, "6"),
 (10, "Use a latrine regularly", "Before enrolment visit, then repeated", V[8] + "; again before visit 10", E + "; 6 months; 18 months", NM, "6"),
 "B. Pregnancy to the birth",
 (11, "Make a birth plan: choose the facility, arrange transport, save money, name a companion", "From enrolment; plan complete by 34 weeks", V[2], "Pregnancy, months 8-9 (items ready)", "Not modelled directly; supports facility birth (behaviour 12).", "2"),
 (12, "Give birth in a health facility with a skilled attendant", "24 weeks to birth", V[3], "At birth (birth record)", "About 27% fewer neonatal sepsis deaths (clean birth) and 30% fewer birth asphyxia deaths (skilled attendant).", "2"),
 (13, "Dry the baby, keep skin-to-skin, delay the first bath 24 hours", "28 weeks to birth", V[3], "At birth; day 1-2; day 3", "About 20% fewer deaths from complications of preterm birth.", "2"),
 (14, "Put the baby to the breast within 1 hour; give colostrum; plan to breastfeed exclusively", "28 weeks to birth", V[3], "At birth (birth record)", "Not modelled separately from exclusive breastfeeding (behaviour 19).", "3"),
 (15, "Clean cord care: chlorhexidine, nothing else on the cord", "28 weeks to birth", V[3], "At birth; day 1-2; day 3; day 7", "About 23% fewer neonatal sepsis deaths.", "2"),
 (16, "Know newborn danger signs and seek care the same day", "28 weeks to birth, repeated in week 1", V[3], "Day 1-2; day 3; day 7 (danger-sign check); referrals that reach the facility", "Not modelled (care-seeking for newborn illness is not in the model).", "2"),
 (17, "Know danger signs for the mother after birth", "28 weeks to birth", V[3], "Day 1-2; day 3; day 7; 6 weeks", "Not modelled; maternal deaths are not in the model.", "2"),
 (18, "Mother and baby checked by a health worker within 48 hours", "28 weeks to birth", V[4], "Day 3", NM, "2"),
 "C. Birth to 6 weeks",
 (19, "Give only breast milk: no water, tea, porridge or other milk", "Late pregnancy; every visit to 6 months", V[3], "Day 1-2; day 3; day 7; 6 weeks; 14 weeks", EBF, "3"),
 (20, "Kangaroo care day and night for a small or early baby", "At birth, for small babies", V[3], "Day 1-2; day 3; day 7", "About 30% fewer deaths from complications of preterm birth.", "2"),
 (21, "Take the baby for BCG and polio at birth, then vaccines at 6, 10 and 14 weeks", "Late pregnancy; weeks 1 to 5", V[5] + " (birth doses); visits 6 and 7 (later doses)", "Day 7; 6 weeks; 14 weeks (card)", "Rotavirus vaccine: about 14% fewer diarrhoea deaths. The other vaccines in this row are not modelled.", "5"),
 (22, "Baby sleeps under a treated net every night, in malaria-endemic areas", "From birth", V[5], "Day 7; 14 weeks; 6, 9 and 18 months", "About 55% fewer malaria deaths at 1-23 months.", "5"),
 (23, "Start a modern family planning method by 6 weeks", "Late pregnancy; weeks 1 to 6", V[6], "6 weeks; 14 weeks; 6, 9 and 18 months", NM, "7"),
 "D. 6 weeks to 5 months",
 (24, "Know child danger signs and seek care the same day", "Weeks 4 to 10, then repeated", V[6], "6 weeks onward (danger-sign check); referrals that reach the facility", "Not modelled directly; leads to the care in behaviours 25 to 27.", "4"),
 (25, "Give ORS and zinc for diarrhoea; keep feeding", "Weeks 6 to 14", V[7], "6 weeks onward, whenever diarrhoea in the last 2 weeks is reported", "ORS: about 93% fewer diarrhoea deaths. Zinc: about 23% fewer.", "4"),
 (26, "Take a child with cough and fast or difficult breathing to a health worker", "Weeks 6 to 14", V[7], "6 weeks onward, whenever reported", "About 70% fewer pneumonia deaths.", "4"),
 (27, "Have a child with fever tested for malaria the same or next day, in malaria-endemic areas", "Weeks 6 to 14", V[7], "6 weeks onward, whenever fever is reported", "Not modelled (malaria treatment is not in the model).", "4"),
 (28, "Continue only breast milk until 6 months", "Weeks 6 to 24", V[7], "6 weeks; 14 weeks", EBF, "3"),
 (29, "Start soft foods at 6 months, not before; give food of the proper consistency", "Months 4 to 6", V[8], "6 months", NM, "8"),
 (30, "Bring the child for vitamin A at 6 months, then every 6 months", "Months 4 to 6", V[9] + "; again before visit 10", "9 months; 18 months (card)", "About 7% fewer diarrhoea deaths at 6-23 months.", "5"),
 "E. 6 to 17 months",
 (31, "Feed at least 5 of 8 food groups each day; right amount and frequency for age", "Months 6 to 9, repeated to 18", V[9] + "; again before visit 10", "9 months; 18 months (food groups yesterday); MUAC at 6, 9, 18 months", NM, "8"),
 (32, "Continue breastfeeding to 24 months", "Months 6 to 18", V[9] + "; again before visit 10", "9 months; 18 months", NM, "8"),
 (33, "Take the child for measles-rubella at 9 and 18 months", "Months 7 to 9; months 16 to 18", V[9] + " (first dose); " + V[10] + " (second dose)", "9 months; 18 months (card)", "About 85% fewer measles deaths (first dose).", "5"),
 (34, "Keep the handwashing place and latrine in use; put child faeces in the latrine", "Months 4 to 6, then repeated to 18", V[8] + "; again before visits 9 and 10", "6, 9 and 18 months (handwashing place and latrine at 6 and 18 months; child's last stool at all three)", "Handwashing as in behaviour 8. Latrine use and stool disposal are not modelled.", "6"),
]
BLOCKS = [("1", "Healthy pregnancy", "Antenatal care, iron-folic acid, tetanus doses, HIV test, diet, danger signs in pregnancy", "1-4, 6, 7"),
 ("2", "Birth and the first week", "Birth plan, facility delivery, drying and skin-to-skin, cord care, kangaroo care, newborn and maternal danger signs, check within 48 hours", "11-13, 15-18, 20"),
 ("3", "Breastfeeding", "Breast within 1 hour, only breast milk to 6 months", "14, 19, 28"),
 ("4", "When a child is sick", "Danger signs, ORS and zinc, care for fast breathing, malaria test for fever", "24-27"),
 ("5", "Preventing illness", "Vaccines on time, vitamin A, treated nets", "5, 21, 22, 30, 33"),
 ("6", "Water, sanitation and hygiene", "Handwashing place with soap, safe water, latrine, child faeces into the latrine", "8-10, 34"),
 ("7", "Family planning", "Method started by 6 weeks; spacing of at least 2 years", "23"),
 ("8", "Feeding from 6 months", "Soft foods of the proper consistency at 6 months, food groups, continued breastfeeding", "29, 31, 32")]
SETS = [("Pregnancy, up to month 7", "Visit 1 · pregnancy visit 1", "Enrolment to 31 weeks of pregnancy"), ("Pregnancy, months 8-9", "Visit 2 · pregnancy visit 2", "32 weeks to birth"),
 ("At birth", "Recorded once, when the birth is reported", "At birth"), ("Day 1-2", "Visit 3", "Days 0 to 2 of the child's life"), ("Day 3", "Visit 4", "Days 3 to 5"), ("Day 7", "Visit 5", "Days 6 to 27"),
 ("6 weeks", "Visit 6", "4 to 9 weeks"), ("14 weeks", "Visit 7", "10 weeks to 5 months"), ("6 months", "Visit 8", "6 to 8 months"), ("9 months", "Visit 9", "9 to 17 months"), ("18 months", "Visit 10", "18 to 23 months")]
# items = the most questions the visit can contain (all three illnesses reported); minutes are estimates, not field timings
TIME = [("1 · Pregnancy visit 1", "13", "8", "12-13"), ("2 · Pregnancy visit 2", "11", "8", "12-13"), ("3 · Day 1-2", "8", "7", "11-12"), ("4 · Day 3", "6", "4", "8-9"), ("5 · Day 7", "7", "6", "10"),
 ("6 · 6 weeks", "8", "6", "10-11"), ("7 · 14 weeks", "8", "5", "9-10"), ("8 · 6 months", "13", "8", "12"), ("9 · 9 months", "12", "8", "12-13"), ("10 · 18 months", "14", "9", "13")]

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
               "so a behaviour that is first measured at visit 1 shows the next CHW visit that measures it. <b>Survival impact</b> is the proportional reduction in deaths from the named cause among children "
               "who move from not receiving to receiving the behaviour, as used in the app's lives-saved model. 'Not modelled' means the app's simplified model leaves the behaviour out; it does not mean the behaviour has no effect.", P)]
rows, secs = [], []
for r in ROWS:
    if isinstance(r, str):
        secs.append(len(rows) + 1); rows.append([Paragraph(r, SEC)] + [""] * 5)
    else:
        rows.append([Paragraph(str(r[0]), C), Paragraph(r[1], C), Paragraph(r[2], C), Paragraph(r[3], CB), Paragraph(r[4], C), Paragraph(r[5], C), Paragraph(r[6], C)])
S.append(table(["#", "Behaviour to promote", "Promote during", "Promote prior to CHW visit # / child age", "Measured at (month of pregnancy or age of child)", "Survival impact", "Lesson block"], rows,
               [W * x for x in (.025, .205, .125, .15, .2, .245, .05)], secs))
S += [Paragraph("Suggested lesson blocks for CGVs", H2),
      Paragraph("A Care Group meets as one group, but its households are at different stages: some women are pregnant while others have a child of 18 months. The table above therefore cannot be followed "
                "as a single calendar. Two things together cover it. First, the group lessons run in the block order below, which places the periods with the most deaths first (pregnancy, birth and the "
                "first week, then breastfeeding and care of the sick child). Second, at each fortnightly home visit the volunteer repeats the behaviours for that household's own stage, using the "
                "'Promote during' and 'Promote prior to CHW visit' columns. Training is provided to volunteers on how to promote all the main behaviours on schedule, according to each household's stage. "
                "The block order is a proposal for discussion.", P),
      table(["Block", "Theme", "Content", "Behaviours"], [[Paragraph(x, C) for x in b] for b in BLOCKS], [W * x for x in (.06, .2, .58, .16)]),
      Paragraph("When each question set is asked", H2),
      Paragraph("The CHW asks a question set once, at her scheduled visit. The Care Group Volunteer asks the same set at every fortnightly visit while the woman or child is in the matching stage, "
                "so most behaviours are measured several times. Each volunteer range runs from one CHW visit to the next, which is why the 9-month set is asked from 9 to 17 months. "
                "The CHW visits at 9 and 18 months coincide with the two measles-rubella doses, and vitamin A is checked at both.", P),
      table(["Question set", "Asked by the CHW at", "Asked by the Care Group Volunteer every 2 weeks while the woman or child is at"], [[Paragraph(x, C) for x in b] for b in SETS], [W * x for x in (.2, .35, .45)]),
      Paragraph("Does it fit in a 15-minute CHW visit?", H2),
      Paragraph("The table gives the largest number of items each CHW visit can contain and an estimate of the time needed. The estimates assume 20 seconds for a yes-or-no question, 1 minute for a measurement, "
                "a danger-sign list or the vaccination card, and 1.5 minutes of counselling on each behaviour the family is not practising. They have not been timed in the field. "
                "Every visit fits within 15 minutes when up to 3 behaviours need counselling. Where more than 3 are missing, the CHW counsels on the 3 with the largest survival impact and "
                "the volunteer covers the rest at her fortnightly visits.", P),
      table(["CHW visit", "Items (most)", "Minutes to ask and measure", "Minutes with counselling on 3 behaviours"], [[Paragraph(x, C) for x in b] for b in TIME], [W * x for x in (.25, .15, .25, .35)]),
      Spacer(1, 6),
      Paragraph("Notes. (1) Birth plan: WHO lists education on birth preparedness and complication readiness at every antenatal contact throughout pregnancy, and birth and emergency preparedness counselling "
                "from the third contact (third trimester). Promotion therefore starts at enrolment. "
                "(2) Illness behaviours 25 to 27 are measured only in households that report the illness in the last 2 weeks, so their denominators are small in any one Care Group. "
                "(3) Behaviours 5, 22 and 27 apply in malaria-endemic areas. The app has a switch for this in Settings; when it is off, the questions on nets and malaria testing are not asked. "
                "Treated nets protect mainly against mosquitoes that bite at night, which carry malaria. The mosquitoes that carry dengue and chikungunya bite mainly by day, so nets give little protection against them "
                "except for people who sleep in the daytime, such as infants. "
                "(4) The malaria vaccine and the yellow fever vaccine are each switched on or off in Settings for the area. "
                "(5) Survival-impact figures use the Kenya settings of the model and are the same in the Ghana settings.", P)]
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
