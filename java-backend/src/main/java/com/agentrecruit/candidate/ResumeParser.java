package com.agentrecruit.candidate;

import com.agentrecruit.common.ApiException;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.extractor.XWPFWordExtractor;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.springframework.stereotype.Component;

import java.io.ByteArrayInputStream;

/** 简历文本提取：PDF 用 PDFBox，DOCX 用 Apache POI。 */
@Component
public class ResumeParser {

    public record PdfResult(String text, int pages) {
    }

    public PdfResult extractPdf(byte[] bytes) {
        try (PDDocument doc = Loader.loadPDF(bytes)) {
            String text = new PDFTextStripper().getText(doc).strip();
            return new PdfResult(text, doc.getNumberOfPages());
        } catch (Exception e) {
            throw new ApiException(422, "PDF 解析失败：" + e.getMessage());
        }
    }

    public String extractDocx(byte[] bytes) {
        try (XWPFDocument doc = new XWPFDocument(new ByteArrayInputStream(bytes));
             XWPFWordExtractor extractor = new XWPFWordExtractor(doc)) {
            return extractor.getText().strip();
        } catch (Exception e) {
            throw new ApiException(422, "DOCX 解析失败：" + e.getMessage());
        }
    }

    /** 按扩展名提取纯文本（.pdf / .docx）。 */
    public String extractText(byte[] bytes, String ext) {
        return switch (ext) {
            case ".pdf" -> extractPdf(bytes).text();
            case ".docx" -> extractDocx(bytes);
            default -> "";
        };
    }
}
