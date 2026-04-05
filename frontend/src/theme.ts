import type { ThemeConfig } from "antd";

import { mdColors, mdRadius } from "@site/tokens";

/** Ant Design 与 site/tokens.ts 对齐 */
export const mdTheme: ThemeConfig = {
  token: {
    colorPrimary: mdColors.primary,
    colorInfo: mdColors.blue,
    colorSuccess: mdColors.green,
    colorWarning: mdColors.orange,
    colorError: "#e11d48",
    colorText: mdColors.text,
    colorTextSecondary: mdColors.textSecondary,
    colorTextDescription: mdColors.textSecondary,
    colorBorder: mdColors.border,
    colorSplit: mdColors.borderSplit,
    borderRadius: mdRadius.sm,
    fontFamily: `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`,
    fontSize: 15,
    lineHeight: 1.55,
    controlHeight: 40,
    wireframe: false,
  },
  components: {
    Button: {
      primaryColor: mdColors.black,
      colorPrimary: mdColors.primary,
      colorPrimaryHover: mdColors.primaryHover,
      colorPrimaryActive: mdColors.primaryActive,
      fontWeight: 600,
      borderRadius: mdRadius.sm,
      controlHeight: 44,
      paddingContentHorizontal: 24,
    },
    Input: {
      hoverBorderColor: mdColors.purple,
      activeBorderColor: mdColors.purple,
      activeShadow: "0 0 0 3px rgba(125, 102, 255, 0.2)",
    },
    Card: {
      borderRadiusLG: mdRadius.md,
      paddingLG: 24,
    },
    Table: {
      headerBg: mdColors.bgMuted,
      headerColor: "rgba(13, 13, 13, 0.85)",
      rowHoverBg: "rgba(255, 241, 0, 0.12)",
    },
  },
};
