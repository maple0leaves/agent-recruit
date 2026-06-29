package com.agentrecruit.match.export;

import com.agentrecruit.common.ApiException;
import com.lowagie.text.Document;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.Map;

/** 用 OpenPDF 生成匹配报告 PDF，内嵌中文 TTF/TTC 字体。 */
@Slf4j
@Service
public class PdfReportService {

    private final String fontPath;
    private BaseFont baseFont;

    public PdfReportService(@Value("${app.export.cjk-font}") String fontPath) {
        this.fontPath = fontPath;
    }

    @PostConstruct
    void initFont() {
        try {
            baseFont = BaseFont.createFont(fontPath, BaseFont.IDENTITY_H, BaseFont.EMBEDDED);
        } catch (Exception e) {
            log.error("中文字体加载失败（{}）：{}", fontPath, e.getMessage());
            throw new IllegalStateException("无法加载中文字体: " + fontPath, e);
        }
    }

    public byte[] generate(String jdTitle, String matchDate, List<Map<String, Object>> candidates) {
        Font titleFont = new Font(baseFont, 16, Font.BOLD);
        Font metaFont = new Font(baseFont, 10);
        Font headerFont = new Font(baseFont, 9, Font.NORMAL, Color.WHITE);
        Font cellFont = new Font(baseFont, 9);

        Document doc = new Document(PageSize.A4, 42, 42, 56, 56);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try {
            PdfWriter.getInstance(doc, out);
            doc.open();

            Paragraph title = new Paragraph("匹配报告: " + jdTitle, titleFont);
            title.setSpacingAfter(12);
            doc.add(title);

            Paragraph meta = new Paragraph("生成日期: " + matchDate, metaFont);
            meta.setSpacingAfter(18);
            doc.add(meta);

            PdfPTable table = new PdfPTable(new float[]{40, 20, 50, 50, 20});
            table.setWidthPercentage(100);
            table.setHeaderRows(1);

            Color headerBg = new Color(0x4F, 0x81, 0xBD);
            for (String h : List.of("候选人", "匹配度", "匹配技能", "缺失技能", "审核状态")) {
                PdfPCell cell = new PdfPCell(new Phrase(h, headerFont));
                cell.setBackgroundColor(headerBg);
                cell.setHorizontalAlignment(Element.ALIGN_CENTER);
                cell.setVerticalAlignment(Element.ALIGN_MIDDLE);
                cell.setPadding(5);
                table.addCell(cell);
            }

            Color stripe = new Color(0xF2, 0xF2, 0xF2);
            int row = 0;
            for (Map<String, Object> c : candidates) {
                Color bg = (row % 2 == 0) ? Color.WHITE : stripe;
                addCell(table, str(c.get("candidate_name")), cellFont, bg, Element.ALIGN_LEFT);
                addCell(table, scorePercent(c.get("match_score")), cellFont, bg, Element.ALIGN_CENTER);
                addCell(table, joinList(c.get("matched_skills")), cellFont, bg, Element.ALIGN_LEFT);
                addCell(table, joinList(c.get("missing_skills")), cellFont, bg, Element.ALIGN_LEFT);
                addCell(table, statusLabel(c.get("should_proceed")), cellFont, bg, Element.ALIGN_CENTER);
                row++;
            }

            doc.add(table);
            doc.close();
        } catch (Exception e) {
            throw new ApiException(500, "生成 PDF 失败：" + e.getMessage());
        }
        return out.toByteArray();
    }

    private void addCell(PdfPTable table, String text, Font font, Color bg, int align) {
        PdfPCell cell = new PdfPCell(new Phrase(text, font));
        cell.setBackgroundColor(bg);
        cell.setHorizontalAlignment(align);
        cell.setVerticalAlignment(Element.ALIGN_MIDDLE);
        cell.setPadding(4);
        table.addCell(cell);
    }

    static String str(Object o) {
        return o == null ? "" : o.toString();
    }

    static String scorePercent(Object score) {
        if (score instanceof Number n) {
            return n.intValue() + "%";
        }
        return "0%";
    }

    @SuppressWarnings("unchecked")
    static String joinList(Object value) {
        if (value instanceof List<?> list) {
            return String.join(", ", list.stream().map(String::valueOf).toList());
        }
        return "";
    }

    static String statusLabel(Object shouldProceed) {
        if (Boolean.TRUE.equals(shouldProceed)) {
            return "通过";
        }
        if (Boolean.FALSE.equals(shouldProceed)) {
            return "驳回";
        }
        return "待审";
    }
}
