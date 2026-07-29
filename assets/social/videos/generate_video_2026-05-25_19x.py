# -*- coding: utf-8 -*-
# Book Genesis flagship video — 2026-05-25
# Angle: "Pipeline beats prompt — the 19x gap (same model underneath)"
# Reuses the editorial PIL-slides + ffmpeg house style.
import sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont

LANG   = sys.argv[1] if len(sys.argv)>1 else 'en'   # 'pt' | 'en'
ORIENT = sys.argv[2] if len(sys.argv)>2 else 'v'    # 'v' | 'h'
OUT    = sys.argv[3] if len(sys.argv)>3 else 'out.mp4'
MAXSEC = float(sys.argv[4]) if len(sys.argv)>4 else 0

FPS = 30
if ORIENT=='v': W,H = 1080,1920
else:           W,H = 1920,1080
M = min(W,H)

BG=(244,235,217); INK=(35,28,22); INK_SOFT=(95,80,65); HAIR=(195,180,155)
ACCENT=(180,86,52); ACCENT_F=(210,145,115); PANEL=(250,245,234); GREEN=(72,110,72)

FD="/usr/share/fonts/truetype/dejavu/"
def F(path,sz): return ImageFont.truetype(FD+path,sz)
_cache={}
def font(kind,sz):
    k=(kind,sz)
    if k in _cache: return _cache[k]
    m={'serif':'DejaVuSerif.ttf','serifb':'DejaVuSerif-Bold.ttf','serifi':'DejaVuSerif-Italic.ttf',
       'mono':'DejaVuSansMono.ttf','monob':'DejaVuSansMono-Bold.ttf'}
    f=F(m[kind],sz); _cache[k]=f; return f

def lerp(a,b,t): return tuple(int(round(a[i]+(b[i]-a[i])*t)) for i in range(3))
def fade(col,a): a=max(0,min(1,a)); return lerp(BG,col,a)
def clamp(x,a,b): return a if x<a else b if x>b else x
def lin(t,a,b):
    if b<=a: return 1.0 if t>=b else 0.0
    return clamp((t-a)/(b-a),0,1)

def tw(d,t,f): return d.textlength(t,font=f)
def lineh(f,ls=1.0):
    a,de=f.getmetrics(); return (a+de)*ls
def wrap(d,text,f,maxw):
    out=[]
    for para in text.split("\n"):
        words=para.split(); cur=""
        for w in words:
            t=(cur+" "+w).strip()
            if tw(d,t,f)<=maxw: cur=t
            else:
                if cur: out.append(cur)
                cur=w
        out.append(cur)
    return out
def block(d,lines,f,cx,top,col,ls=1.12):
    lh=lineh(f,ls); y=top
    for ln in lines:
        d.text((cx-tw(d,ln,f)/2,y),ln,font=f,fill=col); y+=lh
    return y
def tracked(d,text,f,cx,y,col,tr):
    total=sum(tw(d,ch,f)+tr for ch in text)-tr
    x=cx-total/2
    for ch in text:
        d.text((x,y),ch,font=f,fill=col); x+=tw(d,ch,f)+tr
def rrect(d,box,r,fill=None,outline=None,wd=1):
    d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=wd)
def asterisk(d,x,y,sz,col):
    for k in range(6):
        ang=math.pi*k/6; dx=math.cos(ang)*sz; dy=math.sin(ang)*sz
        d.line([(x-dx,y-dy),(x+dx,y+dy)],fill=col,width=2)
    d.ellipse([x-3,y-3,x+3,y+3],fill=ACCENT)
def frame_base(label):
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)
    mg=int(M*0.028)
    d.rectangle([mg,mg,W-mg,H-mg],outline=HAIR,width=2)
    asterisk(d,mg+34,mg+34,13,INK)
    fm=font('mono',int(M*0.016))
    d.text((W-mg-tw(d,"MMXXVI",fm)-12,mg+22),"MMXXVI",font=fm,fill=INK_SOFT)
    if label:
        tracked(d,label,font('mono',int(M*0.0155)),W/2,mg+22,INK_SOFT,5)
    return img,d

# ---------------- strings ----------------
T = {
 'en':{
  'lab':["I · THE GAP","II · THE NUMBERS","III · THE REVEAL","IV · WHY","V · THE FIX","VI · THE LESSON",""],
  'hook1':"Same prompt.",'hook2':"Same model underneath.",'hook3':"So why a 19x gap?",
  'cmp_cap':"One brief. Two systems.",
  'cmpA_name':"PLAIN CHATGPT",'cmpA_v':"3,140",'cmpA_u':"words · 12 sec",
  'cmpB_name':"BOOK GENESIS",'cmpB_v':"60,800",'cmpB_u':"words · 4h 30",
  'cmp_sub':"Same Claude model powering both.",
  'rev1':"The model wasn't the difference.",'rev2':"The architecture was.",
  'why_cap':"One prompt = one call to do 8 jobs:",
  'why_list':"Plan · Characters · Theme · Tone\nProse · Pacing · Audit · Ending",
  'why_punch':"So the model does what models do:\nit averages.",
  'fix_cap':"The pipeline splits the work.",
  'fix_big':"15 skills · 8 phases",
  'fix1':"Each phase writes a durable artifact.",
  'fix2':"The next phase reads it from disk.",
  'fix3':"The model never holds the whole book\nin its head.",
  'lesson1':"Any AI task bigger than a tweet",
  'lesson2':"that needs coherence",
  'lesson3':"wins from decomposition.",
  'cta_pre':"BOOK GENESIS",
  'cta1':"Open source. Runs on any agent\nthat reads files.",
  'url':"github.com/felipelobomotta-blip/book-genesis-v4",
  'cta_sub':"MIT · Claude Code · Codex · Kimi · Antigravity",
 },
 'pt':{
  'lab':["I · O GAP","II · OS NÚMEROS","III · A VIRADA","IV · POR QUÊ","V · A SOLUÇÃO","VI · A LIÇÃO",""],
  'hook1':"Mesmo prompt.",'hook2':"Mesmo modelo por baixo.",'hook3':"Então por que 19x de diferença?",
  'cmp_cap':"Um brief. Dois sistemas.",
  'cmpA_name':"CHATGPT PURO",'cmpA_v':"3.140",'cmpA_u':"palavras · 12 seg",
  'cmpB_name':"BOOK GENESIS",'cmpB_v':"60.800",'cmpB_u':"palavras · 4h30",
  'cmp_sub':"O mesmo modelo Claude nos dois.",
  'rev1':"O modelo não era a diferença.",'rev2':"A arquitetura era.",
  'why_cap':"Um prompt = uma chamada pra fazer 8 coisas:",
  'why_list':"Plano · Personagens · Tema · Tom\nProsa · Pacing · Auditoria · Final",
  'why_punch':"Aí o modelo faz o que modelo faz:\ntira média.",
  'fix_cap':"O pipeline divide o trabalho.",
  'fix_big':"15 skills · 8 fases",
  'fix1':"Cada fase escreve um artefato durável.",
  'fix2':"A próxima fase lê do disco.",
  'fix3':"O modelo nunca segura o livro inteiro\nna cabeça.",
  'lesson1':"Toda tarefa de IA maior que um tweet",
  'lesson2':"que precisa de coerência",
  'lesson3':"ganha com decomposição.",
  'cta_pre':"BOOK GENESIS",
  'cta1':"Open source. Roda em qualquer agente\nque lê arquivo.",
  'url':"github.com/felipelobomotta-blip/book-genesis-v4",
  'cta_sub':"MIT · Claude Code · Codex · Kimi · Antigravity",
 }
}
L=T[LANG]
CW = W-2*int(M*0.10)
CX = W/2

# ===================== SCENES =====================
def sc_hook(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    f=font('serifb',int(M*0.092))
    y=H*0.26
    y=block(d,wrap(d,L['hook1'],f,CW),f,CX,y,fade(INK,lin(t,0.1,0.6)),1.06)
    y=block(d,wrap(d,L['hook2'],f,CW),f,CX,y+H*0.015,fade(INK,lin(t,0.7,1.2)),1.06)
    fi=font('serifi',int(M*0.062))
    block(d,wrap(d,L['hook3'],fi,CW),fi,CX,y+H*0.05,fade(ACCENT,lin(t,1.5,2.1)*a),1.05)

def panel(d,x0,y0,cw,ch,name,val,unit,ra,accent=False):
    bcol=ACCENT if accent else HAIR
    rrect(d,[x0,y0,x0+cw,y0+ch],int(M*0.018),fill=fade(PANEL,ra),outline=fade(bcol,ra),wd=3 if accent else 2)
    fn=font('mono',int(M*0.019))
    tracked(d,name,fn,x0+cw/2,y0+ch*0.13,fade(ACCENT if accent else INK_SOFT,ra),3)
    fb=font('serifb',int(M*0.105))
    d.text((x0+cw/2-tw(d,val,fb)/2,y0+ch*0.30),val,font=fb,fill=fade(INK,ra))
    fu=font('serifi',int(M*0.034))
    d.text((x0+cw/2-tw(d,unit,fu)/2,y0+ch*0.70),unit,font=fu,fill=fade(INK_SOFT,ra))

def sc_compare(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    cap=font('serifb',int(M*0.06))
    block(d,wrap(d,L['cmp_cap'],cap,CW),cap,CX,H*0.12,fade(INK,lin(t,0,0.45)*a),1.05)
    cw=CW; ch=H*0.20; x0=CX-cw/2
    yA=H*0.30; yB=yA+ch+int(M*0.05)
    panel(d,x0,yA,cw,ch,L['cmpA_name'],L['cmpA_v'],L['cmpA_u'],lin(t,0.5,1.0)*a,accent=False)
    panel(d,x0,yB,cw,ch,L['cmpB_name'],L['cmpB_v'],L['cmpB_u'],lin(t,1.3,1.8)*a,accent=True)
    # 19x badge
    ba=lin(t,2.2,2.7)*a
    if ba>0:
        bs=int(M*0.075); bx=CX; by=(yA+ch+yB)/2
        d.ellipse([bx-bs,by-bs*0.62,bx+bs,by+bs*0.62],fill=fade(ACCENT,ba))
        ft=font('serifb',int(M*0.05))
        txt="19x"
        d.text((bx-tw(d,txt,ft)/2,by-lineh(ft)*0.42),txt,font=ft,fill=fade(BG,ba))
    sub=font('serifi',int(M*0.034))
    block(d,wrap(d,L['cmp_sub'],sub,CW),sub,CX,yB+ch+int(M*0.04),fade(INK_SOFT,lin(t,2.8,3.3)*a),1.05)

def sc_reveal(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    f1=font('serif',int(M*0.06))
    y=block(d,wrap(d,L['rev1'],f1,CW),f1,CX,H*0.34,fade(INK,lin(t,0.1,0.7)*a),1.1)
    f2=font('serifb',int(M*0.078))
    block(d,wrap(d,L['rev2'],f2,CW),f2,CX,y+H*0.04,fade(ACCENT,lin(t,1.2,1.8)*a),1.08)

def sc_why(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    cap=font('serifb',int(M*0.05))
    y=block(d,wrap(d,L['why_cap'],cap,CW),cap,CX,H*0.16,fade(INK,lin(t,0,0.5)*a),1.1)
    fl=font('mono',int(M*0.03))
    la=lin(t,0.7,1.4)*a
    y=block(d,L['why_list'].split("\n"),fl,CX,y+H*0.05,fade(INK_SOFT,la),1.5)
    fp=font('serifi',int(M*0.05))
    block(d,L['why_punch'].split("\n"),fp,CX,y+H*0.06,fade(ACCENT,lin(t,2.0,2.6)*a),1.12)

def sc_fix(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    cap=font('serifb',int(M*0.054))
    y=block(d,wrap(d,L['fix_cap'],cap,CW),cap,CX,H*0.13,fade(INK,lin(t,0,0.45)*a),1.08)
    fb=font('serifb',int(M*0.06))
    ba=lin(t,0.6,1.1)*a
    rrect(d,[CX-CW*0.42,y+H*0.02,CX+CW*0.42,y+H*0.02+lineh(fb,1.5)],int(M*0.014),
          fill=fade(PANEL,ba),outline=fade(ACCENT,ba),wd=2)
    block(d,[L['fix_big']],fb,CX,y+H*0.02+lineh(fb,0.22),fade(ACCENT,ba),1.0)
    y=y+H*0.02+lineh(fb,1.5)
    fi=font('serif',int(M*0.04))
    steps=[(L['fix1'],1.4),(L['fix2'],2.0),(L['fix3'],2.6)]
    yy=y+H*0.04
    for txt,ts in steps:
        ra=lin(t,ts,ts+0.5)*a
        for ln in txt.split("\n"):
            d.text((CX-tw(d,ln,fi)/2,yy),ln,font=fi,fill=fade(INK,ra)); yy+=lineh(fi,1.12)
        yy+=int(M*0.022)

def sc_lesson(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    f1=font('serif',int(M*0.058))
    y=block(d,wrap(d,L['lesson1'],f1,CW),f1,CX,H*0.30,fade(INK,lin(t,0.1,0.6)*a),1.12)
    y=block(d,wrap(d,L['lesson2'],f1,CW),f1,CX,y+H*0.01,fade(INK,lin(t,0.6,1.1)*a),1.12)
    f2=font('serifb',int(M*0.07))
    block(d,wrap(d,L['lesson3'],f2,CW),f2,CX,y+H*0.04,fade(ACCENT,lin(t,1.5,2.1)*a),1.08)

def sc_cta(d,t,dur):
    a=lin(t,0,0.6)
    lab=font('mono',int(M*0.02))
    tracked(d,L['cta_pre'],lab,CX,H*0.22,fade(INK_SOFT,a),6)
    fb=font('serifb',int(M*0.05))
    y=block(d,wrap(d,L['cta1'].replace("\n"," "),fb,CW),fb,CX,H*0.29,fade(INK,lin(t,0.2,0.8)*a),1.12)
    da=lin(t,0.9,1.3); dl=int(M*0.5); dx0=CX-dl/2; dy=y+H*0.04
    d.line([(dx0,dy),(dx0+dl*da,dy)],fill=fade(HAIR,a),width=2)
    if da>0.9: d.ellipse([CX-4,dy-4,CX+4,dy+4],fill=fade(ACCENT,a))
    fu=font('mono',int(M*0.0205)); ua=lin(t,1.2,1.7)
    d.text((CX-tw(d,L['url'],fu)/2,dy+H*0.035),L['url'],font=fu,fill=fade(INK,ua))
    fsub=font('mono',int(M*0.0155)); sa=lin(t,1.5,2.0)
    d.text((CX-tw(d,L['cta_sub'],fsub)/2,dy+H*0.075),L['cta_sub'],font=fsub,fill=fade(INK_SOFT,sa))

SCENES=[(5.0,sc_hook),(7.5,sc_compare),(5.0,sc_reveal),(7.0,sc_why),(7.5,sc_fix),(5.0,sc_lesson),(6.0,sc_cta)]
LABELS=L['lab']
TOTAL=sum(d for d,_ in SCENES)
if MAXSEC>0: TOTAL=min(TOTAL,MAXSEC)
NF=int(TOTAL*FPS)

cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
     "-i","-","-an","-c:v","libx264","-pix_fmt","yuv420p","-crf","19","-preset","medium",
     "-movflags","+faststart",OUT]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for fi in range(NF):
    t=fi/FPS; acc=0; si=0; tl=t
    for idx,(dur,fn) in enumerate(SCENES):
        if t<acc+dur or idx==len(SCENES)-1:
            si=idx; tl=t-acc; break
        acc+=dur
    dur,fn=SCENES[si]
    img,d=frame_base(LABELS[si])
    fn(d,tl,dur)
    proc.stdin.write(img.tobytes())
proc.stdin.close(); proc.wait()
print("DONE %s" % OUT, flush=True)
