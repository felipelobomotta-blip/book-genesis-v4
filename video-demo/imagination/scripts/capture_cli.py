"""Record real runner output with deterministic, explicitly labeled fixtures."""
from pathlib import Path
import contextlib, importlib.util, io, json, os, sys, tempfile
from unittest.mock import patch
from rich.console import Console
from rich.terminal_theme import MONOKAI

SOURCE = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / 'public'
CAP = OUT / 'capture-pages'
CAP.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE))
from runner.app import main, session_main
from runner.ui import RichView
from runner.review import build_review

def write_html(name, console):
    page=console.export_html(clear=True,theme=MONOKAI)
    # This only frames unmodified Rich console output for screen recording.
    page=page.replace('<body>', '<body style="margin:0;padding:24px">').replace(str(RUN), '[capture-folder]')
    (CAP/f'{name}.html').write_text(page,encoding='utf-8')

class CaptureView(RichView):
    def __init__(self, answers):
        self.answers=iter(answers)
        self.captures=[]
        self.sink=io.StringIO()
        super().__init__(interactive=True,live=False,console=Console(file=self.sink,record=True,width=86,force_terminal=True))
    def checkpoint(self,title,body,hint):
        self.console.export_text(clear=True)
        answer=next(self.answers)
        with patch.object(self.console,'input',return_value=answer):
            result=super().checkpoint(title,body,hint)
        name={'The brief':'capture-checkpoint','The outline':'capture-outline','Chapter 1, read blind':'capture-chapter'}[title]
        write_html(name,self.console)
        self.captures.append({'title':title,'answer':answer,'capture':name})
        return result

spec=importlib.util.spec_from_file_location('demo_builder',SOURCE/'scripts/build_reader_demo.py')
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
draft=demo.CHAPTERS[1][0]; accepted=demo.CHAPTERS[1][1]
brief='A night-shift librarian finds a library card stamped with tomorrow\'s date. The name on it is her own.'
intake=('=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nScripted interface fixture.\n'
        '=== FILE: artifacts/00-brief.md ===\n# Brief\n\n'+brief+'\n\nAudience: adult mystery readers.\nDirection: an intimate mystery inside a night library.\n'
        '=== FILE: artifacts/01-market-map.md ===\n# Market map\n\nFixture material, not market research.\n'
        '=== FILE: artifacts/02-story-engine.md ===\n# Story engine\n\nMara must discover why the date is ahead.\n'
        '=== STATE ===\ntitle: The Lantern Index\ngenre: thriller\nlanguage: en\n')
intake_note=intake.replace('Audience: adult mystery readers.','Author direction: Mara questions the date before touching the card.\nAudience: adult mystery readers.')
foundation=('=== FILE: artifacts/03-characters.md ===\n# Characters\n\nMara, a cautious night librarian.\n'
            '=== FILE: artifacts/04-theme.md ===\n# Theme\n\nWho gets to decide the next page?\n'
            '=== FILE: artifacts/06-emotional-curve.md ===\n# Curve\n\nCuriosity becomes a choice.\n')
outline=('=== FILE: artifacts/05-outline.md ===\n# Outline\n\n## Chapter 1: The Lantern Index\n\nMara finds the card and questions its date before the return chute clicks.\n\n## Chapter 2: The Return Chute\n\nA second card introduces a name from the past.\n'
         '=== FILE: artifacts/07-opening-strategy.md ===\n# Opening strategy\n\nBegin with the card and a concrete unanswered question.\n')
yes='```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the library card stamped tomorrow\nflags: []\nvs_previous: none\nvs_anchor: none\n```\n'
sep='\n=== NEXT ===\n'
RUN=Path(tempfile.mkdtemp(prefix='book-genesis-video-'))
(RUN/'new-responses.txt').write_text(sep.join([intake,intake_note,foundation,outline]),encoding='utf-8')
(RUN/'resume-responses.txt').write_text(sep.join([draft,accepted,yes,yes,yes]),encoding='utf-8')
os.chdir(RUN)
project=Path('books/lantern-demo')
if project.exists():raise SystemExit('Recording project already exists; choose a fresh capture directory.')
view=CaptureView(['Make Mara question the date before touching the card.','','q'])
code=session_main(['new','--idea',brief,'--language','en','--path',str(project),'--fake-responses','new-responses.txt'],view=view)
assert code==0
resume=CaptureView(['','q'])
code2=session_main(['resume',str(project),'--fake-responses','resume-responses.txt'],view=resume)
assert code2==0
transcripts={}
for name,args in [('capture-setup',['--help']),('capture-export',['export',str(project),'--format','epub'])]:
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):ret=main(args)
    assert ret==0
    text=stream.getvalue().replace(str(project.resolve()),'[project]');transcripts[name]={'args':args,'exit_code':ret,'output':text}
    c=Console(file=io.StringIO(),record=True,width=94)
    c.print('$ book-genesis '+' '.join(args),style='bold cyan')
    c.print(text,markup=False)
    write_html(name,c)
    (CAP/f'{name}.txt').write_text(text,encoding='utf-8')
transcripts['guided']={'new_exit':code,'resume_exit':code2,'checkpoints':view.captures+resume.captures,'new_output':view.sink.getvalue(),'resume_output':resume.sink.getvalue()}
(CAP/'recording-evidence.json').write_text(json.dumps(transcripts,indent=2),encoding='utf-8')
# The existing public fixture provides a second chapter and two version choices.
demo.build(OUT/'reader',SOURCE)
(CAP/'capture-start.html').write_text((CAP/'capture-checkpoint.html').read_text(encoding='utf-8'),encoding='utf-8')
print(json.dumps({'new_exit':code,'resume_exit':code2,'checkpoints':len(view.captures+resume.captures),'export_exists':(project/'exports/manuscript.epub').is_file(),'captures':[p.name for p in CAP.glob('*.html')]},indent=2))
