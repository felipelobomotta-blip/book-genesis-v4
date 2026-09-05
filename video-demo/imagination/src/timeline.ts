import timing from './timing.json';

export type TimelineSceneId = 'hook' | 'setup' | 'start' | 'checkpoint' | 'reader' | 'export' | 'cta';

export type TimelineScene = {
  id: TimelineSceneId;
  caption: string;
  voice: string;
  frames: number;
};

export const fps = timing.fps;
export const longTimeline = timing.long as TimelineScene[];
export const shortTimeline = timing.short as TimelineScene[];
export const totalFrames = (timeline: TimelineScene[]) => timeline.reduce((sum, scene) => sum + scene.frames, 0);
