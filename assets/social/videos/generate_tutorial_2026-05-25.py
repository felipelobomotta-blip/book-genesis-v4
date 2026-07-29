# -*- coding: utf-8 -*-
# Book Genesis — "How to use it" step-by-step tutorial (terminal screencast style)
# Real commands + real 8-phase pipeline from the repo (book-genesis-v4).
import sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont

LANG   = sys.argv[1] if len(sys.argv)>1 else 'en'
ORIENT = sys.argv[2] if len(sys.argv)>2 else 'v'
OUT    = sys.argv[3] if len(sys.argv)>3 else 'out.mp4'

FPS = 30
W,H = (1080,1920) if ORIENT=='v' else (1920,1080)
M = min(W,H)

# cream/editorial palette
BG=(244,235,217); INK=(35,28,22); INK_SOFT=(95,80,65); HAIR=(195,180,155)
ACCENT=(180,86,52); PANEL=(250,245,234)
# terminal palette (dark)
TBG=(26,28,38); TBAR=(40,43,56); TTXT=(223,226,233); TMUTE=(150,156,170)
TGREEN=(126,196,140); TACC=(236,156,112)
DOT1=(237,106,94); DOT2=(245,191,79); DOT3=(98,197,109)

FD="/usr/share/fonts/truetype/dejavu/"
_cache={}
def font(kind,sz):
    k=(kind,sz)
    if k in _cache: return _cache[k]
    m={'serif':'DejaVuSerif.ttf','serifb':'DejaVuSerif-Bold.ttf','serifi':'DejaVuSerif-Italic.ttf',
       'mono':'DejaVuSansMono.ttf','monob':'DejaVuSansMono-Bold.ttf'}
    f=ImageFont.truetype(FD+m[kind],sz); _cache[k]=f; return f

def lerp(a,b,t): return tuple(int(round(a[i]+(b[i]-a[i])*t)) for i in range(3))
def fade(col,a): a=max(0,min(1,a)); return lerp(BG,col,a)
def tfade(col,a): a=max(0,min(1,a)); return lerp(TBG,col,a)
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

# ---------------- terminal renderer ----------------
START_DELAY=0.45; GAP_CMD=0.30; GAP_OUT=0.26; CPS=0.028

def timeline(lines):
    tl=[]; cur=START_DELAY
    for kind,text in lines:
        is_cmd=(kind=='cmd')
        dur=max(0.4,len(text)*CPS) if is_cmd else 0.0
        tl.append((kind,text,cur,dur,is_cmd))
        cur += (dur+GAP_CMD) if is_cmd else GAP_OUT
    return tl,cur

def draw_terminal(d,t,box,title,lines,FS):
    x0,y0,x1,y1=box
    pa=lin(t,0,0.35)
    rrect(d,[x0,y0,x1,y1],int(M*0.02),fill=tfade(TBG,pa))
    barh=int(M*0.055)
    d.rounded_rectangle([x0,y0,x1,y0+barh+int(M*0.02)],radius=int(M*0.02),fill=tfade(TBAR,pa))
    d.rectangle([x0,y0+barh,x1,y0+barh+2],fill=tfade(TBG,pa))
    # dots
    cy=y0+barh/2; r=int(M*0.011); bx=x0+int(M*0.04)
    for i,c in enumerate([DOT1,DOT2,DOT3]):
        d.ellipse([bx-r,cy-r,bx+r,cy+r],fill=tfade(c,pa)); bx+=int(M*0.038)
    ft=font('mono',int(M*0.018))
    d.text((x0+(x1-x0)/2-tw(d,title,ft)/2,y0+barh/2-lineh(ft)/2),title,font=ft,fill=tfade(TMUTE,pa))
    if pa<1: return
    pad=int(M*0.035); fm=font('mono',FS); lh=lineh(fm,1.42)
    cx=x0+pad; cy0=y0+barh+pad; y=cy0
    tl,total=timeline(lines)
    last=None
    for (kind,text,start,dur,is_cmd) in tl:
        if t<start: break
        shown=text; typing=False
        if is_cmd and t<start+dur:
            n=int(len(text)*((t-start)/dur)); shown=text[:n]; typing=True
        x=cx
        if kind=='cmd':
            d.text((x,y),"$ ",font=fm,fill=TGREEN); x+=tw(d,"$ ",fm)
            d.text((x,y),shown,font=fm,fill=TTXT); x+=tw(d,shown,fm)
        elif kind=='cont':
            d.text((x,y),shown,font=fm,fill=TTXT); x+=tw(d,shown,fm)
        elif kind=='comment':
            d.text((x,y),shown,font=fm,fill=TMUTE); x+=tw(d,shown,fm)
        elif kind=='ok':
            d.text((x,y),"✓ ",font=fm,fill=TGREEN); x+=tw(d,"✓ ",fm)
            d.text((x,y),shown,font=fm,fill=TTXT); x+=tw(d,shown,fm)
        elif kind=='accent':
            d.text((x,y),"✓ ",font=fm,fill=TACC); x+=tw(d,"✓ ",fm)
            d.text((x,y),shown,font=fm,fill=TACC); x+=tw(d,shown,fm)
        elif kind=='out':
            d.text((x,y),shown,font=fm,fill=TMUTE); x+=tw(d,shown,fm)
        elif kind=='blank':
            pass
        last=(x,y,typing)
        y+=lh
    # cursor
    if last:
        lx,ly,typing=last
        blink = typing or (int(t*2)%2==0)
        if blink:
            cw=tw(d,"M",fm); ch=lh*0.74
            d.rectangle([lx,ly+lh*0.06,lx+cw*0.6,ly+ch],fill=TGREEN)

# ---------------- strings ----------------
T={
 'en':{
  'i_top':"HOW TO USE",'i_big':"Book Genesis",
  'i_sub':"From an idea to a scored, market-ready book — step by step.",
  's1_lab':"STEP 1 · INSTALL",'s1_cap':"Clone the repo and install the skills.",
  's1':[('cmd','git clone .../book-genesis-v4'),('cmd','cd book-genesis-v4'),
        ('cmd','./install.ps1'),('ok','9 book-studio skills installed')],
  's2_lab':"STEP 2 · POINT ANY AGENT",'s2_cap':"Works in any agent that reads files.",
  's2':[('comment','# Claude Code / Codex / Antigravity / Kimi'),
        ('cmd','Read AGENTS.md. Use Book Genesis.'),
        ('out','loaded: Universal Book Genesis Core'),
        ('out','9 skills - 8-phase pipeline - scoring')],
  's3_lab':"STEP 3 · START A BOOK",'s3_cap':"One command. One idea. That's the whole input.",
  's3':[('cmd','/book-genesis-codex en "an archivist'),
        ('cont','  who finds every deleted manuscript'),
        ('cont','  is still being edited somewhere"'),
        ('out','project created -> PROJECT_STATE.yaml')],
  's4_lab':"STEP 4 · THE PIPELINE RUNS",'s4_cap':"8 phases. Each writes a file the next one reads.",
  's4':[('out','running pipeline...'),
        ('ok','P0 Intake        brief - market map'),
        ('ok','P1 Foundation    characters - theme'),
        ('ok','P2 Architecture  outline - opening'),
        ('ok','P3 Drafting      manuscript/chapters'),
        ('accent','P4 Adversarial Audit  (before score)'),
        ('ok','P5 Barrier Loop  fix weakest dimension'),
        ('ok','P6 Final Score   Genesis Score + floor'),
        ('ok','P7 Editorial Pkg query - synopsis')],
  's5_lab':"STEP 5 · THE QUALITY GATE",'s5_cap':"This is the trick: hype separated from evidence.",
  's5':[('out','adversarial audit runs BEFORE the score'),
        ('out','floor rule: no weak dimension hides'),
        ('out','  behind a high average'),
        ('blank',''),
        ('accent','Genesis Score 8.7   gate 8.5+   PASS')],
  's6_lab':"STEP 6 · WHAT YOU GET",'s6_cap':"Every quality claim is backed by a file you can open.",
  's6':[('ok','manuscript/       full draft'),
        ('ok','artifacts/        brief to score'),
        ('ok','evaluations/      audit - revisions'),
        ('ok','editorial-package query - cover brief'),
        ('out','done. a book package you can audit.')],
  'cta_pre':"BOOK GENESIS",
  'cta1':"Open source. Runs on any agent\nthat reads files.",
  'url':"github.com/felipelobomotta-blip/book-genesis-v4",
  'cta_sub':"MIT - Claude Code - Codex - Kimi - Antigravity",
 },
 'pt':{
  'i_top':"COMO USAR",'i_big':"Book Genesis",
  'i_sub':"De uma ideia a um livro pontuado e pronto pro mercado — passo a passo.",
  's1_lab':"PASSO 1 · INSTALAR",'s1_cap':"Clone o repo e instale as skills.",
  's1':[('cmd','git clone .../book-genesis-v4'),('cmd','cd book-genesis-v4'),
        ('cmd','./install.ps1'),('ok','9 skills de estudio instaladas')],
  's2_lab':"PASSO 2 · APONTE QUALQUER AGENTE",'s2_cap':"Funciona em qualquer agente que le arquivo.",
  's2':[('comment','# Claude Code / Codex / Antigravity / Kimi'),
        ('cmd','Leia AGENTS.md. Use o Book Genesis.'),
        ('out','carregado: Universal Book Genesis Core'),
        ('out','9 skills - pipeline de 8 fases - score')],
  's3_lab':"PASSO 3 · COMECE UM LIVRO",'s3_cap':"Um comando. Uma ideia. E so isso de entrada.",
  's3':[('cmd','/book-genesis-codex pt "um arquivista'),
        ('cont','  que descobre que todo manuscrito'),
        ('cont','  apagado ainda esta sendo editado"'),
        ('out','projeto criado -> PROJECT_STATE.yaml')],
  's4_lab':"PASSO 4 · O PIPELINE RODA",'s4_cap':"8 fases. Cada uma escreve um arquivo que a proxima le.",
  's4':[('out','rodando pipeline...'),
        ('ok','F0 Intake        brief - mapa mercado'),
        ('ok','F1 Fundacao      personagens - tema'),
        ('ok','F2 Arquitetura   outline - abertura'),
        ('ok','F3 Draft         manuscript/capitulos'),
        ('accent','F4 Adversarial Audit  (antes do score)'),
        ('ok','F5 Barrier Loop  corrige o elo fraco'),
        ('ok','F6 Score Final   Genesis Score + floor'),
        ('ok','F7 Pacote Edit.  query - sinopse')],
  's5_lab':"PASSO 5 · O PORTAO DE QUALIDADE",'s5_cap':"O truque: hype separado de evidencia.",
  's5':[('out','auditoria adversarial roda ANTES do score'),
        ('out','floor rule: nenhum elo fraco se esconde'),
        ('out','  atras de uma media alta'),
        ('blank',''),
        ('accent','Genesis Score 8.7   gate 8.5+   PASSA')],
  's6_lab':"PASSO 6 · O QUE VOCE RECEBE",'s6_cap':"Toda alegacao de qualidade vem com um arquivo pra abrir.",
  's6':[('ok','manuscript/       draft completo'),
        ('ok','artifacts/        do brief ao score'),
        ('ok','evaluations/      audit - revisoes'),
        ('ok','editorial-package query - capa'),
        ('out','pronto. um pacote de livro auditavel.')],
  'cta_pre':"BOOK GENESIS",
  'cta1':"Open source. Roda em qualquer agente\nque le arquivo.",
  'url':"github.com/felipelobomotta-blip/book-genesis-v4",
  'cta_sub':"MIT - Claude Code - Codex - Kimi - Antigravity",
 },
}
L=T[LANG]
CW=W-2*int(M*0.10); CX=W/2
FS=int(M*0.0265)
TBOX=(int(M*0.075),int(H*0.205),W-int(M*0.075),int(H*0.78)) if ORIENT=='v' else (int(W*0.18),int(H*0.20),int(W*0.82),int(H*0.80))

def scene_step(d,t,dur,lab_key,cap_key,lines_key,title):
    cap=font('serifi',int(M*0.034))
    a=lin(t,0.1,0.6)
    draw_terminal(d,t,TBOX,title,L[lines_key],FS)
    cy=TBOX[3]+int(M*0.045)
    block(d,wrap(d,L[cap_key],cap,CW),cap,CX,cy,fade(INK_SOFT,a),1.12)

def sc_intro(d,t,dur):
    a=(1-lin(t,dur-0.35,dur))
    tracked(d,L['i_top'],font('mono',int(M*0.022)),CX,H*0.30,fade(INK_SOFT,lin(t,0.1,0.6)*a),7)
    fb=font('serifb',int(M*0.10))
    y=block(d,wrap(d,L['i_big'],fb,CW),fb,CX,H*0.36,fade(INK,lin(t,0.4,1.0)*a),1.05)
    da=lin(t,1.0,1.4); dl=int(M*0.42); d.line([(CX-dl/2,y+H*0.03),(CX-dl/2+dl*da,y+H*0.03)],fill=fade(HAIR,a),width=2)
    fs=font('serifi',int(M*0.04))
    block(d,wrap(d,L['i_sub'],fs,CW*0.92),fs,CX,y+H*0.06,fade(INK_SOFT,lin(t,1.4,2.0)*a),1.15)

def sc_s1(d,t,dur): scene_step(d,t,dur,'s1_lab','s1_cap','s1',"book-genesis — bash")
def sc_s2(d,t,dur): scene_step(d,t,dur,'s2_lab','s2_cap','s2',"agent — session")
def sc_s3(d,t,dur): scene_step(d,t,dur,'s3_lab','s3_cap','s3',"book-genesis — bash")
def sc_s4(d,t,dur): scene_step(d,t,dur,'s4_lab','s4_cap','s4',"book-genesis — pipeline")
def sc_s5(d,t,dur): scene_step(d,t,dur,'s5_lab','s5_cap','s5',"book-genesis — score")
def sc_s6(d,t,dur): scene_step(d,t,dur,'s6_lab','s6_cap','s6',"book-genesis — output")

def sc_cta(d,t,dur):
    a=lin(t,0,0.6)
    tracked(d,L['cta_pre'],font('mono',int(M*0.02)),CX,H*0.26,fade(INK_SOFT,a),6)
    fb=font('serifb',int(M*0.05))
    y=block(d,wrap(d,L['cta1'].replace("\n"," "),fb,CW),fb,CX,H*0.33,fade(INK,lin(t,0.2,0.8)*a),1.12)
    da=lin(t,0.9,1.3); dl=int(M*0.5); dy=y+H*0.04
    d.line([(CX-dl/2,dy),(CX-dl/2+dl*da,dy)],fill=fade(HAIR,a),width=2)
    if da>0.9: d.ellipse([CX-4,dy-4,CX+4,dy+4],fill=fade(ACCENT,a))
    fu=font('mono',int(M*0.0205)); d.text((CX-tw(d,L['url'],fu)/2,dy+H*0.035),L['url'],font=fu,fill=fade(INK,lin(t,1.2,1.7)))
    fsub=font('mono',int(M*0.0155)); d.text((CX-tw(d,L['cta_sub'],fsub)/2,dy+H*0.075),L['cta_sub'],font=fsub,fill=fade(INK_SOFT,lin(t,1.5,2.0)))

SCENES=[(4.5,sc_intro),(6.5,sc_s1),(6.0,sc_s2),(7.0,sc_s3),(11.0,sc_s4),(7.5,sc_s5),(7.0,sc_s6),(6.0,sc_cta)]
TOTAL=sum(d for d,_ in SCENES); NF=int(TOTAL*FPS)
STEP_LABELS={1:'s1_lab',2:'s2_lab',3:'s3_lab',4:'s4_lab',5:'s5_lab',6:'s6_lab'}

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
    # frame_base label: show step label for terminal scenes
    lab=""
    if si in STEP_LABELS: lab=L[STEP_LABELS[si]]
    img,d=frame_base(lab)
    fn(d,tl,dur)
    proc.stdin.write(img.tobytes())
proc.stdin.close(); proc.wait()
print("DONE %s" % OUT, flush=True)
