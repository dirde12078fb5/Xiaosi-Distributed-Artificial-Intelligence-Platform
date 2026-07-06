package com.xiaosi.nas.util;

import lombok.experimental.UtilityClass;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

@UtilityClass
public class FileUtils {

    public String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf(".") + 1).toLowerCase();
    }

    public String getMimeType(String filename) {
        String ext = getFileExtension(filename);
        return switch (ext) {
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "gif" -> "image/gif";
            case "bmp" -> "image/bmp";
            case "webp" -> "image/webp";
            case "svg" -> "image/svg+xml";
            case "pdf" -> "application/pdf";
            case "doc", "docx" -> "application/msword";
            case "xls", "xlsx" -> "application/vnd.ms-excel";
            case "ppt", "pptx" -> "application/vnd.ms-powerpoint";
            case "zip" -> "application/zip";
            case "rar" -> "application/x-rar-compressed";
            case "7z" -> "application/x-7z-compressed";
            case "mp3" -> "audio/mpeg";
            case "mp4" -> "video/mp4";
            case "avi" -> "video/x-msvideo";
            case "mkv" -> "video/x-matroska";
            case "txt" -> "text/plain";
            case "html", "htm" -> "text/html";
            case "css" -> "text/css";
            case "js" -> "application/javascript";
            case "json" -> "application/json";
            case "xml" -> "application/xml";
            case "java" -> "text/x-java-source";
            case "py" -> "text/x-python";
            default -> "application/octet-stream";
        };
    }

    public String formatFileSize(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        } else if (bytes < 1024 * 1024) {
            return String.format("%.2f KB", bytes / 1024.0);
        } else if (bytes < 1024 * 1024 * 1024) {
            return String.format("%.2f MB", bytes / (1024.0 * 1024));
        } else {
            return String.format("%.2f GB", bytes / (1024.0 * 1024 * 1024));
        }
    }

    public String generateUniqueFilename(String originalFilename) {
        String extension = getFileExtension(originalFilename);
        String uuid = UUID.randomUUID().toString().substring(0, 8);
        String baseName = originalFilename.substring(0, originalFilename.lastIndexOf(".") != -1 ? originalFilename.lastIndexOf(".") : originalFilename.length());
        return baseName + "_" + uuid + (extension.isEmpty() ? "" : "." + extension);
    }

    public boolean isImageFile(String filename) {
        String ext = getFileExtension(filename);
        return ext.equals("jpg") || ext.equals("jpeg") || ext.equals("png") || ext.equals("gif") || ext.equals("bmp") || ext.equals("webp") || ext.equals("svg");
    }

    public boolean isVideoFile(String filename) {
        String ext = getFileExtension(filename);
        return ext.equals("mp4") || ext.equals("avi") || ext.equals("mkv") || ext.equals("mov") || ext.equals("wmv") || ext.equals("flv");
    }

    public boolean isAudioFile(String filename) {
        String ext = getFileExtension(filename);
        return ext.equals("mp3") || ext.equals("wav") || ext.equals("ogg") || ext.equals("flac") || ext.equals("aac");
    }

    public boolean isDocumentFile(String filename) {
        String ext = getFileExtension(filename);
        return ext.equals("pdf") || ext.equals("doc") || ext.equals("docx") || ext.equals("xls") || ext.equals("xlsx") || ext.equals("ppt") || ext.equals("pptx") || ext.equals("txt");
    }

    public boolean isArchiveFile(String filename) {
        String ext = getFileExtension(filename);
        return ext.equals("zip") || ext.equals("rar") || ext.equals("7z") || ext.equals("tar") || ext.equals("gz");
    }

    public boolean ensureDirectoryExists(String path) {
        try {
            Path dir = Paths.get(path);
            if (!Files.exists(dir)) {
                Files.createDirectories(dir);
                return true;
            }
            return Files.isDirectory(dir);
        } catch (Exception e) {
            return false;
        }
    }

    public boolean deleteDirectory(File directory) {
        if (!directory.exists()) {
            return true;
        }
        File[] files = directory.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    deleteDirectory(file);
                } else {
                    file.delete();
                }
            }
        }
        return directory.delete();
    }
}