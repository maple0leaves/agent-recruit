package com.agentrecruit.jd;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.common.PageResponse;
import com.agentrecruit.jd.dto.JdRequest;
import com.agentrecruit.jd.dto.JdResponse;
import com.agentrecruit.jd.entity.Jd;
import com.agentrecruit.jd.mapper.JdMapper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class JdService {

    private static final Set<String> VALID_STATUS = Set.of("draft", "active", "closed");
    private static final Map<String, Set<String>> VALID_TRANSITIONS = Map.of(
            "draft", Set.of("active"),
            "active", Set.of("closed"),
            "closed", Set.of("active"));

    private final JdMapper jdMapper;

    public JdService(JdMapper jdMapper) {
        this.jdMapper = jdMapper;
    }

    public PageResponse<JdResponse> list(int page, int pageSize, String status, String keyword,
                                         String dateFrom, String dateTo) {
        LambdaQueryWrapper<Jd> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(status)) {
            wrapper.eq(Jd::getStatus, status);
        }
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(Jd::getTitle, keyword)
                    .or().like(Jd::getDepartment, keyword)
                    .or().like(Jd::getSkills, keyword));
        }
        if (StringUtils.hasText(dateFrom)) {
            wrapper.ge(Jd::getUpdatedAt, dateFrom);
        }
        if (StringUtils.hasText(dateTo)) {
            wrapper.le(Jd::getUpdatedAt, dateTo + " 23:59:59");
        }
        wrapper.orderByDesc(Jd::getUpdatedAt);

        Page<Jd> result = jdMapper.selectPage(Page.of(page, pageSize), wrapper);
        List<JdResponse> items = result.getRecords().stream().map(JdResponse::from).toList();
        return new PageResponse<>(items, result.getTotal(), page, pageSize);
    }

    public JdResponse get(Long id) {
        return JdResponse.from(require(id));
    }

    public JdResponse create(JdRequest req) {
        Jd jd = new Jd();
        applyRequest(jd, req);
        jd.setStatus("draft");
        jdMapper.insert(jd);
        return JdResponse.from(jdMapper.selectById(jd.getId()));
    }

    public JdResponse update(Long id, JdRequest req) {
        Jd jd = require(id);
        applyRequest(jd, req);
        jdMapper.updateById(jd);
        return JdResponse.from(jdMapper.selectById(id));
    }

    public void delete(Long id) {
        Jd jd = require(id);
        jdMapper.deleteById(jd.getId());
    }

    public JdResponse updateStatus(Long id, String newStatus) {
        if (!VALID_STATUS.contains(newStatus)) {
            throw ApiException.badRequest("无效的状态值: " + newStatus);
        }
        Jd jd = require(id);
        String current = jd.getStatus();
        Set<String> allowed = VALID_TRANSITIONS.getOrDefault(current, Set.of());
        if (!allowed.contains(newStatus)) {
            throw ApiException.badRequest(
                    String.format("无效的状态转换：不能从「%s」到「%s」", current, newStatus));
        }
        jd.setStatus(newStatus);
        jdMapper.updateById(jd);
        return JdResponse.from(jdMapper.selectById(id));
    }

    private void applyRequest(Jd jd, JdRequest req) {
        jd.setTitle(req.title().strip());
        jd.setDepartment(req.departmentOrEmpty());
        jd.setSkills(req.skillsOrEmpty());
        jd.setExperienceYears(req.experienceYearsOrZero());
        jd.setEducation(req.educationOrDefault());
        jd.setSalaryMin(req.salaryMinOrZero());
        jd.setSalaryMax(req.salaryMaxOrZero());
        jd.setDescription(req.descriptionOrEmpty());
    }

    private Jd require(Long id) {
        Jd jd = jdMapper.selectById(id);
        if (jd == null) {
            throw ApiException.notFound("JD 不存在");
        }
        return jd;
    }
}
