/**
 * 与 site/tokens.css 同步的 TS token，供 Ant Design theme、图表等使用。
 * 修改颜色时请同时更新 site/tokens.css 中的 :root。
 */

export const mdColors = {
  primary: "#fff100",
  primaryHover: "#fff456",
  primaryActive: "#e6dc00",
  black: "#0d0d0d",
  purple: "#7d66ff",
  orange: "#ff6900",
  blue: "#2eafff",
  green: "#00c770",
  bg: "#ffffff",
  bgMuted: "#fafafa",
  bgPage: "#fafafa",
  code: "#1e1e1e",
  text: "rgba(13, 13, 13, 0.92)",
  textSecondary: "#626262",
  border: "#d4d4d4",
  borderSplit: "#e5e5e5",
} as const;

export const mdRadius = {
  sm: 8,
  md: 12,
  lg: 16,
} as const;

export const mdLayout = {
  maxWidth: 1200,
  sidebarWidth: 280,
  topbarHeight: 64,
} as const;
