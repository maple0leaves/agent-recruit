package com.agentrecruit.jd;

import com.agentrecruit.common.PageResponse;
import com.agentrecruit.jd.dto.JdRequest;
import com.agentrecruit.jd.dto.JdResponse;
import com.agentrecruit.jd.dto.StatusUpdateRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/jd")
public class JdController {

    private final JdService jdService;

    public JdController(JdService jdService) {
        this.jdService = jdService;
    }

    @GetMapping("/templates")
    public List<Map<String, Object>> templates() {
        return JdTemplates.all();
    }

    @GetMapping
    public PageResponse<JdResponse> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword,
            @RequestParam(name = "date_from", required = false) String dateFrom,
            @RequestParam(name = "date_to", required = false) String dateTo) {
        return jdService.list(page, pageSize, status, keyword, dateFrom, dateTo);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public JdResponse create(@Valid @RequestBody JdRequest request) {
        return jdService.create(request);
    }

    @GetMapping("/{id}")
    public JdResponse get(@PathVariable Long id) {
        return jdService.get(id);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public JdResponse update(@PathVariable Long id, @Valid @RequestBody JdRequest request) {
        return jdService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public void delete(@PathVariable Long id) {
        jdService.delete(id);
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('ADMIN','RECRUITER')")
    public JdResponse updateStatus(@PathVariable Long id, @Valid @RequestBody StatusUpdateRequest request) {
        return jdService.updateStatus(id, request.status());
    }
}
