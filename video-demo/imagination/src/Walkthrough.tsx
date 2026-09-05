import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {longTimeline, TimelineScene} from './timeline';
import {Hero} from './scenes/Hero';
import {ProductScene} from './scenes/ProductScene';
import {CheckpointScene} from './scenes/CheckpointScene';
import {Closing} from './scenes/Closing';

const sceneComponent = (scene: TimelineScene): React.ReactNode => {
  switch (scene.id) {
    case 'hook': return <Hero />;
    case 'setup': return <ProductScene eyebrow="Connect your tools" title="Use the provider you already have." body="Install with Python 3.10 or newer, then run book-genesis setup to choose a supported model route." asset="capture-setup.png" alt="Book Genesis setup help capture" active={0} caption={scene.caption} />;
    case 'start': return <ProductScene eyebrow="Start with an idea" title="Give the story one sentence." body="Run book-genesis new, add your premise, and choose the language for the manuscript." asset="capture-start.png" alt="Book Genesis new-project capture" active={1} caption={scene.caption} />;
    case 'checkpoint': return <CheckpointScene caption={scene.caption} />;
    case 'reader': return <ProductScene eyebrow="Read the change" title="Follow the work, version by version." body="The local reader keeps the draft and its revision history close enough to inspect." asset="reader-desktop.mp4" alt="Local reader interaction capture" kind="video" active={3} caption={scene.caption} />;
    case 'export': return <ProductScene eyebrow="Keep the result" title="Export the working manuscript." body="Export accepted chapters as Markdown or EPUB. Incomplete projects are labeled as partial." asset="capture-export.png" alt="Book Genesis export capture" active={4} caption={scene.caption} />;
    case 'cta': return <Closing />;
  }
};

export const Walkthrough: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill>
      {longTimeline.map((scene) => {
        const sceneFrom = from;
        from += scene.frames;
        return <Sequence key={scene.id} from={sceneFrom} durationInFrames={scene.frames} name={scene.id}>
          <Audio src={staticFile(scene.voice)} />
          {sceneComponent(scene)}
        </Sequence>;
      })}
    </AbsoluteFill>
  );
};
