"use client";

import type { PromptPreviewResponse } from "@/lib/api/index";
import { formatMaterialSource } from "../../utils";

export function PromptPreviewMaterials({
  item,
}: {
  item: PromptPreviewResponse["items"][number];
}) {
  return (
    <div className="preview-material-grid">
      <PreviewMaterialList title="章节素材" materials={item.chapters} />
      <PreviewMaterialList title="资料素材" materials={item.documents} />
    </div>
  );
}

function PreviewMaterialList({
  materials,
  title,
}: {
  materials: PromptPreviewResponse["items"][number]["chapters"];
  title: string;
}) {
  return (
    <section className="preview-material-list">
      <h3>{title}</h3>
      {materials.length ? (
        materials.map((material) => (
          <article key={`${material.id}-${material.source}`}>
            <strong>{material.title}</strong>
            <span>{material.id}</span>
            <small>
              {formatMaterialSource(material.source)} · {material.content_mode} ·{" "}
              {material.token_estimate} token · {material.chars} 字符
              {material.truncated ? " · 已截断" : ""}
            </small>
          </article>
        ))
      ) : (
        <p>未选取素材。</p>
      )}
    </section>
  );
}
