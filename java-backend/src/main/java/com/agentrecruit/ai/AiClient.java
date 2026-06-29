package com.agentrecruit.ai;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** 调用 Python AI 服务（服务间内部调用）。 */
@Slf4j
@Component
public class AiClient {

    private final WebClient aiWebClient;

    public AiClient(WebClient aiWebClient) {
        this.aiWebClient = aiWebClient;
    }

    /** 结构化解析的简历信息，对应 Python CandidateInfo。 */
    public record ParsedResume(String name, String email, List<String> skills,
                               Integer years_of_experience, String education, String summary) {
    }

    /**
     * 调用 Python /api/internal/parse-resume 把简历文本结构化为候选人信息。
     * 失败时返回 empty（调用方降级为手动填写，对应 Python D-05 partial success）。
     */
    @SuppressWarnings("unchecked")
    public Optional<ParsedResume> parseResume(String text) {
        try {
            Map<String, Object> body = aiWebClient.post()
                    .uri("/api/internal/parse-resume")
                    .bodyValue(Map.of("text", text))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .timeout(Duration.ofSeconds(60))
                    .block();
            if (body == null) {
                return Optional.empty();
            }
            List<String> skills = (List<String>) body.getOrDefault("skills", List.of());
            Integer years = body.get("years_of_experience") instanceof Number n ? n.intValue() : 0;
            return Optional.of(new ParsedResume(
                    str(body.get("name")), str(body.get("email")), skills,
                    years, str(body.get("education")), str(body.get("summary"))));
        } catch (Exception e) {
            log.warn("调用 AI 解析简历失败，降级为空：{}", e.getMessage());
            return Optional.empty();
        }
    }

    private static String str(Object o) {
        return o == null ? "" : o.toString();
    }
}
