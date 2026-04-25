"use client";

export function ShortcutSettingsOverview({
  tabQuickGenerationEnabled,
}: {
  tabQuickGenerationEnabled: boolean;
}) {
  return (
    <section className="settings-overview">
      <article className="settings-card">
        <span>正文 Tab 快速生成</span>
        <strong>{tabQuickGenerationEnabled ? "已启用" : "已关闭"}</strong>
        <p>正文框聚焦时，Tab 会按写作台右侧栏设置直接生成并应用到光标位置。</p>
      </article>
    </section>
  );
}

export function ShortcutSettingsDetail({
  onChange,
  tabQuickGenerationEnabled,
}: {
  onChange: (enabled: boolean) => void;
  tabQuickGenerationEnabled: boolean;
}) {
  return (
    <>
      <div className="detail-heading">
        <div>
          <p className="eyebrow">Keyboard</p>
          <h2>快捷键设置</h2>
        </div>
      </div>

      <div className="api-config-form shortcut-settings-form">
        <p className="detail-description">
          仅在正文编辑框聚焦时生效；有待确认生成、弹窗或输入法组合中不会触发。
        </p>

        <label className="settings-check">
          <input
            checked={tabQuickGenerationEnabled}
            onChange={(event) => onChange(event.target.checked)}
            type="checkbox"
          />
          <span>启用正文 Tab 快速生成</span>
        </label>

        <p className="empty-note">
          快速生成使用写作台右侧栏里的设置，模型、Temperature、提示词和作者人格会在所有章节复用。
        </p>
      </div>
    </>
  );
}
