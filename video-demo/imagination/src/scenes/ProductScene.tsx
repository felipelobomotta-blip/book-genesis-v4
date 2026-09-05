import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';
import {Background, BrandMark, Caption, Eyebrow, FadeIn, Footer, MediaFrame, ScriptedSample, StepRail} from '../components';
import {colors, sans, serif} from '../theme';

type ProductSceneProps = {
  eyebrow: string;
  title: string;
  body: string;
  asset: string;
  alt: string;
  kind?: 'image' | 'video';
  active: number;
  caption: string;
  mobile?: boolean;
  short?: boolean;
};

export const ProductScene: React.FC<ProductSceneProps> = ({
  eyebrow,
  title,
  body,
  asset,
  alt,
  kind,
  active,
  caption,
  mobile,
  short = false,
}) => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  return (
    <AbsoluteFill>
      <Background />
      <div style={{position: 'absolute', left: portrait ? 64 : 70, right: portrait ? 64 : 70, top: portrait ? 70 : 58}}>
        <FadeIn><BrandMark /></FadeIn>
      </div>
      <div style={{position: 'absolute', left: portrait ? 64 : 78, right: portrait ? 64 : width * 0.68, top: portrait ? 172 : 165, zIndex: 3}}>
        <FadeIn delay={5}><Eyebrow>{eyebrow}</Eyebrow></FadeIn>
        <FadeIn delay={12}>
          <div style={{color: colors.forestDeep, fontFamily: serif, fontSize: portrait ? 67 : 62, lineHeight: 1.04, letterSpacing: -2, marginTop: 20}}>{title}</div>
        </FadeIn>
        <FadeIn delay={23}>
          <div style={{color: colors.muted, fontFamily: sans, fontSize: portrait ? 27 : 24, lineHeight: 1.4, marginTop: 22, maxWidth: portrait ? 720 : 500}}>{body}</div>
        </FadeIn>
      </div>
      <div style={{position: 'absolute', right: portrait ? 64 : 72, top: portrait ? height * 0.30 : 140, left: portrait ? 64 : width * 0.38, bottom: portrait ? 215 : 135, display: 'flex', justifyContent: portrait ? 'center' : 'flex-end', alignItems: 'center'}}>
        <MediaFrame src={asset} alt={alt} kind={kind} mobile={mobile} />
        <ScriptedSample />
      </div>
      {!short && (
        <div style={{position: 'absolute', left: 78, right: 78, bottom: 100}}>
          <StepRail active={active} vertical={portrait} />
        </div>
      )}
      <Caption>{caption}</Caption>
      {!short && <Footer />}
    </AbsoluteFill>
  );
};
