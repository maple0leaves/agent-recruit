export type JDStatus = "draft" | "active" | "closed";
export type EducationLevel = "高中" | "大专" | "本科" | "硕士" | "博士" | "不限";

export interface JD {
  id: number;
  title: string;
  department: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
  status: JDStatus;
  created_at: string;
  updated_at: string;
}

export interface JDListResponse {
  items: JD[];
  total: number;
  page: number;
  page_size: number;
}

export interface JDFormValues {
  title: string;
  department: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
}

export interface JDTemplate {
  name: string;
  description: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
}
