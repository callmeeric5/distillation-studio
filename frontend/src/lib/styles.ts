import type { ProjectStatus, RunState } from '../types/projects';

export const statusStyles: Record<RunState['status'], string> = {
  idle: 'border-[#dedbd0] bg-[#f4f1e8] text-[#6f6a5f]',
  running: 'border-[#d2c9b7] bg-[#f7f2e8] text-[#7a5139]',
  success: 'border-[#c9d1bd] bg-[#eef3e8] text-[#4d5f39]',
  error: 'border-[#dec6b5] bg-[#fbede5] text-[#8a4429]',
};

export const projectStatusStyles: Record<ProjectStatus, string> = {
  ready: 'bg-[#e8eee0] text-[#415234] ring-[#cfd8c4]',
  'coming soon': 'bg-[#dfe8f0] text-[#36546d] ring-[#c9d7e2]',
  'in progress': 'bg-[#f3dfd2] text-[#8a4429] ring-[#e4c2ae]',
};
