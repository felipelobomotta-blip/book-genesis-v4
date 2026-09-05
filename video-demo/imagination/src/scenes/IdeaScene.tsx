import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';
import {Background, BrandMark, Caption, Eyebrow, FadeIn, Footer, StepRail} from '../components';
import {colors, sans, serif} from '../theme';

export const IdeaScene: React.FC<{short?: boolean}> = ({short = false}) => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  return (
    <AbsoluteFill>
      <Background />
      <div style={{position: 'absolute', top: portrait ? 74 : 60, left: portrait ? 64 : 76}}><FadeIn><BrandMark /></FadeIn></div>
      <div style={{position: 'absolute', top: portrait ? 190 : 165, left: portrait ? 64 : 78, right: portrait ? 64 : width * 0.53}}>
        <FadeIn delay={5}><Eyebrow>Start with an idea</Eyebrow></FadeIn>
        <FadeIn delay={12}><div style={{color: colors.forestDeep, fontFamily: serif, fontSize: portrait ? 72 : 70, letterSpacing: -2.5, lineHeight: 1.04, marginTop: 22}}>You provide the spark.</div></FadeIn>
        <FadeIn delay={23}><div style={{color: colors.muted, fontFamily: sans, fontSize: portrait ? 29 : 25, lineHeight: 1.4, marginTop: 22}}>Choose the premise, language, and providers. The runner gives your idea a structured path forward.</div></FadeIn>
      </div>
      <FadeIn delay={17} duration={18} style={{position: 'absolute', top: portrait ? 520 : 206, right: portrait ? 64 : 90, left: portrait ? 64 : width * 0.49}}>
        <div style={{backgroundColor: colors.forestDeep, borderRadius: 22, padding: portrait ? '34px 32px' : '36px 40px', boxShadow: '0 30px 70px rgba(12,41,35,.24)'}}>
          <div style={{color: colors.copperSoft, fontFamily: sans, fontSize: 16, letterSpacing: 2, textTransform: 'uppercase', fontWeight: 700, marginBottom: 18}}>Your terminal</div>
          <div style={{color: colors.cream, fontFamily: '"Courier New", monospace', fontSize: portrait ? 21 : 25, lineHeight: 1.55, wordBreak: 'break-word'}}>
            <span style={{color: colors.copperSoft}}>$</span> book-genesis new --idea<br />&nbsp;&nbsp;"Your premise" --language en
          </div>
          <div style={{height: 1, backgroundColor: 'rgba(247,241,230,.16)', margin: '26px 0 19px'}} />
          <div style={{color: 'rgba(247,241,230,.72)', fontFamily: sans, fontSize: portrait ? 20 : 19, lineHeight: 1.4}}>The software serves the author’s choices.</div>
        </div>
      </FadeIn>
      {!short && <div style={{position: 'absolute', left: 78, right: 78, bottom: 100}}><StepRail active={0} vertical={portrait} /></div>}
      <Caption>Your premise stays at the center of the work.</Caption>
      {!short && <Footer />}
    </AbsoluteFill>
  );
};
