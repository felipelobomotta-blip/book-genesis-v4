import React from 'react';
import {Composition, Folder} from 'remotion';
import {Walkthrough} from './Walkthrough';
import {Short} from './Short';
import {Hero} from './scenes/Hero';
import {IdeaScene} from './scenes/IdeaScene';
import {Closing} from './scenes/Closing';
import {longTimeline, shortTimeline, totalFrames} from './timeline';

export const RemotionRoot: React.FC = () => (
  <>
    <Folder name="Book-Genesis-5-scenes">
      <Composition id="BG-Hook" component={Hero} durationInFrames={210} fps={30} width={1920} height={1080} />
      <Composition id="BG-Idea" component={IdeaScene} durationInFrames={250} fps={30} width={1920} height={1080} />
      <Composition id="BG-Closing" component={Closing} durationInFrames={140} fps={30} width={1920} height={1080} />
    </Folder>
    <Composition id="BookGenesisWalkthrough" component={Walkthrough} durationInFrames={totalFrames(longTimeline)} fps={30} width={1920} height={1080} defaultProps={{}} />
    <Composition id="BookGenesisShort" component={Short} durationInFrames={totalFrames(shortTimeline)} fps={30} width={1080} height={1920} defaultProps={{}} />
  </>
);
