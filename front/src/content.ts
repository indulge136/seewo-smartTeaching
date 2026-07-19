export type NavItem = {
  label: string;
  href: string;
};

export type Metric = {
  value: string;
  label: string;
  detail: string;
};

export const navItems: NavItem[] = [
  { label: 'AI批改', href: '#' },
  { label: '模型优势', href: '#' },
  { label: '教学场景', href: '#' },
  { label: '资源中心', href: '#' },
  { label: '版本方案', href: '#' }
];

export const heroMetrics: Metric[] = [
  { value: '50万+', label: '累计批改', detail: '50万+份作业' },
  { value: '10000+', label: '覆盖全国', detail: '10000+中小学' },
  { value: '3秒', label: '单份作业', detail: '秒完成AI初判' }
];
