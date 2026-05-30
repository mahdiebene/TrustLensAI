import { DocsClient } from "@/app/docs/DocsClient";
import { evaluateDocsAccess, resolvePublishWindow } from "@/lib/docs/access";
import { getDocsLiveState } from "@/lib/docs/live";
import { readDocsConfig, readDocsContent, readDocsVersions } from "@/lib/docs/storage";

export const dynamic = "force-dynamic";

export default async function DocsPage() {
  const [config, content, versions] = await Promise.all([
    readDocsConfig(),
    readDocsContent(),
    readDocsVersions(),
  ]);

  const access = evaluateDocsAccess(config);
  if (!access.isPublic) {
    const window = resolvePublishWindow(config);

    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="section-surface max-w-2xl p-8 text-center">
          <p className="text-caption uppercase caps-wide text-text-tertiary">Documentation Access</p>
          <h1 className="text-page-section font-semibold heading-tight text-text-primary mt-2">Not Available</h1>
          <p className="text-body text-text-secondary mt-3">
            Public documentation is currently unavailable. Reason: {access.reason.replace("_", " ")}.
          </p>
          <p className="text-caption text-text-tertiary mt-4">
            Window: {window.start.toLocaleString()} to {window.end.toLocaleString()}
          </p>
        </div>
      </div>
    );
  }

  const live = await getDocsLiveState(content, versions);
  return <DocsClient content={content} visibility={config} access={access} live={live} versions={versions} />;
}
