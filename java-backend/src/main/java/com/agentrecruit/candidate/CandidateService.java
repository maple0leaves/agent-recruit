package com.agentrecruit.candidate;

import com.agentrecruit.ai.AiClient;
import com.agentrecruit.candidate.dto.CandidateResponse;
import com.agentrecruit.candidate.dto.CandidateUpdateRequest;
import com.agentrecruit.candidate.entity.Candidate;
import com.agentrecruit.candidate.mapper.CandidateMapper;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.common.PageResponse;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.task.TaskExecutor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

@Slf4j
@Service
public class CandidateService {

    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024;
    private static final Set<String> ALLOWED_EXT = Set.of(".pdf", ".docx");
    private static final Set<String> VALID_STATUS = Set.of("new", "screening", "interview", "hired", "rejected");
    private static final Map<String, Set<String>> VALID_TRANSITIONS = Map.of(
            "new", Set.of("screening", "rejected"),
            "screening", Set.of("interview", "rejected"),
            "interview", Set.of("hired", "rejected"),
            "hired", Set.of(),
            "rejected", Set.of());

    private final CandidateMapper candidateMapper;
    private final ResumeParser resumeParser;
    private final AiClient aiClient;
    private final TaskExecutor applicationTaskExecutor;
    private final String resumeDir;

    public CandidateService(CandidateMapper candidateMapper,
                            ResumeParser resumeParser,
                            AiClient aiClient,
                            TaskExecutor applicationTaskExecutor,
                            @Value("${app.resume.dir}") String resumeDir) {
        this.candidateMapper = candidateMapper;
        this.resumeParser = resumeParser;
        this.aiClient = aiClient;
        this.applicationTaskExecutor = applicationTaskExecutor;
        this.resumeDir = resumeDir;
    }

    public record UploadResult(CandidateResponse candidate, List<String> warnings, String filename) {
    }

    public record UploadFailure(String filename, String error) {
    }

    public record BatchUploadResult(List<UploadResult> items, List<UploadFailure> failures) {
    }

    private record StoredResume(String originalFilename, String ext, Path path, String relativePath) {
    }

    public PageResponse<CandidateResponse> list(int page, int pageSize, String status, String keyword) {
        LambdaQueryWrapper<Candidate> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(status)) {
            wrapper.eq(Candidate::getStatus, status);
        }
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(Candidate::getName, keyword)
                    .or().like(Candidate::getSkills, keyword));
        }
        wrapper.orderByDesc(Candidate::getCreatedAt);
        Page<Candidate> result = candidateMapper.selectPage(Page.of(page, pageSize), wrapper);
        List<CandidateResponse> items = result.getRecords().stream().map(CandidateResponse::from).toList();
        return new PageResponse<>(items, result.getTotal(), page, pageSize);
    }

    public CandidateResponse get(Long id) {
        return CandidateResponse.from(require(id));
    }

    public CandidateResponse update(Long id, CandidateUpdateRequest req) {
        Candidate c = require(id);
        if (req.name() != null) c.setName(req.name());
        if (req.email() != null) c.setEmail(req.email());
        if (req.phone() != null) c.setPhone(req.phone());
        if (req.skills() != null) c.setSkills(req.skills());
        if (req.education() != null) c.setEducation(req.education());
        if (req.experience() != null) c.setExperience(req.experience());
        candidateMapper.updateById(c);
        return CandidateResponse.from(candidateMapper.selectById(id));
    }

    public CandidateResponse updateStatus(Long id, String newStatus, String statusNote) {
        if (!VALID_STATUS.contains(newStatus)) {
            throw ApiException.badRequest("无效的状态值: " + newStatus);
        }
        if (!StringUtils.hasText(statusNote)) {
            throw new ApiException(422, "状态变更时备注为必填项");
        }
        Candidate c = require(id);
        Set<String> allowed = VALID_TRANSITIONS.getOrDefault(c.getStatus(), Set.of());
        if (!allowed.contains(newStatus)) {
            throw ApiException.badRequest(
                    String.format("无效的状态变更：无法从 %s 变更为 %s", c.getStatus(), newStatus));
        }
        c.setStatus(newStatus);
        c.setStatusNote(statusNote.strip());
        candidateMapper.updateById(c);
        return CandidateResponse.from(candidateMapper.selectById(id));
    }

    public UploadResult upload(MultipartFile file) {
        StoredResume stored = storeResume(file);

        Candidate candidate = new Candidate();
        candidate.setName(fallbackName(stored.originalFilename()));
        candidate.setEmail("");
        candidate.setPhone("");
        candidate.setSkills("");
        candidate.setEducation("");
        candidate.setExperience("");
        candidate.setStatus("new");
        candidate.setResumeFilePath(stored.relativePath());
        candidate.setStatusNote("简历已上传，正在后台解析");
        candidate.setParsedAt(null);

        candidateMapper.insert(candidate);
        Candidate saved = candidateMapper.selectById(candidate.getId());

        applicationTaskExecutor.execute(() ->
                parseResumeInBackground(saved.getId(), stored.path(), stored.ext()));

        return new UploadResult(CandidateResponse.from(saved), List.of(), stored.originalFilename());
    }

    public BatchUploadResult uploadBatch(List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            throw ApiException.badRequest("请选择要上传的简历文件");
        }

        List<UploadResult> items = new ArrayList<>();
        List<UploadFailure> failures = new ArrayList<>();

        for (MultipartFile file : files) {
            String filename = displayFilename(file);
            try {
                items.add(upload(file));
            } catch (ApiException e) {
                failures.add(new UploadFailure(filename, e.getMessage()));
            } catch (Exception e) {
                log.warn("上传简历失败：{}", filename, e);
                failures.add(new UploadFailure(filename, "上传失败，请稍后重试"));
            }
        }

        return new BatchUploadResult(items, failures);
    }

    public void delete(Long id) {
        Candidate candidate = require(id);
        candidateMapper.deleteById(id);
        deleteResumeFile(candidate.getResumeFilePath());
    }

    private StoredResume storeResume(MultipartFile file) {
        String filename = displayFilename(file);
        String ext = extension(filename);
        if (!ALLOWED_EXT.contains(ext)) {
            if (".doc".equals(ext)) {
                throw ApiException.badRequest("不支持的格式。请将 .doc 文件另存为 .docx 格式后重新上传。");
            }
            throw ApiException.badRequest("仅支持 PDF 和 Word (.docx) 格式，不支持 " + ext + " 文件。");
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
        if (raw.length > MAX_FILE_SIZE) {
            throw ApiException.badRequest("文件大小不能超过 10MB");
        }

        String safeName = UUID.randomUUID().toString().replace("-", "") + ext;
        Path dir = Path.of(resumeDir).toAbsolutePath().normalize();
        Path target = dir.resolve(safeName).normalize();
        if (!target.startsWith(dir)) {
            throw new ApiException(500, "简历保存路径非法");
        }

        try {
            Files.createDirectories(dir);
            Files.write(target, raw);
        } catch (IOException e) {
            throw new ApiException(500, "保存简历文件失败：" + e.getMessage());
        }

        return new StoredResume(filename, ext, target, "data/resumes/" + safeName);
    }

    private void parseResumeInBackground(Long candidateId, Path resumePath, String ext) {
        try {
            byte[] raw = Files.readAllBytes(resumePath);
            String text = resumeParser.extractText(raw, ext);

            Candidate candidate = candidateMapper.selectById(candidateId);
            if (candidate == null) {
                return;
            }

            if (!StringUtils.hasText(text)) {
                markParseFailed(candidate, "未能从文件中提取到文字内容，请手动补充候选人信息");
                return;
            }

            Optional<AiClient.ParsedResume> parsed = aiClient.parseResume(text);
            if (parsed.isEmpty()) {
                markParseFailed(candidate, "AI 简历解析失败，请手动补充候选人信息");
                return;
            }

            applyParsedResume(candidate, parsed.get());
            candidate.setParsedAt(LocalDateTime.now());
            candidate.setStatusNote("简历解析完成");
            candidateMapper.updateById(candidate);
        } catch (Exception e) {
            log.warn("后台解析简历失败，candidateId={}: {}", candidateId, e.getMessage());
            markParseFailed(candidateId, "简历解析失败：" + safeMessage(e));
        }
    }

    private void applyParsedResume(Candidate candidate, AiClient.ParsedResume parsed) {
        if (StringUtils.hasText(parsed.name())) {
            candidate.setName(parsed.name().strip());
        }
        if (parsed.email() != null) {
            candidate.setEmail(parsed.email().strip());
        }
        if (parsed.skills() != null && !parsed.skills().isEmpty()) {
            candidate.setSkills(String.join(", ", parsed.skills()));
        }
        if (parsed.education() != null) {
            candidate.setEducation(parsed.education().strip());
        }
        if (StringUtils.hasText(parsed.summary())) {
            candidate.setExperience(parsed.summary().strip());
        } else if (parsed.years_of_experience() != null && parsed.years_of_experience() > 0) {
            candidate.setExperience(parsed.years_of_experience() + " 年经验");
        }
    }

    private void markParseFailed(Long candidateId, String note) {
        Candidate candidate = candidateMapper.selectById(candidateId);
        if (candidate != null) {
            markParseFailed(candidate, note);
        }
    }

    private void markParseFailed(Candidate candidate, String note) {
        candidate.setStatusNote(truncate(note, 1000));
        candidate.setParsedAt(null);
        candidateMapper.updateById(candidate);
    }

    private void deleteResumeFile(String resumeFilePath) {
        if (!StringUtils.hasText(resumeFilePath)) {
            return;
        }

        try {
            Path dir = Path.of(resumeDir).toAbsolutePath().normalize();
            Path stored = Path.of(resumeFilePath);
            Path filename = stored.getFileName();
            if (filename == null) {
                return;
            }
            Path target = dir.resolve(filename.toString()).normalize();
            if (!target.startsWith(dir)) {
                log.warn("跳过删除非法简历路径：{}", resumeFilePath);
                return;
            }
            Files.deleteIfExists(target);
        } catch (IOException | InvalidPathException e) {
            log.warn("删除简历文件失败：{}", resumeFilePath, e);
        }
    }

    private Candidate require(Long id) {
        Candidate c = candidateMapper.selectById(id);
        if (c == null) {
            throw ApiException.notFound("候选人不存在");
        }
        return c;
    }

    private static String displayFilename(MultipartFile file) {
        String filename = file == null ? null : file.getOriginalFilename();
        if (!StringUtils.hasText(filename)) {
            return "resume.pdf";
        }
        String normalized = filename.replace("\\", "/");
        return normalized.substring(normalized.lastIndexOf('/') + 1);
    }

    private static String fallbackName(String filename) {
        String name = filename;
        int dot = name.lastIndexOf('.');
        if (dot > 0) {
            name = name.substring(0, dot);
        }
        name = name.strip();
        if (!StringUtils.hasText(name)) {
            return "解析中候选人";
        }
        return truncate(name, 200);
    }

    private static String extension(String filename) {
        int dot = filename.lastIndexOf('.');
        return dot < 0 ? "" : filename.substring(dot).toLowerCase();
    }

    private static String safeMessage(Exception e) {
        String message = e.getMessage();
        return StringUtils.hasText(message) ? message : e.getClass().getSimpleName();
    }

    private static String truncate(String value, int maxLength) {
        if (value == null || value.length() <= maxLength) {
            return value;
        }
        return value.substring(0, maxLength);
    }
}
