package com.agentrecruit.match.export;

import com.agentrecruit.common.ApiException;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.Map;

/** 用 Apache POI 生成匹配报告 Excel(.xlsx)。 */
@Service
public class ExcelReportService {

    public byte[] generate(List<Map<String, Object>> candidates) {
        try (Workbook wb = new XSSFWorkbook(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            Sheet sheet = wb.createSheet("匹配结果");

            CellStyle headerStyle = wb.createCellStyle();
            Font headerFont = wb.createFont();
            headerFont.setBold(true);
            headerFont.setColor(IndexedColors.WHITE.getIndex());
            headerStyle.setFont(headerFont);
            headerStyle.setFillForegroundColor(IndexedColors.ROYAL_BLUE.getIndex());
            headerStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            headerStyle.setAlignment(HorizontalAlignment.CENTER);
            headerStyle.setVerticalAlignment(VerticalAlignment.CENTER);
            applyThinBorder(headerStyle);

            CellStyle dataStyle = wb.createCellStyle();
            dataStyle.setVerticalAlignment(VerticalAlignment.CENTER);
            applyThinBorder(dataStyle);

            String[] headers = {"候选人姓名", "匹配度", "匹配技能", "缺失技能", "审核状态", "备注"};
            Row headerRow = sheet.createRow(0);
            for (int i = 0; i < headers.length; i++) {
                Cell cell = headerRow.createCell(i);
                cell.setCellValue(headers[i]);
                cell.setCellStyle(headerStyle);
            }

            int rowIdx = 1;
            for (Map<String, Object> c : candidates) {
                Row row = sheet.createRow(rowIdx++);
                setCell(row, 0, PdfReportService.str(c.get("candidate_name")), dataStyle);
                Cell scoreCell = row.createCell(1);
                scoreCell.setCellValue(c.get("match_score") instanceof Number n ? n.intValue() : 0);
                scoreCell.setCellStyle(dataStyle);
                setCell(row, 2, PdfReportService.joinList(c.get("matched_skills")), dataStyle);
                setCell(row, 3, PdfReportService.joinList(c.get("missing_skills")), dataStyle);
                setCell(row, 4, PdfReportService.statusLabel(c.get("should_proceed")), dataStyle);
                setCell(row, 5, PdfReportService.str(c.get("recommendation")), dataStyle);
            }

            int[] widths = {18, 10, 40, 40, 12, 30};
            for (int i = 0; i < widths.length; i++) {
                sheet.setColumnWidth(i, widths[i] * 256);
            }

            wb.write(out);
            return out.toByteArray();
        } catch (Exception e) {
            throw new ApiException(500, "生成 Excel 失败：" + e.getMessage());
        }
    }

    private void setCell(Row row, int col, String value, CellStyle style) {
        Cell cell = row.createCell(col);
        cell.setCellValue(value);
        cell.setCellStyle(style);
    }

    private void applyThinBorder(CellStyle style) {
        style.setBorderTop(BorderStyle.THIN);
        style.setBorderBottom(BorderStyle.THIN);
        style.setBorderLeft(BorderStyle.THIN);
        style.setBorderRight(BorderStyle.THIN);
    }
}
