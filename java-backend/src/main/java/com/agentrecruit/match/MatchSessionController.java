package com.agentrecruit.match;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.jd.entity.Jd;
import com.agentrecruit.jd.mapper.JdMapper;
import com.agentrecruit.match.entity.MatchSession;
import com.agentrecruit.match.mapper.MatchSessionMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@RestController
public class MatchSessionController {

    private final MatchSessionMapper matchSessionMapper;
    private final JdMapper jdMapper;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final String resumeDir;

    public MatchSessionController(MatchSessionMapper matchSessionMapper,
                                  JdMapper jdMapper,
                                  @Value("${app.resume.dir}") String resumeDir) {
        this.matchSessionMapper = matchSessionMapper;
        this.jdMapper = jdMapper;
        this.resumeDir = resumeDir;
    }

    @GetMapping("/api/match-sessions")
    public Map<String, Object> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(name = "jd_id", required = false) Long jdId,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<MatchSession> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(status)) {
            wrapper.eq(MatchSession::getStatus, status);
        }
        if (jdId != null) {
            wrapper.eq(MatchSession::getJdId, jdId);
        }
        wrapper.orderByDesc(MatchSession::getCreatedAt);

        if (StringUtils.hasText(keyword)) {
            String normalizedKeyword = keyword.strip().toLowerCase();
            List<Map<String, Object>> filtered = matchSessionMapper.selectList(wrapper).stream()
                    .filter(session -> matchesKeyword(session, normalizedKeyword))
                    .map(this::toSummary)
                    .toList();

            int safePage = Math.max(1, page);
            int safePageSize = Math.max(1, pageSize);
            int fromIndex = Math.min((safePage - 1) * safePageSize, filtered.size());
            int toIndex = Math.min(fromIndex + safePageSize, filtered.size());

            Map<String, Object> body = new LinkedHashMap<>();
            body.put("items", filtered.subList(fromIndex, toIndex));
            body.put("total", filtered.size());
            body.put("page", safePage);
            body.put("page_size", safePageSize);
            return body;
        }

        Page<MatchSession> result = matchSessionMapper.selectPage(Page.of(page, pageSize), wrapper);

        List<Map<String, Object>> items = result.getRecords().stream()
                .map(this::toSummary)
                .toList();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("items", items);
        body.put("total", result.getTotal());
        body.put("page", page);
        body.put("page_size", pageSize);
        return body;
    }

    private boolean matchesKeyword(MatchSession session, String keyword) {
        if (!StringUtils.hasText(keyword)) {
            return true;
        }

        StringBuilder text = new StringBuilder();
        text.append(defaultString(String.valueOf(session.getId()))).append(' ');
        text.append(defaultString(session.getThreadId())).append(' ');
        text.append(defaultString(session.getStatus())).append(' ');
        text.append(defaultString(getJdTitle(session.getJdId()))).append(' ');
        text.append(defaultString(session.getResultsJson())).append(' ');
        if (session.getCreatedAt() != null) {
            text.append(session.getCreatedAt());
        }

        return text.toString().toLowerCase().contains(keyword);
    }

    @GetMapping("/api/match-sessions/{id}")
    public Map<String, Object> detail(@PathVariable Long id) {
        return toDetail(require(id));
    }

    @DeleteMapping("/api/match-sessions/{id}")
    public Map<String, String> delete(@PathVariable Long id) {
        require(id);
        matchSessionMapper.deleteById(id);
        return Map.of("message", "deleted");
    }

    @GetMapping("/api/match-sessions/{id}/resume")
    public ResponseEntity<Resource> previewResume(@PathVariable Long id,
                                                  @RequestParam("candidate_name") String candidateName) {
        MatchSession session = require(id);
        Map<String, Object> result = findResultByCandidateName(session, candidateName);
        Path resumePath = resolveResumePath(asText(result.get("resume_source")));
        if (resumePath == null) {
            throw ApiException.notFound("原始简历文件不存在");
        }

        String filename = resumePath.getFileName().toString();
        if (!filename.toLowerCase().endsWith(".pdf")) {
            throw new ApiException(415, "目前仅支持预览 PDF 简历");
        }

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"resume.pdf\"")
                .header(HttpHeaders.CACHE_CONTROL, "private, max-age=300")
                .body(new FileSystemResource(resumePath));
    }

    @PatchMapping("/api/match-sessions/{id}/review")
    public Map<String, Object> review(@PathVariable Long id, @RequestBody ReviewRequest request) {
        MatchSession session = require(id);
        List<ReviewDecision> approvals = request == null ? List.of() : request.approvals();
        if (approvals == null || approvals.isEmpty()) {
            throw new ApiException(422, "请至少审核一位候选人");
        }

        Map<String, ReviewDecision> decisionsByCandidate = approvals.stream()
                .filter(Objects::nonNull)
                .filter(decision -> StringUtils.hasText(decision.candidateName()))
                .collect(Collectors.toMap(
                        decision -> decision.candidateName().trim(),
                        decision -> decision,
                        (existing, replacement) -> replacement,
                        LinkedHashMap::new
                ));

        List<Map<String, Object>> results = parseResults(session.getResultsJson());
        for (Map<String, Object> result : results) {
            String candidateName = asText(result.get("candidate_name"));
            ReviewDecision decision = decisionsByCandidate.get(candidateName);
            if (decision == null) {
                continue;
            }

            result.put("review_status", decision.approved() ? "approved" : "rejected");
            result.put("review_feedback", defaultString(decision.feedback()));
        }

        int approvedCount = 0;
        int rejectedCount = 0;
        int reviewedCount = 0;
        for (Map<String, Object> result : results) {
            String reviewStatus = asText(result.get("review_status"));
            if ("approved".equals(reviewStatus)) {
                approvedCount++;
                reviewedCount++;
            } else if ("rejected".equals(reviewStatus)) {
                rejectedCount++;
                reviewedCount++;
            }
        }

        session.setApprovedCount(approvedCount);
        session.setRejectedCount(rejectedCount);
        session.setTotalCandidates(Math.max(defaultInt(session.getTotalCandidates()), results.size()));
        session.setStatus(results.isEmpty() || reviewedCount < results.size() ? "pending" : "completed");
        session.setUpdatedAt(LocalDateTime.now());
        session.setResultsJson(writeResults(results));
        matchSessionMapper.updateById(session);

        return toDetail(session);
    }

    private MatchSession require(Long id) {
        MatchSession session = matchSessionMapper.selectById(id);
        if (session == null) {
            throw ApiException.notFound("匹配记录不存在");
        }
        return session;
    }

    private Map<String, Object> toSummary(MatchSession session) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", session.getId());
        item.put("jd_id", session.getJdId());
        item.put("jd_title", getJdTitle(session.getJdId()));
        item.put("candidate_id", session.getCandidateId());
        item.put("thread_id", session.getThreadId());
        item.put("status", session.getStatus());
        item.put("total_candidates", defaultInt(session.getTotalCandidates()));
        item.put("approved_count", defaultInt(session.getApprovedCount()));
        item.put("rejected_count", defaultInt(session.getRejectedCount()));
        item.put("created_at", session.getCreatedAt() == null ? null : session.getCreatedAt().toString());
        item.put("updated_at", session.getUpdatedAt() == null ? null : session.getUpdatedAt().toString());
        return item;
    }

    private Map<String, Object> toDetail(MatchSession session) {
        Map<String, Object> item = toSummary(session);
        item.put("results", parseResults(session.getResultsJson()));
        return item;
    }

    private String getJdTitle(Long jdId) {
        if (jdId == null) {
            return null;
        }
        Jd jd = jdMapper.selectById(jdId);
        return jd == null ? null : jd.getTitle();
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

    private Map<String, Object> findResultByCandidateName(MatchSession session, String candidateName) {
        if (!StringUtils.hasText(candidateName)) {
            throw new ApiException(422, "候选人姓名不能为空");
        }

        String target = candidateName.strip();
        for (Map<String, Object> result : parseResults(session.getResultsJson())) {
            if (target.equals(asText(result.get("candidate_name")).strip())) {
                return result;
            }
        }

        throw ApiException.notFound("候选人匹配结果不存在");
    }

    private Path resolveResumePath(String source) {
        if (!StringUtils.hasText(source)) {
            return null;
        }

        Path resumeRoot = Path.of(resumeDir).toAbsolutePath().normalize();
        List<Path> candidates = new ArrayList<>();
        try {
            Path sourcePath = Path.of(source).normalize();
            if (sourcePath.isAbsolute()) {
                candidates.add(sourcePath.toAbsolutePath().normalize());
            }
            Path filename = sourcePath.getFileName();
            if (filename != null) {
                candidates.add(resumeRoot.resolve(filename.toString()).normalize());
            }
        } catch (InvalidPathException ignored) {
            return null;
        }

        for (Path candidate : candidates) {
            if (candidate.startsWith(resumeRoot) && Files.isRegularFile(candidate)) {
                return candidate;
            }
        }
        return null;
    }

    private String writeResults(List<Map<String, Object>> results) {
        try {
            return objectMapper.writeValueAsString(results);
        } catch (Exception e) {
            throw new ApiException(500, "保存审核结果失败：" + e.getMessage());
        }
    }

    private int defaultInt(Integer value) {
        return value == null ? 0 : value;
    }

    private String asText(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private String defaultString(String value) {
        return value == null ? "" : value;
    }

    public record ReviewRequest(List<ReviewDecision> approvals) {
    }

    public record ReviewDecision(@JsonProperty("candidate_name") String candidateName,
                                 boolean approved,
                                 String feedback) {
    }
}
