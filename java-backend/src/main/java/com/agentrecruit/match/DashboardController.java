package com.agentrecruit.match;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.agentrecruit.candidate.entity.Candidate;
import com.agentrecruit.candidate.mapper.CandidateMapper;
import com.agentrecruit.jd.entity.Jd;
import com.agentrecruit.jd.mapper.JdMapper;
import com.agentrecruit.match.entity.MatchSession;
import com.agentrecruit.match.mapper.MatchSessionMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final JdMapper jdMapper;
    private final CandidateMapper candidateMapper;
    private final MatchSessionMapper matchSessionMapper;

    public DashboardController(JdMapper jdMapper, CandidateMapper candidateMapper,
                               MatchSessionMapper matchSessionMapper) {
        this.jdMapper = jdMapper;
        this.candidateMapper = candidateMapper;
        this.matchSessionMapper = matchSessionMapper;
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        long activeJds = jdMapper.selectCount(new LambdaQueryWrapper<Jd>().eq(Jd::getStatus, "active"));
        long totalCandidates = candidateMapper.selectCount(null);
        long pendingApprovals = matchSessionMapper.selectCount(
                new LambdaQueryWrapper<MatchSession>().eq(MatchSession::getStatus, "pending"));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("active_jds", activeJds);
        result.put("total_candidates", totalCandidates);
        result.put("pending_approvals", pendingApprovals);
        return result;
    }

    @GetMapping("/trend")
    public List<Map<String, Object>> trend() {
        DateTimeFormatter label = DateTimeFormatter.ofPattern("MM/dd");
        LocalDate today = LocalDate.now();
        List<Map<String, Object>> result = new ArrayList<>();
        for (int i = 6; i >= 0; i--) {
            LocalDate day = today.minusDays(i);
            LocalDateTime start = day.atStartOfDay();
            LocalDateTime end = day.atTime(LocalTime.MAX);

            long candidates = candidateMapper.selectCount(new LambdaQueryWrapper<Candidate>()
                    .between(Candidate::getCreatedAt, start, end));
            long matches = matchSessionMapper.selectCount(new LambdaQueryWrapper<MatchSession>()
                    .between(MatchSession::getCreatedAt, start, end));

            Map<String, Object> row = new LinkedHashMap<>();
            row.put("date", day.format(label));
            row.put("candidates", candidates);
            row.put("matches", matches);
            result.add(row);
        }
        return result;
    }
}
