"""
Convince Me That — PDF Generator
Flask web app. Receives form data, generates PDF in memory, returns download.
"""

from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
import re

app = Flask(__name__)

# ── Sanitize input — strip anything that could break PDF rendering ────────────
def clean(text, max_len=200):
    text = text.strip()[:max_len]
    # Remove control characters but keep standard punctuation
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text or "[ not provided ]"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Pull and sanitize form values
    prompt     = clean(request.form.get("prompt", ""), max_len=300)
    text_title = clean(request.form.get("text_title", ""), max_len=100)
    grade      = clean(request.form.get("grade", "4"), max_len=2)
    domain     = clean(request.form.get("domain", "ELA"), max_len=30)

    # Validate grade is a number 1-12
    if not grade.isdigit() or not (1 <= int(grade) <= 12):
        grade = "4"

    # Generate PDF in memory
    try:
        pdf_bytes = build_pdf(prompt, text_title, grade, domain)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Build a safe filename
    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', text_title)[:40]
    filename = f"CMT_{safe_title}_Grade{grade}.pdf"

    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION  (cmt_v4.py logic, adapted for in-memory output)
# ══════════════════════════════════════════════════════════════════════════════
def build_pdf(PROMPT, TEXT_TITLE, GRADE, DOMAIN):
    """Generate the CMT packet and return raw PDF bytes."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    W, H = letter
    M = 0.35 * inch

    # ── Palette ───────────────────────────────────────────────────────────────
    NAVY       = colors.HexColor("#1B3A5C")
    TEAL       = colors.HexColor("#1A6B6B")
    GOLD_DARK  = colors.HexColor("#9A6800")
    GOLD_BG    = colors.HexColor("#FDF3DC")
    GOLD_LINE  = colors.HexColor("#E8A820")
    CORAL      = colors.HexColor("#B83A1A")
    CORAL_BG   = colors.HexColor("#FDEAE5")
    SAGE       = colors.HexColor("#35603F")
    SAGE_BG    = colors.HexColor("#E6F2EA")
    LAV        = colors.HexColor("#4E4080")
    LAV_BG     = colors.HexColor("#EDE9F5")
    TEAL_BG    = colors.HexColor("#DFF0F0")
    CREAM      = colors.HexColor("#FDF8F2")
    LGRAY      = colors.HexColor("#EFEFEB")
    MGRAY      = colors.HexColor("#606060")
    DARK       = colors.HexColor("#1A1A1A")
    WHITE      = colors.white

    ROLES = [
        ("Claim Maker",       "C", CORAL, CORAL_BG),
        ("Text Hunter",       "T", TEAL,  TEAL_BG),
        ("Opposition Finder", "O", LAV,   LAV_BG),
        ("Final Word Author", "F", SAGE,  SAGE_BG),
    ]

    # ── Helpers ───────────────────────────────────────────────────────────────
    def rr(c, x, y, w, h, r=6, fill=None, stroke=None, sw=1):
        if fill:   c.setFillColor(fill)
        if stroke: c.setStrokeColor(stroke); c.setLineWidth(sw)
        c.roundRect(x, y, w, h, r,
                    stroke=1 if stroke else 0,
                    fill=1 if fill else 0)

    def t(c, text, x, y, font="Helvetica", size=10, color=DARK, align="left"):
        c.setFont(font, size); c.setFillColor(color)
        {"left":   c.drawString,
         "center": lambda x,y,s: c.drawCentredString(x,y,s),
         "right":  lambda x,y,s: c.drawRightString(x,y,s)
        }[align](x, y, text)

    def wrap_lines(c, text, x, y, max_w, font="Helvetica", size=10,
                   color=DARK, leading=14):
        c.setFont(font, size); c.setFillColor(color)
        words = text.split(); line = ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, font, size) <= max_w: line = test
            else:
                if line: c.drawString(x, y, line)
                y -= leading; line = word
        if line: c.drawString(x, y, line)
        return y - leading

    def hlines(c, x, y, w, n, gap, color=colors.HexColor("#C8C4BC")):
        c.setStrokeColor(color); c.setLineWidth(0.5)
        for i in range(n):
            c.line(x, y - i*gap, x+w, y - i*gap)
        return y - n*gap

    def chrome(c, page, total, section):
        c.setFillColor(NAVY)
        c.rect(0, H-0.38*inch, W, 0.38*inch, fill=1, stroke=0)
        t(c, f"CONVINCE ME THAT  \u2022  {DOMAIN.upper()} EVIDENCE & ARGUMENT",
          0.25*inch, H-0.25*inch, font="Helvetica-Bold", size=8, color=WHITE)
        t(c, f"{section}   |   Page {page} of 6",
          W-0.25*inch, H-0.25*inch, font="Helvetica", size=8,
          color=colors.HexColor("#9BBFCC"), align="right")
        c.setFillColor(GOLD_LINE)
        c.rect(0, H-0.41*inch, W, 0.04*inch, fill=1, stroke=0)
        c.setFillColor(LGRAY)
        c.rect(0, 0, W, 0.3*inch, fill=1, stroke=0)
        t(c, f"Grade {GRADE} {DOMAIN}  \u2022  {TEXT_TITLE}",
          0.25*inch, 0.1*inch, font="Helvetica", size=7.5, color=MGRAY)
        t(c, f"Convince Me That \u2014 {DOMAIN} Evidence & Argument",
          W-0.25*inch, 0.1*inch, font="Helvetica", size=7.5,
          color=MGRAY, align="right")

    # ── Write to memory buffer ─────────────────────────────────────────────────
    buf = BytesIO()
    cv = canvas.Canvas(buf, pagesize=letter)

    # ── Page 1: Cover ─────────────────────────────────────────────────────────
    inner_w = W - 2*M
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    cv.setFillColor(NAVY); cv.rect(0,H-1.45*inch,W,1.45*inch,fill=1,stroke=0)
    cv.setFillColor(GOLD_LINE); cv.rect(0,H-1.49*inch,W,0.05*inch,fill=1,stroke=0)
    t(cv,f"EVIDENCE & ARGUMENT  \u2022  SMALL GROUP  \u2022  {DOMAIN.upper()}",
      0.4*inch,H-0.4*inch,font="Helvetica-Bold",size=9,color=GOLD_LINE)
    t(cv,"Convince Me That\u2026",0.4*inch,H-0.88*inch,
      font="Helvetica-Bold",size=34,color=WHITE)
    t(cv,f"Text: {TEXT_TITLE}",0.4*inch,H-1.25*inch,
      font="Helvetica",size=9.5,color=colors.HexColor("#8AAEBD"))

    pb_top = H-1.6*inch
    words=PROMPT.split(); out_lines=[]; cur=""
    max_pw=inner_w-0.38*inch
    for w in words:
        test=(cur+" "+w).strip()
        if cv.stringWidth(test,"Helvetica-Bold",15)<=max_pw: cur=test
        else: out_lines.append(cur); cur=w
    if cur: out_lines.append(cur)
    pb_h=max(0.9*inch,0.38*inch+len(out_lines)*0.26*inch+0.12*inch)
    rr(cv,M,pb_top-pb_h,inner_w,pb_h,r=10,fill=GOLD_BG,stroke=GOLD_LINE,sw=2.5)
    t(cv,"CONVINCE ME THAT:",M+0.18*inch,pb_top-0.22*inch,
      font="Helvetica-Bold",size=8.5,color=GOLD_DARK)
    py=pb_top-0.48*inch
    for ol in out_lines:
        t(cv,ol,M+0.18*inch,py,font="Helvetica-Bold",size=15,color=NAVY); py-=0.26*inch

    ny=pb_top-pb_h-0.28*inch
    t(cv,"Names & Roles:",M,ny,font="Helvetica-Bold",size=10,color=NAVY)
    ROW_GAP=0.42*inch; col_w=inner_w/2-0.1*inch
    for i,(role,_,accent,_) in enumerate(ROLES):
        col=M if i%2==0 else M+inner_w/2; ry=ny-(i//2+1)*ROW_GAP
        cv.setFillColor(accent); cv.circle(col+0.1*inch,ry+0.08*inch,0.07*inch,fill=1,stroke=0)
        t(cv,role,col+0.26*inch,ry+0.02*inch,font="Helvetica-Bold",size=8.5,color=accent)
        lx=col+0.26*inch+cv.stringWidth(role,"Helvetica-Bold",8.5)+5
        cv.setStrokeColor(colors.HexColor("#AAAAAA")); cv.setLineWidth(0.6)
        cv.line(lx,ry,col+col_w,ry)

    date_y=ny-2*ROW_GAP-0.38*inch
    t(cv,"Date:",M,date_y,font="Helvetica-Bold",size=10,color=NAVY)
    cv.setStrokeColor(colors.HexColor("#AAAAAA")); cv.setLineWidth(0.6)
    cv.line(M+0.55*inch,date_y,M+2.5*inch,date_y)

    hw_top=date_y-0.32*inch; hw_h=1.42*inch
    rr(cv,M,hw_top-hw_h,inner_w,hw_h,r=8,fill=TEAL_BG,stroke=TEAL,sw=1.5)
    t(cv,"How This Works",M+0.18*inch,hw_top-0.18*inch,font="Helvetica-Bold",size=11,color=TEAL)
    steps=["1.  Think First (Page 2) \u2014 respond on your own before any discussion.",
           "2.  Take a Role (Page 3) \u2014 each teammate completes their role card independently.",
           "3.  Discuss (Page 4) \u2014 share role cards and build the argument together.",
           "4.  Write Together (Page 5) \u2014 compose your team\u2019s final response."]
    sy=hw_top-0.44*inch
    for s in steps:
        wrap_lines(cv,s,M+0.22*inch,sy,inner_w-0.44*inch,font="Helvetica",size=9,color=DARK,leading=13)
        sy-=0.27*inch

    rl_top=hw_top-hw_h-0.18*inch; rl_h=0.6*inch
    rr(cv,M,rl_top-rl_h,inner_w,rl_h,r=8,fill=NAVY)
    t(cv,"The Four Roles:",M+0.18*inch,rl_top-0.2*inch,font="Helvetica-Bold",size=9.5,color=WHITE)
    label_end=M+0.18*inch+cv.stringWidth("The Four Roles:","Helvetica-Bold",9.5)+0.18*inch
    badges_w=W-M-label_end-0.1*inch; badge_w=(badges_w-3*0.06*inch)/4
    for i,(role,_,accent,_) in enumerate(ROLES):
        bx=label_end+i*(badge_w+0.06*inch)
        rr(cv,bx,rl_top-rl_h+0.1*inch,badge_w,0.4*inch,r=6,fill=accent)
        t(cv,role,bx+badge_w/2,rl_top-rl_h+0.24*inch,font="Helvetica-Bold",size=7.5,color=WHITE,align="center")

    gl_top=rl_top-rl_h-0.18*inch; gl_h=0.52*inch
    rr(cv,M,gl_top-gl_h,inner_w,gl_h,r=6,fill=GOLD_BG,stroke=GOLD_LINE,sw=1)
    t(cv,"\u201cYour goal: don\u2019t just find the answer \u2014 build the argument.\u201d",
      W/2,gl_top-gl_h/2-0.07*inch,font="Helvetica-BoldOblique",size=10.5,color=GOLD_DARK,align="center")
    cv.showPage()

    # ── Page 2: Think First ───────────────────────────────────────────────────
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    chrome(cv,2,6,"Think First")
    top=H-0.52*inch
    rr(cv,M,top-0.82*inch,inner_w,0.82*inch,r=8,fill=NAVY)
    t(cv,"Step 1: Think First \u2014 On Your Own",M+0.18*inch,top-0.28*inch,
      font="Helvetica-Bold",size=14,color=WHITE)
    t(cv,"Before you talk to anyone, write your own response. Every voice matters.",
      M+0.18*inch,top-0.54*inch,font="Helvetica",size=9.5,color=colors.HexColor("#8AAEBD"))
    pr_top=top-0.98*inch; pr_h=0.62*inch
    rr(cv,M,pr_top-pr_h,inner_w,pr_h,r=6,fill=GOLD_BG,stroke=GOLD_LINE,sw=1.5)
    t(cv,"Convince me that:",M+0.18*inch,pr_top-0.18*inch,font="Helvetica-Bold",size=8.5,color=GOLD_DARK)
    wrap_lines(cv,PROMPT,M+0.18*inch,pr_top-0.36*inch,inner_w-0.36*inch,
               font="Helvetica-Bold",size=10.5,color=NAVY,leading=14)
    tb_top=pr_top-pr_h-0.1*inch; tb_h=0.3*inch
    rr(cv,M,tb_top-tb_h,inner_w,tb_h,r=5,fill=TEAL_BG,stroke=TEAL,sw=1)
    t(cv,"You have about 3 minutes. Write what YOU think \u2014 no wrong answers here.",
      W/2,tb_top-tb_h/2-0.055*inch,font="Helvetica-Oblique",size=9,color=TEAL,align="center")
    rb_top=tb_top-tb_h-0.14*inch; rb_h=3.2*inch
    rr(cv,M,rb_top-rb_h,inner_w,rb_h,r=8,fill=WHITE,stroke=NAVY,sw=1.5)
    t(cv,"My response:",M+0.18*inch,rb_top-0.22*inch,font="Helvetica-Bold",size=10,color=NAVY)
    hlines(cv,M+0.18*inch,rb_top-0.45*inch,inner_w-0.36*inch,n=11,gap=0.25*inch)
    st_top=rb_top-rb_h-0.22*inch
    t(cv,"Thinking Stems \u2014 choose one to get started:",M,st_top,font="Helvetica-Bold",size=10,color=NAVY)
    stems=[("I believe this is true because\u2026",CORAL_BG,CORAL),
           ("Evidence from the text that supports this\u2026",TEAL_BG,TEAL),
           ("Someone might disagree by saying\u2026 but I think\u2026",LAV_BG,LAV),
           ("A question I still have is\u2026",SAGE_BG,SAGE)]
    sw2=inner_w/2-0.06*inch; sh=0.52*inch; sgap=0.08*inch
    for i,(stem,bg,accent) in enumerate(stems):
        sx=M if i%2==0 else M+inner_w/2+0.06*inch
        sy=st_top-0.26*inch-(i//2)*(sh+sgap)
        rr(cv,sx,sy-sh,sw2,sh,r=6,fill=bg,stroke=accent,sw=1)
        wrap_lines(cv,stem,sx+0.14*inch,sy-0.16*inch,sw2-0.28*inch,
                   font="Helvetica-Oblique",size=9.5,color=accent,leading=13)
    tr_top=st_top-0.26*inch-2*(sh+sgap)-0.14*inch; tr_h=0.42*inch
    rr(cv,M,tr_top-tr_h,inner_w,tr_h,r=6,fill=LGRAY)
    t(cv,"When your teacher signals: flip to Page 3 and find your role card.",
      W/2,tr_top-tr_h/2-0.07*inch,font="Helvetica-Bold",size=9.5,color=NAVY,align="center")
    cv.showPage()

    # ── Page 3: Role Cards ────────────────────────────────────────────────────
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    chrome(cv,3,6,"Role Cards")
    top=H-0.52*inch
    t(cv,"Step 2: Take a Role",M,top,font="Helvetica-Bold",size=13,color=NAVY)
    t(cv,"Complete your role card independently before talking to your group.",
      M,top-0.22*inch,font="Helvetica",size=9.5,color=MGRAY)
    card_data=[
        ("Claim Maker","Write a clear, bold statement that directly answers the prompt.",
         ["What does your team believe? State it directly.",
          "Take a firm stand \u2014 no hedging.",
          "Use strong, confident language."],
         "The ___ was right/wrong to ___ because ___."),
        ("Text Hunter","Find the strongest evidence from the text that proves the claim.",
         ["Reread closely. Look for exact quotes or key details.",
          "Choose your single BEST piece of evidence.",
          "Think: how does this specifically prove the claim?"],
         'In the story, it says "\u2014," which shows ___.'),
        ("Opposition Finder","Find the strongest argument AGAINST your team\u2019s position.",
         ["Think like someone who completely disagrees.",
          "Make their argument as powerful as possible.",
          "A great team understands \u2014 and answers \u2014 both sides."],
         "Someone might argue that ___ because ___."),
        ("Final Word Author","After hearing all roles, write the most powerful version of the claim.",
         ["Listen carefully before you write \u2014 don\u2019t rush.",
          "Restate the claim more powerfully \u2014 OR \u2014",
          "Ask a question that makes the reader keep thinking."],
         "This proves that ___.  OR:  What if ___?"),
    ]
    cw=inner_w/2-0.05*inch; cgap=0.1*inch
    card_top=top-0.38*inch; card_bot=0.38*inch
    ch=(card_top-card_bot-cgap)/2
    positions=[(M,card_top-ch),(M+cw+cgap,card_top-ch),
               (M,card_top-2*ch-cgap),(M+cw+cgap,card_top-2*ch-cgap)]
    for (role,desc,steps,starter),(_,icon,accent,bg) in zip(card_data,ROLES):
        cx,cy=positions[card_data.index((role,desc,steps,starter))]
        rr(cv,cx,cy,cw,ch,r=9,fill=bg,stroke=accent,sw=2)
        hh=0.62*inch
        cv.setFillColor(accent); cv.roundRect(cx,cy+ch-hh,cw,hh,9,fill=1,stroke=0)
        cv.rect(cx,cy+ch-hh,cw,hh/2,fill=1,stroke=0)
        cv.setFillColor(WHITE); cv.circle(cx+0.32*inch,cy+ch-hh/2,0.19*inch,fill=1,stroke=0)
        t(cv,icon,cx+0.32*inch,cy+ch-hh/2-0.07*inch,font="Helvetica-Bold",size=13,color=accent,align="center")
        t(cv,role,cx+0.62*inch,cy+ch-hh/2+0.05*inch,font="Helvetica-Bold",size=12,color=WHITE)
        t(cv,desc,cx+0.15*inch,cy+ch-hh-0.22*inch,font="Helvetica-Oblique",size=8.5,color=accent)
        t(cv,"Your job:",cx+0.15*inch,cy+ch-hh-0.44*inch,font="Helvetica-Bold",size=8.5,color=DARK)
        sy2=cy+ch-hh-0.65*inch
        for step in steps:
            wrap_lines(cv,f"\u2022  {step}",cx+0.2*inch,sy2,cw-0.38*inch,
                       font="Helvetica",size=8.5,color=DARK,leading=12); sy2-=0.19*inch
        sb_y=cy+1.02*inch
        rr(cv,cx+0.12*inch,sb_y-0.06*inch,cw-0.24*inch,0.34*inch,r=4,fill=accent)
        t(cv,"STARTER (optional):",cx+0.2*inch,sb_y+0.16*inch,font="Helvetica-Bold",size=7.5,color=WHITE)
        t(cv,starter,cx+0.2*inch,sb_y+0.03*inch,font="Helvetica-Oblique",size=7.5,color=WHITE)
        wb_y=cy+0.08*inch; wb_h=0.88*inch
        rr(cv,cx+0.12*inch,wb_y,cw-0.24*inch,wb_h,r=4,fill=WHITE,stroke=accent,sw=1)
        t(cv,"MY RESPONSE:",cx+0.2*inch,wb_y+wb_h-0.18*inch,font="Helvetica-Bold",size=8,color=accent)
        hlines(cv,cx+0.2*inch,wb_y+wb_h-0.34*inch,cw-0.44*inch,n=3,gap=0.2*inch)
    cv.showPage()

    # ── Page 4: Discussion ────────────────────────────────────────────────────
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    chrome(cv,4,6,"Team Discussion")
    top=H-0.52*inch
    rr(cv,M,top-0.82*inch,inner_w,0.82*inch,r=8,fill=NAVY)
    t(cv,"Step 3: Discuss Before You Write",M+0.18*inch,top-0.28*inch,
      font="Helvetica-Bold",size=14,color=WHITE)
    t(cv,"Share role cards. Use this protocol to build the strongest possible argument.",
      M+0.18*inch,top-0.54*inch,font="Helvetica",size=9.5,color=colors.HexColor("#8AAEBD"))
    protocol=[
        ("1","Share",CORAL,CORAL_BG,
         "Each person reads their role card aloud. No interrupting. Everyone listens fully.",
         "What was the most surprising thing someone said?"),
        ("2","Probe the Evidence",TEAL,TEAL_BG,
         "Text Hunter reads the quote again. Team: Does this actually prove the claim? How exactly?",
         "Is there stronger evidence we might have missed?"),
        ("3","Steel-Man the Opposition",LAV,LAV_BG,
         "Opposition Finder: make the counter-argument as strong as you can. Team: how do we beat it?",
         "What would it take to make someone change their mind?"),
        ("4","Lock the Argument",SAGE,SAGE_BG,
         "Final Word Author proposes the strongest version of the claim. Everyone must agree before writing.",
         "What is the single most important reason we are right?"),
    ]
    step_h=1.08*inch; sgap=0.08*inch; sy=top-0.98*inch
    for num,title,accent,bg,instruct,question in protocol:
        rr(cv,M,sy-step_h,inner_w,step_h,r=7,fill=bg,stroke=accent,sw=1.5)
        cv.setFillColor(accent); cv.circle(M+0.32*inch,sy-step_h/2,0.24*inch,fill=1,stroke=0)
        t(cv,num,M+0.32*inch,sy-step_h/2-0.085*inch,font="Helvetica-Bold",size=15,color=WHITE,align="center")
        t(cv,title,M+0.72*inch,sy-0.22*inch,font="Helvetica-Bold",size=11.5,color=accent)
        wrap_lines(cv,instruct,M+0.72*inch,sy-0.43*inch,inner_w-0.9*inch,
                   font="Helvetica",size=9,color=DARK,leading=13)
        ab_h=0.3*inch; ab_y=sy-step_h+0.1*inch
        rr(cv,M+0.72*inch,ab_y,inner_w-0.9*inch,ab_h,r=4,fill=WHITE,stroke=accent,sw=0.75)
        aw=cv.stringWidth("Anchor: ","Helvetica-Bold",8)
        t(cv,"Anchor: ",M+0.82*inch,ab_y+ab_h/2-0.04*inch,font="Helvetica-Bold",size=8,color=accent)
        t(cv,question,M+0.82*inch+aw,ab_y+ab_h/2-0.04*inch,font="Helvetica-Oblique",size=8.5,color=DARK)
        sy-=step_h+sgap
    nb_top=sy-0.12*inch; nb_bot=0.38*inch; nb_h=nb_top-nb_bot
    rr(cv,M,nb_bot,inner_w,nb_h,r=7,fill=WHITE,stroke=NAVY,sw=1.5)
    t(cv,"Discussion Notes \u2014 jot anything important here:",M+0.18*inch,nb_top-0.2*inch,
      font="Helvetica-Bold",size=10,color=NAVY)
    hlines(cv,M+0.18*inch,nb_top-0.4*inch,inner_w-0.36*inch,
           n=int((nb_h-0.5*inch)//(0.28*inch)),gap=0.28*inch)
    cv.showPage()

    # ── Page 5: Team Assembly ─────────────────────────────────────────────────
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    chrome(cv,5,6,"Team Response")
    top=H-0.52*inch
    t(cv,"Step 4: Write Your Argument Together",M,top,font="Helvetica-Bold",size=13,color=NAVY)
    t(cv,"Use your discussion to build the strongest possible written response.",
      M,top-0.22*inch,font="Helvetica",size=9.5,color=MGRAY)
    sections=[
        ("C","Claim",CORAL,CORAL_BG,
         "State your position clearly and directly. What does your team believe \u2014 and why?",
         "The ___ was right/wrong to ___ because ___."),
        ("E","Evidence",TEAL,TEAL_BG,
         "Include your strongest quote or detail from the text. Explain exactly what it proves.",
         'In the text, it says "\u2014." This shows ___ because ___.'),
        ("R","Rebuttal",LAV,LAV_BG,
         "Acknowledge the other side \u2014 then explain clearly why your argument wins anyway.",
         "Some might argue ___. However, ___ because ___."),
        ("C","Conclusion",SAGE,SAGE_BG,
         "Restate your claim powerfully, OR leave the reader with a question that demands an answer.",
         "This proves ___.   OR:   What might have happened if ___?"),
    ]
    used_top=0.52*inch+0.42*inch; used_bot=0.38*inch
    avail=H-used_top-used_bot-0.38*inch
    n_sec=len(sections); sec_gap=0.07*inch
    sec_h=(avail-(n_sec-1)*sec_gap)/n_sec; sy=top-0.38*inch
    for badge_ltr,label,accent,bg,instruct,starter in sections:
        rr(cv,M,sy-sec_h,inner_w,sec_h,r=7,fill=bg,stroke=accent,sw=1.5)
        badge_w=0.48*inch
        cv.setFillColor(accent); cv.roundRect(M,sy-sec_h,badge_w,sec_h,7,fill=1,stroke=0)
        cv.rect(M+badge_w-8,sy-sec_h,8,sec_h,fill=1,stroke=0)
        t(cv,badge_ltr,M+badge_w/2,sy-sec_h/2-0.09*inch,
          font="Helvetica-Bold",size=20,color=WHITE,align="center")
        content_x=M+badge_w+0.16*inch; content_w=inner_w-badge_w-0.2*inch
        t(cv,label,content_x,sy-0.24*inch,font="Helvetica-Bold",size=11.5,color=accent)
        wrap_lines(cv,instruct,content_x,sy-0.46*inch,content_w,
                   font="Helvetica",size=9,color=DARK,leading=13)
        t(cv,f"Starter: {starter}",content_x,sy-0.68*inch,
          font="Helvetica-Oblique",size=8.5,color=MGRAY)
        lines_top=sy-0.85*inch; lines_bot=sy-sec_h+0.12*inch
        n_lines=max(3,int((lines_top-lines_bot)/0.26*inch))
        hlines(cv,content_x,lines_top,content_w,n=n_lines,gap=0.26*inch)
        sy-=sec_h+sec_gap
    cv.showPage()

    # ── Page 6: Rubric ────────────────────────────────────────────────────────
    cv.setFillColor(CREAM); cv.rect(0,0,W,H,fill=1,stroke=0)
    chrome(cv,6,6,"Rubric & Reflection")
    top=H-0.52*inch
    rr(cv,M,top-0.82*inch,inner_w,0.82*inch,r=8,fill=NAVY)
    t(cv,"How Strong Is Our Argument?",M+0.18*inch,top-0.3*inch,
      font="Helvetica-Bold",size=16,color=GOLD_LINE)
    t(cv,"Score yourselves before submitting. Then your teacher will score it too.",
      M+0.18*inch,top-0.57*inch,font="Helvetica",size=9.5,color=WHITE)
    rubric=[
        ("4","Strong",SAGE,
         ["Clear, confident claim that directly answers the prompt",
          "Strong text evidence with a direct quote and clear explanation",
          "Counterargument acknowledged and effectively rebutted",
          "Conclusion is powerful \u2014 restates or provokes deeper thinking",
          "Writing is complete, organized, and uses full sentences"]),
        ("3","Proficient",TEAL,
         ["Clear claim that answers the prompt",
          "Relevant text evidence included and partially explained",
          "Some acknowledgment of the other side",
          "Writing is mostly clear and complete"]),
        ("2","Developing",colors.HexColor("#8A6000"),
         ["Claim is present but unclear or incomplete",
          "Evidence is vague, weak, or not explained",
          "Little or no counterargument; limited connection to text"]),
        ("1","Beginning",CORAL,
         ["Opinion stated but not supported",
          "Little or no text evidence",
          "Ideas are hard to follow"]),
        ("0","Not Yet",MGRAY,
         ["No claim, no evidence, off topic or incomplete"]),
    ]
    used=0.52*inch+0.82*inch+0.12*inch+1.3*inch+0.38*inch
    avail_rub=H-used; total_bullets=sum(len(b) for _,_,_,b in rubric)
    min_h=0.55*inch
    row_h=[max(avail_rub*len(b)/total_bullets,min_h) for _,_,_,b in rubric]
    scale=avail_rub/sum(row_h); row_h=[h*scale for h in row_h]
    ry=top-0.82*inch-0.12*inch; badge_w=0.78*inch
    for i,(score,label,accent,bullets) in enumerate(rubric):
        rh=row_h[i]
        rr(cv,M,ry-rh,inner_w,rh,r=6,fill=LGRAY,stroke=accent,sw=1.5)
        cv.setFillColor(accent); cv.roundRect(M,ry-rh,badge_w,rh,6,fill=1,stroke=0)
        cv.rect(M+badge_w-8,ry-rh,8,rh,fill=1,stroke=0)
        t(cv,score,M+badge_w/2,ry-rh/2-0.08*inch,font="Helvetica-Bold",size=24,color=WHITE,align="center")
        t(cv,label.upper(),M+badge_w/2,ry-rh+0.12*inch,font="Helvetica-Bold",size=7.5,color=WHITE,align="center")
        bx=M+badge_w+0.16*inch; by=ry-0.24*inch
        bullet_gap=min(0.21*inch,(rh-0.3*inch)/max(len(bullets),1))
        for b in bullets:
            t(cv,f"\u2713  {b}",bx,by,font="Helvetica",size=9,color=DARK); by-=bullet_gap
        ry-=rh+0.05*inch
    ref_top=ry-0.06*inch; ref_bot=0.38*inch; ref_h=ref_top-ref_bot
    rr(cv,M,ref_bot,inner_w,ref_h,r=7,fill=GOLD_BG,stroke=GOLD_LINE,sw=1.5)
    t(cv,"Reflection",M+0.18*inch,ref_top-0.2*inch,font="Helvetica-Bold",size=11,color=GOLD_DARK)
    sl_y=ref_top-0.44*inch
    t(cv,"Our team score:",M+0.18*inch,sl_y,font="Helvetica-Bold",size=9,color=DARK)
    sw1=cv.stringWidth("Our team score:","Helvetica-Bold",9)
    cv.setStrokeColor(colors.HexColor("#AAAAAA")); cv.setLineWidth(0.6)
    cv.line(M+0.18*inch+sw1+4,sl_y,M+0.18*inch+sw1+0.7*inch,sl_y)
    t(cv,"Teacher score:",M+2.5*inch,sl_y,font="Helvetica-Bold",size=9,color=DARK)
    sw2=cv.stringWidth("Teacher score:","Helvetica-Bold",9)
    cv.line(M+2.5*inch+sw2+4,sl_y,M+2.5*inch+sw2+0.7*inch,sl_y)
    rq_y=sl_y-0.28*inch
    t(cv,"What made this argument hard to prove?",M+0.18*inch,rq_y,
      font="Helvetica-Bold",size=9,color=DARK)
    n_ref_lines=max(2,int((rq_y-ref_bot-0.25*inch)/(0.27*inch)))
    hlines(cv,M+0.18*inch,rq_y-0.2*inch,inner_w-0.36*inch,n=n_ref_lines,gap=0.27*inch)
    cv.showPage()

    cv.save()
    return buf.getvalue()


if __name__ == "__main__":
    app.run(debug=True)
