import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {shortTimeline, TimelineScene} from './timeline';
import {Hero} from './scenes/Hero';
import {ProductScene} from './scenes/ProductScene';
import {CheckpointScene} from './scenes/CheckpointScene';
import {Closing} from './scenes/Closing';

const sceneComponent = (scene: TimelineScene): React.ReactNode => {
  switch (scene.id) {
    case 'hook': return <Hero short />;
    case 'setup': return <ProductScene short eyebrow="Connect your tools" title="Connect your model route." body="Install Python 3.10+, then run book-genesis setup to connect a supported route." asset="capture-setup.png" alt="Book Genesis setup help capture" active={0} caption={scene.caption} />;
    case 'start': return <ProductScene short eyebrow="Start with an idea" title="Start with one sentence." body="Use book-genesis new to turn a premise into a guided project." asset="capture-start.png" alt="Book Genesis new-project capture" active={1} caption={scene.caption} />;
    case 'checkpoint': return <CheckpointScene short caption={scene.caption} />;
    case 'reader': return <ProductScene short eyebrow="Read the version" title="See the manuscript change." body="A local reader shows the working draft and its revisions." asset="reader-mobile.mp4" alt="Mobile local reader interaction capture" kind="video" mobile active={3} caption={scene.caption} />;
    case 'export': return <ProductScene short eyebrow="Keep the work" title="Export the manuscript." body="Export accepted chapters as Markdown or EPUB. Partial work stays clearly labeled." asset="capture-export.png" alt="Book Genesis export capture" active={4} caption={scene.caption} />;
    case 'cta': return <Closing short />;
  }
};

export const Short: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill>
      {shortTimeline.map((scene) => {
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
