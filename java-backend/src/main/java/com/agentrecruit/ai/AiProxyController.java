package com.agentrecruit.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.core.io.buffer.DefaultDataBufferFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;
import reactor.core.publisher.Flux;

import java.nio.charset.StandardCharsets;
import java.util.function.Consumer;

/**
 * AI 网关：把 /api/recruit* 、/api/skills 、/api/admin/rebuild-index 反向代理到 Python AI 服务。
 * 透传 Authorization/Cookie，使 Python 端鉴权（共享 JWT 密钥）继续生效。
 * 对前端而言 Python 完全透明。
 */
@Slf4j
@RestController
public class AiProxyController {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final WebClient aiWebClient;

    public AiProxyController(WebClient aiWebClient) {
        this.aiWebClient = aiWebClient;
    }

    // ── 非流式 JSON 端点 ──────────────────────────────────────────────

    @PostMapping("/api/recruit")
    public ResponseEntity<byte[]> recruit(@RequestBody(required = false) byte[] body, HttpServletRequest req) {
        return forwardJson(HttpMethod.POST, "/api/recruit", body, req);
    }

    @PostMapping("/api/recruit/hitl/start")
    public ResponseEntity<byte[]> hitlStart(@RequestBody(required = false) byte[] body, HttpServletRequest req) {
        return forwardJson(HttpMethod.POST, "/api/recruit/hitl/start", body, req);
    }

    @PostMapping("/api/recruit/hitl/resume")
    public ResponseEntity<byte[]> hitlResume(@RequestBody(required = false) byte[] body, HttpServletRequest req) {
        return forwardJson(HttpMethod.POST, "/api/recruit/hitl/resume", body, req);
    }

    @GetMapping("/api/skills")
    public ResponseEntity<byte[]> skills(HttpServletRequest req) {
        return forwardJson(HttpMethod.GET, "/api/skills", null, req);
    }

    @PostMapping("/api/admin/rebuild-index")
    public ResponseEntity<byte[]> rebuildIndex(@RequestBody(required = false) byte[] body, HttpServletRequest req) {
        return forwardJson(HttpMethod.POST, "/api/admin/rebuild-index", body, req);
    }

    // ── 流式 SSE 端点 ────────────────────────────────────────────────

    @PostMapping("/api/recruit/stream")
    public ResponseEntity<StreamingResponseBody> recruitStream(@RequestBody(required = false) byte[] body,
                                                               HttpServletRequest req) {
        return forwardStream("/api/recruit/stream", body, req);
    }

    @PostMapping("/api/recruit/hitl/stream")
    public ResponseEntity<StreamingResponseBody> hitlStream(@RequestBody(required = false) byte[] body,
                                                            HttpServletRequest req) {
        return forwardStream("/api/recruit/hitl/stream", body, req);
    }

    @PostMapping("/api/recruit/hitl/reverse-stream")
    public ResponseEntity<StreamingResponseBody> hitlReverseStream(@RequestBody(required = false) byte[] body,
                                                                   HttpServletRequest req) {
        return forwardStream("/api/recruit/hitl/reverse-stream", body, req);
    }

    // ── 内部实现 ──────────────────────────────────────────────────────

    private ResponseEntity<byte[]> forwardJson(HttpMethod method, String path, byte[] body, HttpServletRequest req) {
        WebClient.RequestBodySpec spec = aiWebClient.method(method).uri(path).headers(copyAuthHeaders(req));
        if (body != null && body.length > 0) {
            spec.contentType(MediaType.APPLICATION_JSON).bodyValue(body);
        }
        return spec.exchangeToMono(resp -> resp.toEntity(byte[].class)).block();
    }

    private ResponseEntity<StreamingResponseBody> forwardStream(String path, byte[] body, HttpServletRequest req) {
        StreamingResponseBody stream = outputStream -> {
            Flux<DataBuffer> flux = aiWebClient.post()
                    .uri(path)
                    .headers(copyAuthHeaders(req))
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body == null ? new byte[0] : body)
                    .exchangeToFlux(resp -> {
                        if (resp.statusCode().is2xxSuccessful()) {
                            return resp.bodyToFlux(DataBuffer.class);
                        }
                        return resp.bodyToMono(String.class)
                                .defaultIfEmpty("")
                                .flatMapMany(raw -> {
                                    String message = extractUpstreamMessage(path, resp.statusCode().value(), raw);
                                    log.warn("SSE 上游返回非 2xx: path={}, status={}, msg={}",
                                            path, resp.statusCode().value(), message);
                                    return toErrorSse(message);
                                });
                    })
                    .onErrorResume(e -> {
                        String message = "AI 服务暂时不可用，请稍后重试";
                        log.warn("SSE 反代中断：{}", e.getMessage());
                        return toErrorSse(message);
                    });
            try {
                flux.toIterable().forEach(buffer -> {
                    try {
                        byte[] bytes = new byte[buffer.readableByteCount()];
                        buffer.read(bytes);
                        outputStream.write(bytes);
                        outputStream.flush();
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    } finally {
                        DataBufferUtils.release(buffer);
                    }
                });
            } catch (Exception e) {
                log.warn("SSE 反代中断：{}", e.getMessage());
            }
        };
        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_EVENT_STREAM)
                .header(HttpHeaders.CACHE_CONTROL, "no-cache")
                .body(stream);
    }

    private Flux<DataBuffer> toErrorSse(String message) {
        String safe = escapeJson(message);
        String payload = "data: {\"event\":\"error\",\"data\":{\"message\":\"" + safe + "\"}}\n\n";
        byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
        return Flux.just(DefaultDataBufferFactory.sharedInstance.wrap(bytes));
    }

    private String extractUpstreamMessage(String path, int status, String rawBody) {
        String fallback = "匹配服务请求失败（" + status + "）";
        if (!StringUtils.hasText(rawBody)) {
            return fallback;
        }
        try {
            JsonNode root = MAPPER.readTree(rawBody);
            if (root.hasNonNull("message")) {
                return root.get("message").asText(fallback);
            }
            if (root.hasNonNull("detail")) {
                return root.get("detail").asText(fallback);
            }
            if (root.hasNonNull("error")) {
                JsonNode error = root.get("error");
                if (error.isTextual()) {
                    return error.asText(fallback);
                }
            }
        } catch (Exception ignored) {
            // 非 JSON body，走 fallback
        }
        String compact = rawBody.replaceAll("[\\r\\n]+", " ").trim();
        if (compact.length() > 160) {
            compact = compact.substring(0, 160) + "...";
        }
        return compact.isEmpty() ? fallback : compact;
    }

    private String escapeJson(String text) {
        return text
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\r", "\\r")
                .replace("\n", "\\n");
    }

    private Consumer<HttpHeaders> copyAuthHeaders(HttpServletRequest req) {
        String auth = req.getHeader(HttpHeaders.AUTHORIZATION);
        String cookie = req.getHeader(HttpHeaders.COOKIE);
        return headers -> {
            if (StringUtils.hasText(auth)) {
                headers.set(HttpHeaders.AUTHORIZATION, auth);
            }
            if (StringUtils.hasText(cookie)) {
                headers.set(HttpHeaders.COOKIE, cookie);
            }
        };
    }
}
