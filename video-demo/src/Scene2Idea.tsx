import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { BG, WHITE, PURPLE_LIGHT, GRAY, GRAY_DIM } from './constants';

const IDEA_TEXT =
  '"A journalist covering the 2026 World Cup uncovers a government alien contact cover-up"';

export const Scene2Idea: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in the container
  const containerFade = interpolate(frame, [0, fps * 0.4], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Typing effect: reveal characters over 3.5s
  const typeDuration = fps * 3.5;
  const charsToShow = Math.floor(
    interpolate(frame, [fps * 0.3, fps * 0.3 + typeDuration], [0, IDEA_TEXT.length], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  const visibleText = IDEA_TEXT.slice(0, charsToShow);

  // Blinking cursor: blink every 0.5s
  const cursorVisible = Math.floor(frame / (fps * 0.5)) % 2 === 0;
  const showCursor = charsToShow < IDEA_TEXT.length || cursorVisible;

  // Label slide in
  const labelFade = interpolate(frame, [0, fps * 0.6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: BG,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        padding: '0 120px',
        boxSizing: 'border-box',
      }}
    >
      {/* Subtle grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div style={{ opacity: containerFade, width: '100%', maxWidth: 1100, zIndex: 1 }}>
        {/* Label */}
        <div
          style={{
            opacity: labelFade,
            fontSize: 13,
            fontFamily: "'Courier New', monospace",
            color: PURPLE_LIGHT,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            marginBottom: 20,
          }}
        >
          // your idea
        </div>

        {/* Terminal box */}
        <div
          style={{
            background: 'rgba(124,58,237,0.06)',
            border: `1px solid rgba(124,58,237,0.25)`,
            borderRadius: 12,
            padding: '36px 44px',
          }}
        >
          {/* Terminal header dots */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            {['#ff5f57', '#febc2e', '#28c840'].map((c, i) => (
              <div
                key={i}
                style={{ width: 12, height: 12, borderRadius: '50%', background: c }}
              />
            ))}
          </div>

          {/* Typed text */}
          <div
            style={{
              fontFamily: "'Courier New', 'Consolas', monospace",
              fontSize: 28,
              color: WHITE,
              lineHeight: 1.6,
              minHeight: 80,
            }}
          >
            <span style={{ color: PURPLE_LIGHT }}>$ </span>
            <span>{visibleText}</span>
            {showCursor && (
              <span
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: '1.2em',
                  background: PURPLE_LIGHT,
                  marginLeft: 2,
                  verticalAlign: 'text-bottom',
                }}
              />
            )}
          </div>
        </div>

        {/* Bottom hint */}
        <div
          style={{
            marginTop: 24,
            fontSize: 14,
            color: GRAY_DIM,
            fontFamily: "'Courier New', monospace",
            opacity: charsToShow > 20 ? 1 : 0,
            transition: 'opacity 0.3s',
          }}
        >
          book-genesis-v4 --run pipeline
        </div>
      </div>
    </div>
  );
};
