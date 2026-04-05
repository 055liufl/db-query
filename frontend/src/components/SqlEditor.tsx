import Editor from "@monaco-editor/react";

export function SqlEditor(props: {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  /** 深色代码区与 style.md「code / bg dark」一致 */
  theme?: "vs" | "vs-dark";
}) {
  const { value, onChange, height, theme } = props;
  return (
    <Editor
      height={height ?? "280px"}
      defaultLanguage="sql"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      theme={theme ?? "vs-dark"}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineHeight: 22,
        wordWrap: "on",
        scrollBeyondLastLine: false,
        padding: { top: 16, bottom: 16 },
        fontFamily: '"JetBrains Mono", "Fira Code", "SF Mono", ui-monospace, monospace',
        cursorBlinking: "smooth",
        smoothScrolling: true,
      }}
    />
  );
}
