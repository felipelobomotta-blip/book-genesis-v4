import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, BrandMark, Eyebrow, FadeIn, Footer} from '../components';
import {colors, sans, serif} from '../theme';

export const Hero: React.FC<{short?: boolean}> = ({short = false}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  const headline = short ? 'That idea deserves\na first chapter.' : 'Your story begins\nwith your imagination.';

  return (
    <AbsoluteFill>
      <Background dark />
      <Img
        src={staticFile('hero.png')}
        style={{
          position: 'absolute',
          right: portrait ? 0 : -30,
          top: portrait ? height * 0.53 : 0,
          width: portrait ? width : width * 0.57,
          height: portrait ? height * 0.43 : height,
          objectFit: 'contain',
          opacity: 0.78,
          filter: 'saturate(.88) contrast(1.03)',
          scale: interpolate(frame, [0, 180], [1.07, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        }}
      />
      <div style={{position: 'absolute', inset: 0, background: portrait ? 'linear-gradient(180deg, rgba(12,41,35,.06), rgba(12,41,35,.84) 62%)' : 'linear-gradient(90deg, #0C2923 28%, rgba(12,41,35,.87) 49%, rgba(12,41,35,.14) 100%)'}} />
      <div style={{position: 'absolute', top: portrait ? 88 : 70, left: portrait ? 80 : 90, right: portrait ? 80 : width * 0.48}}>
        <FadeIn><BrandMark dark /></FadeIn>
      </div>
      <div style={{position: 'absolute', top: portrait ? 260 : 232, left: portrait ? 80 : 90, right: portrait ? 70 : width * 0.43}}>
        <FadeIn delay={8}><Eyebrow dark>Imagination Edition</Eyebrow></FadeIn>
        <FadeIn delay={17} duration={18}>
          <div style={{whiteSpace: 'pre-line', color: colors.cream, fontFamily: serif, fontSize: portrait ? 88 : 92, fontWeight: 400, lineHeight: 1.02, letterSpacing: -3, marginTop: 26}}>{headline}</div>
        </FadeIn>
        <FadeIn delay={35}>
          <div style={{color: 'rgba(247,241,230,.84)', fontFamily: sans, fontSize: portrait ? 31 : 28, lineHeight: 1.35, maxWidth: portrait ? 680 : 660, marginTop: 30}}>
            A guided open-source writing runner that keeps the author in the loop.
          </div>
        </FadeIn>
      </div>
      <Footer dark label="Book Genesis 5" />
    </AbsoluteFill>
  );
};
