import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {Background, BrandMark, Caption, Eyebrow, FadeIn, Footer, MediaFrame, ScriptedSample, StepRail} from '../components';
import {colors, sans, serif} from '../theme';

export const CheckpointScene: React.FC<{caption: string; short?: boolean}> = ({caption, short = false}) => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  const segment = short ? 72 : 113;
  const frames = short ? 216 : 341;

  return (
    <AbsoluteFill>
      <Background />
      <div style={{position: 'absolute', left: portrait ? 64 : 70, right: portrait ? 64 : 70, top: portrait ? 70 : 58}}><FadeIn><BrandMark /></FadeIn></div>
      <div style={{position: 'absolute', left: portrait ? 64 : 78, right: portrait ? 64 : width * 0.69, top: portrait ? 172 : 165, zIndex: 3}}>
        <FadeIn delay={5}><Eyebrow>Pause for the author</Eyebrow></FadeIn>
        <FadeIn delay={12}><div style={{color: colors.forestDeep, fontFamily: serif, fontSize: portrait ? 67 : 62, lineHeight: 1.04, letterSpacing: -2, marginTop: 20}}>Review the work at key moments.</div></FadeIn>
        <FadeIn delay={23}><div style={{color: colors.muted, fontFamily: sans, fontSize: portrait ? 27 : 24, lineHeight: 1.4, marginTop: 22, maxWidth: portrait ? 720 : 500}}>Read the brief, outline, and first chapter. Continue, leave a note, or return later.</div></FadeIn>
      </div>
      <div style={{position: 'absolute', right: portrait ? 64 : 72, top: portrait ? height * 0.30 : 140, left: portrait ? 64 : width * 0.38, bottom: portrait ? 215 : 135, display: 'flex', justifyContent: portrait ? 'center' : 'flex-end', alignItems: 'center'}}>
        <Sequence from={0} durationInFrames={segment} layout="none"><MediaFrame src="capture-checkpoint.png" alt="Book Genesis checkpoint capture" /></Sequence>
        <Sequence from={segment} durationInFrames={segment} layout="none"><MediaFrame src="capture-outline.png" alt="Book Genesis outline capture" /></Sequence>
        <Sequence from={segment * 2} durationInFrames={frames - segment * 2} layout="none"><MediaFrame src="capture-chapter.png" alt="Book Genesis chapter capture" /></Sequence>
        <ScriptedSample />
      </div>
      {!short && <div style={{position: 'absolute', left: 78, right: 78, bottom: 100}}><StepRail active={2} vertical={portrait} /></div>}
      <Caption>{caption}</Caption>
      {!short && <Footer />}
    </AbsoluteFill>
  );
};
