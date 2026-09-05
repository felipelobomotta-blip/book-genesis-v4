import React from 'react';
import {AbsoluteFill, Img, staticFile, useVideoConfig} from 'remotion';
import {Background, BrandMark, Eyebrow, FadeIn, Footer} from '../components';
import {colors, sans, serif} from '../theme';

export const Closing: React.FC<{short?: boolean}> = ({short = false}) => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  return (
    <AbsoluteFill>
      <Background dark />
      <Img src={staticFile('hero.png')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: .22, filter: 'saturate(.6)'}} />
      <div style={{position: 'absolute', inset: 0, background: 'rgba(12,41,35,.70)'}} />
      <div style={{position: 'absolute', top: portrait ? 78 : 65, left: portrait ? 72 : 88}}><FadeIn><BrandMark dark /></FadeIn></div>
      <div style={{position: 'absolute', left: portrait ? 72 : 88, right: portrait ? 72 : width * .34, top: portrait ? 270 : 220}}>
        <FadeIn delay={6}><Eyebrow dark>Imagination Edition</Eyebrow></FadeIn>
        <FadeIn delay={13}><div style={{color: colors.cream, fontFamily: serif, fontSize: portrait ? 88 : 88, lineHeight: 1.02, letterSpacing: -3, marginTop: 24}}>Creativity comes first.</div></FadeIn>
        <FadeIn delay={25}><div style={{color: 'rgba(247,241,230,.85)', fontFamily: sans, fontSize: portrait ? 31 : 29, lineHeight: 1.4, marginTop: 26}}>Your story. Your choices. Your first chapter.</div></FadeIn>
        <FadeIn delay={35}><div style={{display: 'inline-block', marginTop: 40, padding: '18px 25px', borderRadius: 8, backgroundColor: colors.copper, color: colors.paper, fontFamily: sans, fontWeight: 700, fontSize: portrait ? 25 : 23, letterSpacing: .3}}>github.com/felipelobomotta-blip/book-genesis-v4</div></FadeIn>
      </div>
      {!short && <Footer dark />}
    </AbsoluteFill>
  );
};
