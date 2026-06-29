package com.agentrecruit.match.export;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.match.entity.MatchSession;
import com.agentrecruit.match.mapper.MatchSessionMapper;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/matching")
public class ExportController {

    private final MatchSessionMapper matchSessionMapper;
    private final PdfReportService pdfReportService;
    private final ExcelReportService excelReportService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ExportController(MatchSessionMapper matchSessionMapper, PdfReportService pdfReportService,
                            ExcelReportService excelReportService) {
        this.matchSessionMapper = matchSessionMapper;
        this.pdfReportService = pdfReportService;
        this.excelReportService = excelReportService;
    }

    @GetMapping("/{sessionId}/export/pdf")
    public ResponseEntity<Resource> exportPdf(@PathVariable Long sessionId) {
        MatchSession session = require(sessionId);
        List<Map<String, Object>> candidates = parseResults(session.getResultsJson());
        String matchDate = session.getCreatedAt() != null
                ? session.getCreatedAt().toLocalDate().format(DateTimeFormatter.ISO_DATE)
                : LocalDate.now().format(DateTimeFormatter.ISO_DATE);
        byte[] pdf = pdfReportService.generate("Session #" + sessionId, matchDate, candidates);
        return download(pdf, "match-report-" + sessionId + ".pdf", MediaType.APPLICATION_PDF);
    }

    @GetMapping("/{sessionId}/export/excel")
    public ResponseEntity<Resource> exportExcel(@PathVariable Long sessionId) {
        MatchSession session = require(sessionId);
        List<Map<String, Object>> candidates = parseResults(session.getResultsJson());
        byte[] xlsx = excelReportService.generate(candidates);
        return download(xlsx, "match-report-" + sessionId + ".xlsx",
                MediaType.parseMediaType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"));
    }

    private ResponseEntity<Resource> download(byte[] data, String filename, MediaType mediaType) {
        return ResponseEntity.ok()
                .contentType(mediaType)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
                .contentLength(data.length)
                .body(new ByteArrayResource(data));
    }

    private MatchSession require(Long id) {
        MatchSession session = matchSessionMapper.selectById(id);
        if (session == null) {
            throw ApiException.notFound("匹配会话不存在");
        }
        return session;
    }

    private List<Map<String, Object>> parseResults(String resultsJson) {
        if (!StringUtils.hasText(resultsJson)) {
            return List.of();
        }
        try {
            return objectMapper.readValue(resultsJson, new TypeReference<>() {
            });
        } catch (Exception e) {
            throw new ApiException(500, "解析匹配结果失败：" + e.getMessage());
        }
    }
}
