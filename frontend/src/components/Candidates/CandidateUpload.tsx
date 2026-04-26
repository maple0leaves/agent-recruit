import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { useUploadCandidate } from "@/hooks/useCandidates";
import { Upload, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import type { CandidateUploadResponse } from "@/types/candidate";

interface CandidateUploadProps {
  onSuccess?: (candidate: CandidateUploadResponse) => void;
}

export default function CandidateUpload({ onSuccess }: CandidateUploadProps) {
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successName, setSuccessName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadCandidate();

  const resetToIdle = useCallback(() => {
    setUploadState("idle");
    setUploadProgress(0);
    setErrorMessage(null);
    setSuccessName(null);
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "docx"].includes(ext)) {
      setUploadState("error");
      setErrorMessage("仅支持 PDF 和 Word (.docx) 格式");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadState("error");
      setErrorMessage("文件大小不能超过 10MB");
      return;
    }

    setUploadState("uploading");
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      const result = await uploadMutation.mutateAsync({
        file,
        onProgress: (pct) => setUploadProgress(pct),
      });
      setUploadState("success");
      setSuccessName(result.name);
      setTimeout(() => resetToIdle(), 3000);
      onSuccess?.(result);
    } catch (err: unknown) {
      setUploadState("error");
      const message =
        err && typeof err === "object" && "response" in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            (err as Error).message ??
            "上传失败")
          : err instanceof Error
            ? err.message
            : "上传失败";
      setErrorMessage(message);
    }
  }, [uploadMutation, onSuccess, resetToIdle]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = "";
  }, [uploadFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  }, [uploadFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleZoneClick = useCallback(() => {
    if (uploadState === "idle") {
      fileInputRef.current?.click();
    }
  }, [uploadState]);

  return (
    <div className="w-full">
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleFileSelect}
      />

      {uploadState === "idle" && (
        <div
          className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
          onClick={handleZoneClick}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm font-medium">上传简历</p>
          <p className="text-xs text-muted-foreground mt-1">
            支持 PDF、Word 格式，单文件不超过 10MB
          </p>
        </div>
      )}

      {uploadState === "uploading" && (
        <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
          <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin text-primary" />
          <p className="text-sm font-medium">上传中 {uploadProgress}%</p>
          <div className="mt-3 h-2 w-full max-w-xs mx-auto bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {uploadState === "success" && (
        <div className="border-2 border-dashed border-green-300 rounded-lg p-8 text-center bg-green-50/50">
          <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-600" />
          <p className="text-sm font-medium text-green-700">
            上传成功：{successName}
          </p>
        </div>
      )}

      {uploadState === "error" && (
        <div className="border-2 border-dashed border-destructive/30 rounded-lg p-8 text-center bg-destructive/5">
          <AlertCircle className="h-8 w-8 mx-auto mb-2 text-destructive" />
          <p className="text-sm font-medium text-destructive mb-3">
            {errorMessage}
          </p>
          <Button variant="outline" size="sm" onClick={resetToIdle}>
            重试
          </Button>
        </div>
      )}
    </div>
  );
}
