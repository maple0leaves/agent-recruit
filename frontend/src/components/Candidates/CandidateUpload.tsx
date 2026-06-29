import {
  useCallback,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type KeyboardEvent,
} from "react";
import { Button } from "@/components/ui/button";
import { useUploadCandidatesBatch } from "@/hooks/useCandidates";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  Upload,
} from "lucide-react";
import type {
  CandidateBatchUploadResponse,
  CandidateUploadFailure,
} from "@/types/candidate";

interface CandidateUploadProps {
  onSuccess?: (result: CandidateBatchUploadResponse) => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ["pdf", "docx"];

function validateFiles(files: File[]) {
  const accepted: File[] = [];
  const failures: CandidateUploadFailure[] = [];

  for (const file of files) {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
      failures.push({
        filename: file.name,
        error: "仅支持 PDF 和 Word (.docx) 格式",
      });
      continue;
    }

    if (file.size > MAX_FILE_SIZE) {
      failures.push({
        filename: file.name,
        error: "单个文件大小不能超过 10MB",
      });
      continue;
    }

    accepted.push(file);
  }

  return { accepted, failures };
}

function mergeFailures(
  result: CandidateBatchUploadResponse,
  clientFailures: CandidateUploadFailure[],
): CandidateBatchUploadResponse {
  const failures = [...clientFailures, ...result.failures];
  return {
    ...result,
    failures,
    failure_count: failures.length,
    total_count: result.items.length + failures.length,
  };
}

function readApiError(err: unknown) {
  if (err && typeof err === "object" && "response" in err) {
    const maybeMessage =
      "message" in err && typeof err.message === "string" ? err.message : undefined;
    const response = (err as {
      response?: { data?: { detail?: string; message?: string } };
    }).response;
    return response?.data?.detail ?? response?.data?.message ?? maybeMessage ?? "上传失败";
  }

  return err instanceof Error ? err.message : "上传失败";
}

export default function CandidateUpload({ onSuccess }: CandidateUploadProps) {
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<CandidateBatchUploadResponse | null>(null);
  const [activeFiles, setActiveFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadCandidatesBatch();

  const resetToIdle = useCallback(() => {
    setUploadState("idle");
    setUploadProgress(0);
    setErrorMessage(null);
    setResult(null);
    setActiveFiles([]);
  }, []);

  const uploadFiles = useCallback(async (files: File[]) => {
    const { accepted, failures: clientFailures } = validateFiles(files);

    setResult(null);
    setErrorMessage(null);
    setActiveFiles(accepted);

    if (accepted.length === 0) {
      setUploadState("error");
      setErrorMessage(clientFailures[0]?.error || "请选择可上传的简历文件");
      setResult({
        items: [],
        failures: clientFailures,
        success_count: 0,
        failure_count: clientFailures.length,
        total_count: clientFailures.length,
      });
      return;
    }

    setUploadState("uploading");
    setUploadProgress(0);

    try {
      const serverResult = await uploadMutation.mutateAsync({
        files: accepted,
        onProgress: (pct) => setUploadProgress(pct),
      });
      const mergedResult = mergeFailures(serverResult, clientFailures);
      setResult(mergedResult);
      setUploadState("done");
      setUploadProgress(100);
      onSuccess?.(mergedResult);
    } catch (err: unknown) {
      setUploadState("error");
      setErrorMessage(readApiError(err));
      if (clientFailures.length > 0) {
        setResult({
          items: [],
          failures: clientFailures,
          success_count: 0,
          failure_count: clientFailures.length,
          total_count: clientFailures.length,
        });
      }
    }
  }, [onSuccess, uploadMutation]);

  const handleFileSelect = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      uploadFiles(files);
    }
    e.target.value = "";
  }, [uploadFiles]);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      uploadFiles(files);
    }
  }, [uploadFiles]);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
  }, []);

  const handleZoneClick = useCallback(() => {
    if (uploadState === "idle") {
      fileInputRef.current?.click();
    }
  }, [uploadState]);

  const handleZoneKeyDown = useCallback((e: KeyboardEvent<HTMLDivElement>) => {
    if ((e.key === "Enter" || e.key === " ") && uploadState === "idle") {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  }, [uploadState]);

  return (
    <div className="w-full">
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf,.docx"
        multiple
        className="hidden"
        onChange={handleFileSelect}
      />

      {uploadState === "idle" && (
        <div
          className="rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 text-center transition-colors hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/70"
          onClick={handleZoneClick}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onKeyDown={handleZoneKeyDown}
          role="button"
          tabIndex={0}
        >
          <Upload className="mx-auto mb-3 size-9 text-muted-foreground" />
          <p className="text-sm font-medium">批量上传简历</p>
          <p className="mt-1 text-xs text-muted-foreground">
            可一次选择或拖入多个 PDF / Word(.docx) 文件，单个文件不超过 10MB
          </p>
        </div>
      )}

      {uploadState === "uploading" && (
        <div className="rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 text-center">
          <Loader2 className="mx-auto mb-3 size-9 animate-spin text-primary" />
          <p className="text-sm font-medium">
            正在上传 {activeFiles.length} 份简历，{uploadProgress}%
          </p>
          <div className="mx-auto mt-3 h-2 w-full max-w-md overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="mx-auto mt-4 grid max-w-md gap-1 text-left text-xs text-muted-foreground">
            {activeFiles.slice(0, 5).map((file) => (
              <div key={`${file.name}-${file.size}`} className="flex items-center gap-2 truncate">
                <FileText className="size-3.5 shrink-0" />
                <span className="truncate">{file.name}</span>
              </div>
            ))}
            {activeFiles.length > 5 && (
              <div>还有 {activeFiles.length - 5} 个文件...</div>
            )}
          </div>
        </div>
      )}

      {uploadState === "done" && result && (
        <div className="rounded-lg border border-border bg-muted/20 p-5">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 size-6 shrink-0 text-green-600" />
            <div>
              <p className="text-sm font-medium">
                已加入后台解析队列：成功 {result.success_count} 份，失败 {result.failure_count} 份
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                候选人会先显示为解析中，AI 解析完成后列表会自动刷新。
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {result.items.length > 0 && (
              <div className="rounded-lg border bg-background p-3">
                <p className="mb-2 text-xs font-medium text-green-700">已入库，后台解析中</p>
                <div className="max-h-32 space-y-1 overflow-y-auto text-xs text-muted-foreground">
                  {result.items.map((item) => (
                    <div key={`${item.id}-${item.filename || item.name}`} className="truncate">
                      {item.filename || item.name || `候选人 #${item.id}`}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.failures.length > 0 && (
              <div className="rounded-lg border bg-background p-3">
                <p className="mb-2 text-xs font-medium text-destructive">上传失败</p>
                <div className="max-h-32 space-y-2 overflow-y-auto text-xs">
                  {result.failures.map((failure) => (
                    <div key={`${failure.filename}-${failure.error}`}>
                      <div className="truncate font-medium">{failure.filename}</div>
                      <div className="text-muted-foreground">{failure.error}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 flex justify-end">
            <Button variant="outline" size="sm" onClick={resetToIdle}>
              继续上传
            </Button>
          </div>
        </div>
      )}

      {uploadState === "error" && (
        <div className="rounded-lg border-2 border-dashed border-destructive/30 bg-destructive/5 p-8 text-center">
          <AlertCircle className="mx-auto mb-2 size-8 text-destructive" />
          <p className="mb-3 text-sm font-medium text-destructive">
            {errorMessage}
          </p>
          {result?.failures.length ? (
            <div className="mx-auto mb-4 max-w-md rounded-lg border bg-background p-3 text-left text-xs">
              {result.failures.map((failure) => (
                <div key={`${failure.filename}-${failure.error}`} className="mb-2 last:mb-0">
                  <div className="font-medium">{failure.filename}</div>
                  <div className="text-muted-foreground">{failure.error}</div>
                </div>
              ))}
            </div>
          ) : null}
          <Button variant="outline" size="sm" onClick={resetToIdle}>
            重新选择
          </Button>
        </div>
      )}
    </div>
  );
}
