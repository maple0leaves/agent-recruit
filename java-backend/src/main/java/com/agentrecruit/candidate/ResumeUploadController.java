package com.agentrecruit.candidate;

import com.agentrecruit.common.ApiException;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * /api/upload-resume：单份简历文本提取（PDF/TXT），供"单简历直通"流程使用。
 * 纯文本提取，不调用 AI，故放在 Java 侧实现。
 */
@RestController
public class ResumeUploadController {

    private final ResumeParser resumeParser;

    public ResumeUploadController(ResumeParser resumeParser) {
        this.resumeParser = resumeParser;
    }

    @PostMapping("/api/upload-resume")
    public Map<String, Object> uploadResume(@RequestParam("file") MultipartFile file) {
        String filename = file.getOriginalFilename() == null ? "" : file.getOriginalFilename();
        String lower = filename.toLowerCase();
        if (!(lower.endsWith(".pdf") || lower.endsWith(".txt"))) {
            throw ApiException.badRequest("仅支持 .pdf 或 .txt 格式的简历文件");
        }

        byte[] raw;
        try {
            raw = file.getBytes();
        } catch (IOException e) {
            throw ApiException.badRequest("读取文件失败");
        }
        if (raw.length == 0) {
            throw ApiException.badRequest("文件内容为空");
        }

        int pageCount = 1;
        String text;
        if (lower.endsWith(".pdf")) {
            ResumeParser.PdfResult result = resumeParser.extractPdf(raw);
            pageCount = result.pages();
            text = result.text();
        } else {
            text = decodeText(raw);
        }

        if (!StringUtils.hasText(text)) {
            throw new ApiException(422, "未能从文件中提取到文字内容（可能是扫描版图片 PDF，暂不支持）");
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("text", text.strip());
        body.put("filename", file.getOriginalFilename());
        body.put("pages", pageCount);
        return body;
    }

    private String decodeText(byte[] raw) {
        try {
            return new String(raw, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return new String(raw, Charset.forName("GBK"));
        }
    }
}
