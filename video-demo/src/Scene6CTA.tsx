import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { BG, WHITE, PURPLE_LIGHT, GRAY, GRAY_DIM } from './constants';

export const Scene6CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const labelFade = interpolate(frame, [0, fps * 0.5], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const urlFade = interpolate(frame, [fps * 0.3, fps * 0.9], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const urlSlide = interpolate(frame, [fps * 0.3, fps * 0.9], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const starFade = interpolate(frame, [fps * 0.8, fps * 1.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Subtle pulse on the URL box
  const pulse = interpolate(
    Math.sin((frame / fps) * Math.PI * 1.5),
    [-1, 1],
    [0.6, 1.0]
  );

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
      {/* Grid bg */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div style={{ textAlign: 'center', zIndex: 1, maxWidth: 900 }}>
        {/* Label */}
        <div
          style={{
            opacity: labelFade,
            fontSize: 13,
            fontFamily: "'Courier New', monospace",
            color: GRAY_DIM,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            marginBottom: 28,
          }}
        >
          open source · build in public
        </div>

        {/* URL box */}
        <div
          style={{
            opacity: urlFade,
            transform: `translateY(${urlSlide}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              background: `rgba(124,58,237,${0.08 + 0.04 * pulse})`,
              border: `1px solid rgba(124,58,237,${0.2 + 0.15 * pulse})`,
              borderRadius: 14,
              padding: '20px 36px',
            }}
          >
            {/* GitHub icon */}
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill={PURPLE_LIGHT}
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>

            <span
              style={{
                fontFamily: "'Courier New', monospace",
                fontSize: 22,
                color: WHITE,
                letterSpacing: '0.02em',
              }}
            >
              github.com/felipelobomotta-blip/book-genesis-v4
            </span>
          </div>
        </div>

        {/* Star nudge */}
        <div
          style={{
            opacity: starFade,
            marginTop: 24,
            fontSize: 14,
            color: GRAY_DIM,
            fontFamily: "'Courier New', monospace",
            letterSpacing: '0.06em',
          }}
        >
          ⭐ star the repo · contributions welcome
        </div>
      </div>
    </div>
  );
};
