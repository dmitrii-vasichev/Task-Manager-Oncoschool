"use client";

import { useState, useRef } from "react";
import { Upload, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { api } from "@/lib/api";

interface AvatarUploadProps {
  memberId: string;
  currentAvatarUrl: string | null;
  memberName: string;
  onAvatarChange: (newUrl: string | null) => void;
}

export function AvatarUpload({ memberId, currentAvatarUrl, memberName, onAvatarChange }: AvatarUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isCustomAvatar = currentAvatarUrl?.includes("/static/avatars/");

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    try {
      const result = await api.uploadAvatar(memberId, selectedFile);
      onAvatarChange(result.avatar_url);
      setPreview(null);
      setSelectedFile(null);
    } catch {
      // error handled by caller
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    setUploading(true);
    try {
      await api.deleteAvatar(memberId);
      onAvatarChange(null);
    } catch {
      // error handled by caller
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setPreview(null);
    setSelectedFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {preview ? (
        <div className="h-20 w-20 rounded-full overflow-hidden ring-2 ring-primary/30">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="Preview" className="h-full w-full object-cover" />
        </div>
      ) : (
        <UserAvatar name={memberName} avatarUrl={currentAvatarUrl} size="xl" />
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleFileSelect}
      />

      <div className="flex items-center gap-2">
        {preview ? (
          <>
            <Button
              size="sm"
              variant="default"
              className="rounded-xl gap-1.5"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Upload className="h-3.5 w-3.5" />
              )}
              Сохранить
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="rounded-xl"
              onClick={handleCancel}
              disabled={uploading}
            >
              Отмена
            </Button>
          </>
        ) : (
          <>
            <Button
              size="sm"
              variant="outline"
              className="rounded-xl gap-1.5"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
            >
              <Upload className="h-3.5 w-3.5" />
              Загрузить
            </Button>
            {isCustomAvatar && (
              <Button
                size="sm"
                variant="outline"
                className="rounded-xl gap-1.5 text-destructive hover:text-destructive"
                onClick={handleDelete}
                disabled={uploading}
              >
                {uploading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
                Удалить
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
