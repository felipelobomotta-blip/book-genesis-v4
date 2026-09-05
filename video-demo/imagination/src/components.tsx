import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {colors, sans, serif} from './theme';

export const FadeIn: React.FC<React.PropsWithChildren<{delay?: number; duration?: number; style?: React.CSSProperties}>> = ({
  children,
  delay = 0,
  duration = 14,
  style,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [delay, delay + duration], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
        translate: `0 ${interpolate(frame, [delay, delay + duration], [20, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        })}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Grain: React.FC = () => (
  <AbsoluteFill
    style={{
      opacity: 0.12,
      backgroundImage:
        'radial-gradient(rgba(23,59,51,.24) .6px, transparent .7px), radial-gradient(rgba(23,59,51,.12) .6px, transparent .7px)',
      backgroundSize: '14px 14px, 19px 19px',
      backgroundPosition: '0 0, 7px 7px',
      pointerEvents: 'none',
    }}
  />
);

export const BrandMark: React.FC<{dark?: boolean}> = ({dark = false}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      color: dark ? colors.cream : colors.forest,
      fontFamily: sans,
      fontSize: 20,
      letterSpacing: 2.8,
      fontWeight: 700,
      textTransform: 'uppercase',
    }}
  >
    <span
      style={{
        display: 'inline-flex',
        width: 32,
        height: 32,
        border: `2px solid ${dark ? colors.copperSoft : colors.copper}`,
        borderRadius: 16,
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: serif,
        fontSize: 20,
      }}
    >
      B
    </span>
    Book Genesis
  </div>
);

export const Eyebrow: React.FC<{children: React.ReactNode; dark?: boolean}> = ({children, dark = false}) => (
  <div
    style={{
      color: dark ? colors.copperSoft : colors.copper,
      fontFamily: sans,
      fontWeight: 700,
      letterSpacing: 3.5,
      fontSize: 20,
      textTransform: 'uppercase',
    }}
  >
    {children}
  </div>
);

export const Footer: React.FC<{dark?: boolean; label?: string}> = ({dark = false, label = 'Book Genesis 5 · Imagination Edition'}) => (
  <div
    style={{
      position: 'absolute',
      left: 68,
      right: 68,
      bottom: 52,
      display: 'flex',
      justifyContent: 'space-between',
      color: dark ? 'rgba(247,241,230,.72)' : 'rgba(23,59,51,.65)',
      fontFamily: sans,
      fontWeight: 700,
      fontSize: 17,
      letterSpacing: 1.3,
      textTransform: 'uppercase',
    }}
  >
    <span>{label}</span>
    <span>Open source · beta</span>
  </div>
);

export const ScriptedSample: React.FC = () => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  return (
    <div
    style={{
      position: 'absolute',
      top: 34,
      right: 38,
      zIndex: 5,
      padding: '10px 15px',
      borderRadius: 30,
      backgroundColor: 'rgba(12,41,35,.88)',
      color: colors.cream,
      fontFamily: sans,
      fontWeight: 700,
      letterSpacing: 0.7,
      fontSize: portrait ? 22 : 15,
    }}
  >
    Scripted sample · edited for time
    </div>
  );
};

export const Caption: React.FC<{children: React.ReactNode; inverse?: boolean}> = ({children, inverse = false}) => (
  <FadeIn delay={8} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
    <div
      style={{
        position: 'absolute',
        zIndex: 8,
        left: '50%',
        bottom: 180,
        translate: '-50% 0',
        maxWidth: 1120,
        padding: '16px 26px',
        borderRadius: 12,
        backgroundColor: inverse ? 'rgba(247,241,230,.94)' : 'rgba(12,41,35,.92)',
        color: inverse ? colors.forestDeep : colors.cream,
        boxShadow: '0 10px 36px rgba(12,41,35,.16)',
        fontFamily: sans,
        fontSize: 28,
        fontWeight: 600,
        lineHeight: 1.25,
        textAlign: 'center',
      }}
    >
      {children}
    </div>
  </FadeIn>
);

export const MediaFrame: React.FC<{src: string; alt: string; kind?: 'image' | 'video'; mobile?: boolean}> = ({
  src,
  alt,
  kind = 'image',
  mobile = false,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const isPortrait = height > width;
  const media = kind === 'video' ? (
    <OffthreadVideo
      muted
      src={staticFile(src)}
      style={{width: '100%', height: '100%', objectFit: 'contain', backgroundColor: '#101615'}}
    />
  ) : (
    <Img src={staticFile(src)} alt={alt} style={{width: '100%', height: '100%', objectFit: 'contain', backgroundColor: '#101615'}} />
  );

  return (
    <div
      aria-label={alt}
      style={{
        position: 'relative',
        width: isPortrait ? width - 128 : Math.min(width * 0.67, 1110),
        height: isPortrait ? 1040 : Math.min(height * 0.61, 658),
        border: `${isPortrait ? 10 : 12}px solid ${colors.paper}`,
        borderRadius: isPortrait ? 24 : 20,
        overflow: 'hidden',
        boxShadow: '0 30px 80px rgba(12,41,35,.28)',
        scale: interpolate(frame, [0, 16], [0.96, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      }}
    >
      {media}
    </div>
  );
};

export const StepRail: React.FC<{active: number; vertical?: boolean}> = ({active, vertical = false}) => {
  const steps = ['Setup', 'Idea', 'Checkpoint', 'Read', 'Export'];
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: vertical ? 'column' : 'row',
        gap: vertical ? 16 : 0,
        alignItems: vertical ? 'stretch' : 'center',
        justifyContent: 'space-between',
      }}
    >
      {steps.map((step, index) => (
        <React.Fragment key={step}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0}}>
            <span
              style={{
                width: 25,
                height: 25,
                borderRadius: 14,
                backgroundColor: index <= active ? colors.copper : 'rgba(23,75,61,.18)',
                color: index <= active ? colors.paper : colors.muted,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: sans,
                fontSize: 13,
                fontWeight: 700,
              }}
            >
              {index + 1}
            </span>
            <span style={{fontFamily: sans, fontSize: 17, fontWeight: 700, color: index === active ? colors.forestDeep : colors.muted}}>{step}</span>
          </div>
          {index < steps.length - 1 && <div style={{height: vertical ? 1 : 2, width: vertical ? 'auto' : 45, backgroundColor: 'rgba(23,75,61,.2)', margin: vertical ? '0 0 0 12px' : '0 14px'}} />}
        </React.Fragment>
      ))}
    </div>
  );
};

export const Background: React.FC<{dark?: boolean}> = ({dark = false}) => (
  <AbsoluteFill style={{backgroundColor: dark ? colors.forestDeep : colors.cream}}>
    <Grain />
    <div
      style={{
        position: 'absolute',
        width: 620,
        height: 620,
        borderRadius: 400,
        right: -210,
        top: -250,
        backgroundColor: dark ? 'rgba(185,103,62,.16)' : 'rgba(184,202,187,.32)',
      }}
    />
  </AbsoluteFill>
);
