package com.agentrecruit.candidate;

import com.agentrecruit.candidate.dto.CandidateResponse;
import com.agentrecruit.candidate.dto.CandidateStatusUpdateRequest;
import com.agentrecruit.candidate.dto.CandidateUpdateRequest;
import com.agentrecruit.common.PageResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/candidates")
public class CandidateController {

    private final CandidateService candidateService;

    public CandidateController(CandidateService candidateService) {
        this.candidateService = candidateService;
    }

    @PostMapping("/upload")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public Map<String, Object> upload(@RequestParam("file") MultipartFile file) {
        CandidateService.UploadResult result = candidateService.upload(file);
        Map<String, Object> body = toUploadMap(result);
        return body;
    }

    @PostMapping("/upload/batch")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public Map<String, Object> uploadBatch(@RequestParam("files") List<MultipartFile> files) {
        CandidateService.BatchUploadResult result = candidateService.uploadBatch(files);
        List<Map<String, Object>> items = result.items().stream()
                .map(this::toUploadMap)
                .toList();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("items", items);
        body.put("failures", result.failures());
        body.put("success_count", items.size());
        body.put("failure_count", result.failures().size());
        body.put("total_count", items.size() + result.failures().size());
        return body;
    }

    private Map<String, Object> toUploadMap(CandidateService.UploadResult result) {
        Map<String, Object> body = new LinkedHashMap<>(toMap(result.candidate()));
        body.put("filename", result.filename());
        if (!result.warnings().isEmpty()) {
            body.put("warnings", result.warnings());
        }
        return body;
    }

    @GetMapping
    public PageResponse<CandidateResponse> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword) {
        return candidateService.list(page, pageSize, status, keyword);
    }

    @GetMapping("/{id}")
    public CandidateResponse get(@PathVariable Long id) {
        return candidateService.get(id);
    }

    @PutMapping("/{id}")
    public CandidateResponse update(@PathVariable Long id, @RequestBody CandidateUpdateRequest request) {
        return candidateService.update(id, request);
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public CandidateResponse updateStatus(@PathVariable Long id,
                                          @Valid @RequestBody CandidateStatusUpdateRequest request) {
        return candidateService.updateStatus(id, request.status(), request.status_note());
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public void delete(@PathVariable Long id) {
        candidateService.delete(id);
    }

    private Map<String, Object> toMap(CandidateResponse c) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.id());
        m.put("name", c.name());
        m.put("email", c.email());
        m.put("phone", c.phone());
        m.put("skills", c.skills());
        m.put("education", c.education());
        m.put("experience", c.experience());
        m.put("status", c.status());
        m.put("resume_file_path", c.resume_file_path());
        m.put("status_note", c.status_note());
        m.put("parse_status", c.parse_status());
        m.put("parsed_at", c.parsed_at() == null ? null : c.parsed_at().toString());
        m.put("created_at", c.created_at() == null ? null : c.created_at().toString());
        m.put("updated_at", c.updated_at() == null ? null : c.updated_at().toString());
        return m;
    }
}
